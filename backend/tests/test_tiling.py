"""Unit tests for the windowed raster tiling service."""

from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from app.services.tiling import inspect_raster, generate_tiles, TileData


@pytest.fixture
def sample_geotiff(tmp_path: Path) -> Path:
    """Generates a synthetic 1024x1024 3-band GeoTIFF with EPSG:4326 georeferencing."""
    file_path = tmp_path / "sample_raster.tif"
    width, height = 1024, 1024
    transform = from_origin(76.50, 11.20, 0.00001, 0.00001)  # ~1m GSD in degrees

    # Create dummy RGB image with green tones
    r = np.full((height, width), 40, dtype=np.uint8)
    g = np.full((height, width), 160, dtype=np.uint8)
    b = np.full((height, width), 50, dtype=np.uint8)
    data = np.stack([r, g, b])

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)

    return file_path


def test_inspect_raster(sample_geotiff: Path):
    """Verifies that raster metadata is inspected correctly without loading full image."""
    meta = inspect_raster(sample_geotiff)
    assert meta.width == 1024
    assert meta.height == 1024
    assert meta.count == 3
    assert meta.is_georeferenced is True
    assert "4326" in str(meta.crs)


def test_generate_tiles_windowing_and_overlap(sample_geotiff: Path):
    """Verifies 512x512 tile extraction with 20% overlap."""
    tiles = list(generate_tiles(sample_geotiff, tile_size=512, overlap_pct=0.20))
    # Step = 512 * 0.8 = 409 or 410.
    # 1024 px length: offsets at 0, 409, 818 -> 3 steps per axis -> 9 tiles total
    assert len(tiles) >= 4

    for tile in tiles:
        assert isinstance(tile, TileData)
        assert tile.image.shape == (512, 512, 3)
        assert tile.col_off >= 0
        assert tile.row_off >= 0
        assert tile.is_georeferenced is True
        assert tile.transform is not None


def test_unreferenced_image_handling(tmp_path: Path):
    """Verifies tiling gracefully handles images without georeferencing."""
    from PIL import Image

    img_path = tmp_path / "plain_photo.jpg"
    img = Image.new("RGB", (600, 600), color=(34, 139, 34))
    img.save(img_path)

    meta = inspect_raster(img_path)
    assert meta.width == 600
    assert meta.height == 600
    assert meta.is_georeferenced is False

    tiles = list(generate_tiles(img_path, tile_size=512, overlap_pct=0.20))
    assert len(tiles) > 0
    assert tiles[0].image.shape == (512, 512, 3)
    assert tiles[0].is_georeferenced is False
