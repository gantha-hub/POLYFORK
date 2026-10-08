"""Tree Registry service for stable IDs, attributes, and GeoJSON export.

Generates deterministic spatial UUIDs and standard GeoJSON FeatureCollections.
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from app.models.tree import Tree
from app.services.stitching import StitchedTree


def generate_stable_tree_id(survey_id: str, centroid_x: float, centroid_y: float) -> str:
    """Generates a reproducible, deterministic UUID based on survey ID and spatial coordinates."""
    # Round coordinates to 6 decimals (millimeter precision) for robust hash stability
    hash_str = f"{survey_id}:{round(centroid_x, 6)}:{round(centroid_y, 6)}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, hash_str))


def create_tree_record(
    survey_id: str,
    stitched: StitchedTree,
    forest_type: str = "tropical_moist",
) -> Tree:
    """Instantiates a Tree ORM record from a stitched detection with allometric estimates."""
    tree_id = generate_stable_tree_id(survey_id, stitched.centroid_x, stitched.centroid_y)

    # Initial rough allometric estimates (CPA -> DBH -> Carbon)
    # Refined later through the dedicated carbon service
    cpa = stitched.crown_area_sqm
    # Baseline power-law: DBH ~ 1.5 * CPA^0.6
    dbh = max(5.0, round(1.5 * (cpa ** 0.6), 2))
    # Biomass ~ exp(-2.0 + 2.1 * ln(dbh))
    import math
    biomass = max(10.0, round(math.exp(-2.0 + 2.1 * math.log(dbh)), 2))
    carbon = round(biomass * 0.47, 2)

    return Tree(
        tree_id=tree_id,
        survey_id=survey_id,
        geometry_geojson=stitched.polygon_geojson,
        centroid_x=stitched.centroid_x,
        centroid_y=stitched.centroid_y,
        crown_area_sqm=cpa,
        confidence=stitched.confidence,
        dbh_cm=dbh,
        biomass_kg=biomass,
        carbon_kg=carbon,
        status="detected",
        data_source="synthetic" if stitched.is_synthetic else "real",
    )


def trees_to_geojson_feature_collection(trees: List[Tree]) -> Dict[str, Any]:
    """Serializes a list of Tree records into a standard GeoJSON FeatureCollection."""
    features = []

    for tree in trees:
        try:
            geometry = json.loads(tree.geometry_geojson)
        except Exception:
            geometry = {
                "type": "Point",
                "coordinates": [tree.centroid_x, tree.centroid_y],
            }

        properties = {
            "tree_id": tree.tree_id,
            "survey_id": tree.survey_id,
            "crown_area_sqm": tree.crown_area_sqm,
            "confidence": tree.confidence,
            "dbh_cm": tree.dbh_cm,
            "biomass_kg": tree.biomass_kg,
            "carbon_kg": tree.carbon_kg,
            "status": tree.status,
            "data_source": tree.data_source,
            "notes": tree.notes,
        }

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
