"""Windowed tiling service for large remote sensing rasters.

Splits GeoTIFF/JPG into 512x512 tiles with 20% overlap.
Strictly reads rasters tile-by-tile via rasterio windowed reads without loading the full image into RAM.
Handles non-georeferenced images gracefully using pixel coordinate space.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Optional, Tuple
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import Affine
from app.core.logging import logger


@dataclass
class RasterMetadata:
    """Metadata extracted from a raster file."""

    width: int
    height: int
    count: int
    crs: Optional[str]
    transform: Affine
    resolution_x: float
    resolution_y: float
    is_georeferenced: bool


@dataclass
class TileData:
    """Individual extracted windowed tile."""

    tile_index: int
    window: Window
    col_off: int
    row_off: int
    width: int
    height: int
    image: np.ndarray  # Shape: (H, W, C), uint8 RGB
    transform: Affine  # Local affine transform for this window
    crs: Optional[str]
    is_georeferenced: bool


def inspect_raster(file_path: str | Path) -> RasterMetadata:
    """Reads header metadata of a raster without loading image data into RAM.

    Args:
        file_path: Path to the GeoTIFF or standard image.

    Returns:
        RasterMetadata with spatial reference and dimensions.
    """
    with rasterio.open(str(file_path)) as dataset:
        crs_str = dataset.crs.to_string() if dataset.crs else None
        res_x, res_y = dataset.res if dataset.res else (1.0, 1.0)
        is_geo = dataset.crs is not None

        return RasterMetadata(
            width=dataset.width,
            height=dataset.height,
            count=dataset.count,
            crs=crs_str,
            transform=dataset.transform,
            resolution_x=abs(res_x),
            resolution_y=abs(res_y),
            is_georeferenced=is_geo,
        )


def generate_tiles(
    file_path: str | Path,
    tile_size: int = 512,
    overlap_pct: float = 0.20,
) -> Generator[TileData, None, None]:
    """Generates windowed 512x512 tiles with 20% overlap using rasterio windows.

    Never loads the full raster in RAM; streams windows directly from disk.

    Args:
        file_path: Path to GeoTIFF or RGB image.
        tile_size: Size of tile in pixels (default 512).
        overlap_pct: Overlap fraction (default 0.20 -> ~102px overlap).

    Yields:
        TileData with RGB numpy array, local transform, and window bounds.
    """
    step = int(tile_size * (1.0 - overlap_pct))
    if step <= 0:
        step = tile_size

    with rasterio.open(str(file_path)) as src:
        total_w = src.width
        total_h = src.height
        crs_str = src.crs.to_string() if src.crs else None
        is_geo = src.crs is not None

        tile_idx = 0
        y_offsets = list(range(0, total_h, step))
        x_offsets = list(range(0, total_w, step))

        for row_off in y_offsets:
            for col_off in x_offsets:
                # Clamp window to raster bounds
                win_w = min(tile_size, total_w - col_off)
                win_h = min(tile_size, total_h - row_off)

                window = Window(col_off=col_off, row_off=row_off, width=win_w, height=win_h)

                # Read only this specific window from disk
                # Read all bands or up to 3 bands
                bands_to_read = min(src.count, 3)
                if bands_to_read == 1:
                    raw_data = src.read(1, window=window)
                    # Replicate grayscale to 3-channel RGB
                    rgb_tile = np.stack([raw_data, raw_data, raw_data], axis=-1)
                elif bands_to_read >= 3:
                    raw_data = src.read([1, 2, 3], window=window)
                    # (C, H, W) -> (H, W, C)
                    rgb_tile = np.transpose(raw_data, (1, 2, 0))
                else:
                    # 2 bands fallback
                    raw_data = src.read([1, 2], window=window)
                    empty_band = np.zeros_like(raw_data[0])
                    rgb_tile = np.stack([raw_data[0], raw_data[1], empty_band], axis=-1)

                # Ensure uint8
                if rgb_tile.dtype != np.uint8:
                    if np.issubdtype(rgb_tile.dtype, np.floating):
                        rgb_tile = np.clip(rgb_tile * 255.0, 0, 255).astype(np.uint8)
                    else:
                        # Normalize 16-bit or other integer
                        max_val = float(np.max(rgb_tile)) if np.max(rgb_tile) > 0 else 1.0
                        rgb_tile = np.clip((rgb_tile / max_val) * 255.0, 0, 255).astype(np.uint8)

                # Pad to full tile_size x tile_size if boundary tile is smaller
                h, w = rgb_tile.shape[:2]
                if h < tile_size or w < tile_size:
                    padded = np.zeros((tile_size, tile_size, 3), dtype=np.uint8)
                    padded[:h, :w, :] = rgb_tile
                    tile_image = padded
                else:
                    tile_image = rgb_tile

                # Compute local affine transform for this window
                win_transform = rasterio.windows.transform(window, src.transform)

                yield TileData(
                    tile_index=tile_idx,
                    window=window,
                    col_off=col_off,
                    row_off=row_off,
                    width=win_w,
                    height=win_h,
                    image=tile_image,
                    transform=win_transform,
                    crs=crs_str,
                    is_georeferenced=is_geo,
                )
                tile_idx += 1
