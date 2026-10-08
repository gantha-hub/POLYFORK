"""Unit tests for ML Adapters (MockModel, TorchModel) and tile inference service."""

import numpy as np
import pytest
from rasterio.windows import Window
from rasterio.transform import Affine
from app.ml_adapters.mock_model import MockModel
from app.ml_adapters.torch_model import TorchModel
from app.services.tiling import TileData
from app.services.inference import run_tile_inference


def test_mock_model_detections_labeled_synthetic():
    """Verifies that MockModel returns clearly labeled synthetic detections."""
    model = MockModel()
    model.load()
    assert model.is_synthetic is True

    # Generate synthetic image with green tree patches
    tile = np.zeros((512, 512, 3), dtype=np.uint8)
    tile[:, :, 1] = 120  # Green background
    # Add a few high-intensity green clusters
    tile[100:150, 100:150, 1] = 240
    tile[300:350, 300:350, 1] = 230

    detections = model.predict_tile(tile)
    assert len(detections) > 0

    for det in detections:
        assert det.is_synthetic is True
        assert 0.60 <= det.confidence <= 0.98
        assert det.area_px > 0
        assert len(det.bbox) == 4
        xmin, ymin, xmax, ymax = det.bbox
        assert xmin < xmax
        assert ymin < ymax


def test_torch_model_fallback_when_weights_missing(tmp_path):
    """Verifies TorchModel falls back to MockModel with is_synthetic=True when weights are absent."""
    missing_weights = tmp_path / "non_existent_weights.pt"
    torch_model = TorchModel(weights_path=str(missing_weights))
    torch_model.load()

    assert torch_model.is_synthetic is True

    dummy_image = np.full((512, 512, 3), 100, dtype=np.uint8)
    dummy_image[200:250, 200:250, 1] = 250
    detections = torch_model.predict_tile(dummy_image)

    assert isinstance(detections, list)
    for det in detections:
        assert det.is_synthetic is True


def test_run_tile_inference_translates_to_global_coords():
    """Verifies local tile detections are correctly offset to global full-raster coordinates."""
    col_off, row_off = 410, 410
    tile_data = TileData(
        tile_index=1,
        window=Window(col_off, row_off, 512, 512),
        col_off=col_off,
        row_off=row_off,
        width=512,
        height=512,
        image=np.full((512, 512, 3), 130, dtype=np.uint8),
        transform=Affine.identity(),
        crs="EPSG:4326",
        is_georeferenced=True,
    )
    # Add green blob at local (100, 100)
    tile_data.image[80:120, 80:120, 1] = 255

    model = MockModel()
    global_dets = run_tile_inference(tile_data, detector=model)

    assert len(global_dets) > 0
    for gdet in global_dets:
        gx_min, gy_min, gx_max, gy_max = gdet.global_bbox
        # Global coordinate must be >= offset
        assert gx_min >= col_off
        assert gy_min >= row_off
        assert gdet.is_synthetic is True
