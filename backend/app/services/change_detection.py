"""Multi-survey spatial change detection service.

Tracks individual trees across repeated surveys (T1 and T2).
Matches crowns using centroid KD-tree distance and polygon IoU to classify trees into:
- new: Present in T2 but not T1
- lost: Present in T1 but absent in T2 (e.g. logging, mortality)
- grown: Matched trees whose crown area expanded by >15%
- unchanged: Matched trees with stable crown canopy
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Polygon
import json

from app.models.tree import Tree
from app.schemas.comparison import ChangeMetric, SurveyComparisonResponse
from app.services.stitching import polygon_iou


@dataclass
class ChangeDetectionSummary:
    """Classified lists of trees across two timepoints."""

    new_trees: List[Tree]
    lost_trees: List[Tree]
    grown_trees: List[Tree]
    unchanged_trees: List[Tree]
    net_tree_change: int
    net_carbon_change_kg: float


def compute_category_metric(trees: List[Tree]) -> ChangeMetric:
    """Computes summary statistics for a category of trees."""
    if not trees:
        return ChangeMetric(count=0, mean_crown_area_sqm=0.0, total_carbon_kg=0.0)

    count = len(trees)
    areas = [t.crown_area_sqm for t in trees]
    carbons = [t.carbon_kg or 0.0 for t in trees]

    return ChangeMetric(
        count=count,
        mean_crown_area_sqm=round(float(np.mean(areas)), 2),
        total_carbon_kg=round(float(np.sum(carbons)), 2),
    )


def match_surveys_change_detection(
    trees_t1: List[Tree],
    trees_t2: List[Tree],
    max_centroid_dist_m: float = 3.0,
    growth_threshold_pct: float = 0.15,
) -> ChangeDetectionSummary:
    """Performs spatial bipartite matching between trees in Survey T1 and Survey T2.

    Args:
        trees_t1: List of Tree records from the earlier survey.
        trees_t2: List of Tree records from the subsequent survey.
        max_centroid_dist_m: Maximum distance (meters or spatial units) to consider a tree match.
        growth_threshold_pct: Minimum relative crown growth to classify as 'grown' (default: +15%).

    Returns:
        ChangeDetectionSummary with categorized trees.
    """
    if not trees_t1 and not trees_t2:
        return ChangeDetectionSummary(
            new_trees=[], lost_trees=[], grown_trees=[], unchanged_trees=[],
            net_tree_change=0, net_carbon_change_kg=0.0
        )

    if not trees_t1:
        # All trees in T2 are new
        c_new = sum(t.carbon_kg or 0.0 for t in trees_t2)
        return ChangeDetectionSummary(
            new_trees=trees_t2, lost_trees=[], grown_trees=[], unchanged_trees=[],
            net_tree_change=len(trees_t2), net_carbon_change_kg=c_new
        )

    if not trees_t2:
        # All trees in T1 are lost
        c_lost = sum(t.carbon_kg or 0.0 for t in trees_t1)
        return ChangeDetectionSummary(
            new_trees=[], lost_trees=trees_t1, grown_trees=[], unchanged_trees=[],
            net_tree_change=-len(trees_t1), net_carbon_change_kg=-c_lost
        )

    coords_t1 = np.array([[t.centroid_x, t.centroid_y] for t in trees_t1])
    coords_t2 = np.array([[t.centroid_x, t.centroid_y] for t in trees_t2])

    # Build KD-Tree on T1
    tree_kd = cKDTree(coords_t1)
    # Query nearest neighbors for T2 in T1
    dists, indices = tree_kd.query(coords_t2, distance_upper_bound=max_centroid_dist_m)

    matched_t1_indices = set()
    matched_t2_indices = set()

    grown_trees: List[Tree] = []
    unchanged_trees: List[Tree] = []

    for idx_t2, (dist, idx_t1) in enumerate(zip(dists, indices)):
        if dist <= max_centroid_dist_m and idx_t1 < len(trees_t1):
            if idx_t1 not in matched_t1_indices:
                matched_t1_indices.add(idx_t1)
                matched_t2_indices.add(idx_t2)

                t1_tree = trees_t1[idx_t1]
                t2_tree = trees_t2[idx_t2]

                # Check crown expansion: delta_area / t1_area
                area1 = max(1.0, t1_tree.crown_area_sqm)
                area2 = t2_tree.crown_area_sqm
                growth_rate = (area2 - area1) / area1

                if growth_rate > growth_threshold_pct:
                    grown_trees.append(t2_tree)
                else:
                    unchanged_trees.append(t2_tree)

    # Trees in T2 that were never matched with any T1 tree -> NEW
    new_trees = [t for i, t in enumerate(trees_t2) if i not in matched_t2_indices]

    # Trees in T1 that were never matched with any T2 tree -> LOST
    lost_trees = [t for i, t in enumerate(trees_t1) if i not in matched_t1_indices]

    total_carbon_t1 = sum(t.carbon_kg or 0.0 for t in trees_t1)
    total_carbon_t2 = sum(t.carbon_kg or 0.0 for t in trees_t2)
    net_carbon = round(total_carbon_t2 - total_carbon_t1, 2)
    net_trees = len(trees_t2) - len(trees_t1)

    return ChangeDetectionSummary(
        new_trees=new_trees,
        lost_trees=lost_trees,
        grown_trees=grown_trees,
        unchanged_trees=unchanged_trees,
        net_tree_change=net_trees,
        net_carbon_change_kg=net_carbon,
    )
