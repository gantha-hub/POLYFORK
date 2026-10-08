"""Unit tests for watershed canopy instance segmentation."""

import numpy as np
import pytest
from app.services.instances import WatershedInstanceHead


def test_watershed_splits_touching_crowns():
    """Tests that marker-controlled watershed successfully splits two touching tree crowns."""
    mask = np.zeros((200, 200), dtype=bool)

    # Crown 1: center at (60, 100), radius 30
    yy, xx = np.ogrid[:200, :200]
    crown1 = (xx - 60) ** 2 + (yy - 100) ** 2 <= 30 ** 2

    # Crown 2: center at (110, 100), radius 30 (overlaps with crown1 between x=80 and x=90)
    crown2 = (xx - 110) ** 2 + (yy - 100) ** 2 <= 30 ** 2

    mask = np.logical_or(crown1, crown2)

    head = WatershedInstanceHead(min_distance=15, min_area_px=50.0)
    instances = head.segment(mask, base_confidence=0.90)

    # Must split into exactly 2 tree instances
    assert len(instances) == 2

    for inst in instances:
        assert inst.confidence == 0.90
        assert inst.area_px > 50.0
        assert inst.polygon.is_valid


def test_watershed_empty_mask_handling():
    """Tests that an empty mask safely returns an empty list."""
    empty_mask = np.zeros((100, 100), dtype=bool)
    head = WatershedInstanceHead()
    instances = head.segment(empty_mask)
    assert instances == []
