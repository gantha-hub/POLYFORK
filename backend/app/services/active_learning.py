"""Active learning and human-in-the-loop verification service.

Identifies the most uncertain or anomalous tree crowns for expert field audit
and stores corrections for downstream model retraining.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from shapely.geometry import shape
from app.models.tree import Tree
from app.models.verification import Verification
from app.core.logging import logger


def calculate_uncertainty_score(tree: Tree) -> Tuple[float, str]:
    """Calculates an active learning priority score based on prediction confidence and geometry anomalies.

    Higher score = higher priority for human verification.
    """
    conf = float(tree.confidence)
    area = float(tree.crown_area_sqm)

    # 1. Prediction uncertainty: close to classification threshold (0.50) or low confidence
    uncertainty_score = 1.0 - conf

    # 2. Geometric anomaly: unusually tiny (< 3 sqm) or massive (> 200 sqm) crowns
    anomaly_penalty = 0.0
    reason = "Low model confidence"

    if area < 3.0:
        anomaly_penalty = 0.3
        reason = "Extremely small crown anomaly (< 3m²)"
    elif area > 200.0:
        anomaly_penalty = 0.35
        reason = "Massive crown / possible fused cluster (> 200m²)"
    elif conf < 0.65:
        reason = f"Borderline detection confidence ({round(conf, 2)})"

    priority = round(min(1.0, uncertainty_score * 0.7 + anomaly_penalty * 0.3), 3)
    return priority, reason


from typing import Tuple


def rank_trees_for_verification(
    trees: List[Tree],
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Ranks unverified trees to produce a prioritized audit queue.

    Args:
        trees: List of candidate Tree records.
        limit: Max number of prioritized trees to return.

    Returns:
        List of serialized tree records ordered by verification priority descending.
    """
    # Only audit trees that are currently in 'detected' status
    unverified = [t for t in trees if t.status in ["detected", "edited"]]

    scored_items = []
    for tree in unverified:
        priority, reason = calculate_uncertainty_score(tree)
        scored_items.append((priority, reason, tree))

    # Sort descending by priority score
    scored_items.sort(key=lambda item: item[0], reverse=True)

    results = []
    for priority, reason, tree in scored_items[:limit]:
        results.append({
            "tree_id": tree.tree_id,
            "survey_id": tree.survey_id,
            "confidence": tree.confidence,
            "crown_area_sqm": tree.crown_area_sqm,
            "centroid_x": tree.centroid_x,
            "centroid_y": tree.centroid_y,
            "geometry_geojson": tree.geometry_geojson,
            "priority_score": priority,
            "audit_reason": reason,
            "status": tree.status,
            "data_source": tree.data_source,
        })

    return results
