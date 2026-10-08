"""Tile inference orchestration service.

Executes detection model adapters across windowed tiles and maps local detections to global raster coordinates.
"""

from dataclasses import dataclass
from typing import Generator, List, Optional, Tuple
import numpy as np
from rasterio.transform import Affine
from app.ml_adapters import get_detector, BaseTreeDetector, RawDetection
from app.services.tiling import TileData
from app.core.logging import logger


@dataclass
class GlobalPixelDetection:
    """Tree crown detection referenced to global raster pixel coordinates."""

    tile_index: int
    global_bbox: Tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax) in full image pixels
    confidence: float
    area_px: float
    is_synthetic: bool
    mask: Optional[np.ndarray]  # Tile-local binary mask
    col_off: int
    row_off: int
    tile_transform: Affine
    crs: Optional[str]


def run_tile_inference(
    tile: TileData,
    detector: Optional[BaseTreeDetector] = None,
) -> List[GlobalPixelDetection]:
    """Runs model detection on a single windowed tile and translates to raster coordinates.

    Args:
        tile: TileData extracted from windowed reader.
        detector: Optional detector instance (defaults to get_detector()).

    Returns:
        List of GlobalPixelDetection objects mapped to full raster coordinates.
    """
    if detector is None:
        detector = get_detector()

    raw_detections: List[RawDetection] = detector.predict_tile(tile.image)
    global_detections: List[GlobalPixelDetection] = []

    for raw in raw_detections:
        lx_min, ly_min, lx_max, ly_max = raw.bbox

        # Filter out detections that occur inside the padded region of boundary tiles
        if lx_min >= tile.width or ly_min >= tile.height:
            continue

        # Clamp max coordinates to actual unpadded tile dimensions
        lx_max = min(lx_max, float(tile.width))
        ly_max = min(ly_max, float(tile.height))

        # Convert tile-local pixel coordinates to global full-image pixel coordinates
        gx_min = lx_min + tile.col_off
        gy_min = ly_min + tile.row_off
        gx_max = lx_max + tile.col_off
        gy_max = ly_max + tile.row_off

        global_detections.append(
            GlobalPixelDetection(
                tile_index=tile.tile_index,
                global_bbox=(gx_min, gy_min, gx_max, gy_max),
                confidence=raw.confidence,
                area_px=raw.area_px,
                is_synthetic=raw.is_synthetic,
                mask=raw.mask,
                col_off=tile.col_off,
                row_off=tile.row_off,
                tile_transform=tile.transform,
                crs=tile.crs,
            )
        )

    return global_detections
