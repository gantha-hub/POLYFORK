"""Unit tests for Polygon NMS and georeferenced stitching."""

import pytest
from shapely.geometry import box
from rasterio.transform import from_origin
from app.services.stitching import (
    polygon_iou,
    polygon_nms,
    compute_crown_area_sqm,
    stitch_and_deduplicate,
)


def test_polygon_iou():
    """Tests calculation of intersection over union between two polygons."""
    p1 = box(0, 0, 10, 10)  # Area 100
    p2 = box(5, 0, 15, 10)  # Area 100, intersection (5..10, 0..10) area 50, union 150 -> IoU = 50/150 = 0.333
    iou = polygon_iou(p1, p2)
    assert round(iou, 2) == 0.33


def test_polygon_nms_suppression():
    """Verifies that overlapping polygons with lower confidence are suppressed."""
    p1 = box(0, 0, 10, 10)
    p2 = box(1, 1, 10, 10)  # Large overlap with p1

    polys = [p1, p2]
    confs = [0.95, 0.70]  # p1 has higher confidence
    synths = [True, True]

    kept_polys, kept_confs, kept_synths = polygon_nms(
        polys, confs, synths, iou_threshold=0.35
    )

    assert len(kept_polys) == 1
    assert kept_confs[0] == 0.95


def test_compute_crown_area_sqm():
    """Tests metric area computation under geographic (EPSG:4326) and projected coordinates."""
    # Projected coordinates (10m x 10m polygon)
    poly_utm = box(500000, 1200000, 500010, 1200010)
    area_utm = compute_crown_area_sqm(poly_utm, crs="EPSG:32643")
    assert round(area_utm, 1) == 100.0

    # Geographic coordinates (0.0001 deg x 0.0001 deg at equator ~ 11.1m x 11.1m ~ 123 m^2)
    poly_geo = box(76.0, 0.0, 76.0001, 0.0001)
    area_geo = compute_crown_area_sqm(poly_geo, crs="EPSG:4326")
    assert 100.0 <= area_geo <= 140.0


def test_stitch_and_deduplicate_end_to_end():
    """Tests the full stitching pipeline converting pixel crowns to real-world StitchedTree instances."""
    p1 = box(100, 100, 150, 150)
    p2 = box(105, 105, 150, 150)  # Duplicate
    p3 = box(300, 300, 350, 350)  # Disjoint crown

    transform = from_origin(76.5, 11.2, 0.00001, 0.00001)

    trees = stitch_and_deduplicate(
        pixel_polygons=[p1, p2, p3],
        confidences=[0.90, 0.65, 0.88],
        synthetic_flags=[True, True, True],
        raster_transform=transform,
        crs="EPSG:4326",
        resolution_m=1.0,
    )

    assert len(trees) == 2  # p2 was suppressed
    for tree in trees:
        assert tree.crown_area_sqm > 0
        assert tree.is_synthetic is True
        assert tree.centroid_x != 0
        assert tree.centroid_y != 0
