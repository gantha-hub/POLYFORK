"""Stitching and spatial deduplication service for cross-tile detections.

Implements Polygon Non-Maximum Suppression (Polygon NMS) to eliminate duplicate
crowns in tile overlap regions and converts pixel geometries to real-world GPS coordinates.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple
from rasterio.transform import Affine
from shapely.geometry import Polygon, Point
from shapely.affinity import affine_transform
from app.core.logging import logger


@dataclass
class StitchedTree:
    """Represents a unified, deduplicated tree crown ready for registration."""

    polygon_geojson: str
    centroid_x: float
    centroid_y: float
    crown_area_sqm: float
    confidence: float
    is_synthetic: bool


def polygon_iou(p1: Polygon, p2: Polygon) -> float:
    """Computes Intersection over Union (IoU) between two Shapely polygons."""
    if not p1.intersects(p2):
        return 0.0
    try:
        inter_area = p1.intersection(p2).area
        union_area = p1.area + p2.area - inter_area
        return inter_area / union_area if union_area > 0 else 0.0
    except Exception:
        return 0.0


def polygon_nms(
    polygons: List[Polygon],
    confidences: List[float],
    synthetic_flags: List[bool],
    iou_threshold: float = 0.35,
) -> Tuple[List[Polygon], List[float], List[bool]]:
    """Runs Polygon Non-Maximum Suppression to remove boundary duplicates."""
    if not polygons:
        return [], [], []

    # Sort indices by confidence descending
    sorted_indices = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)

    kept_indices: List[int] = []

    for idx in sorted_indices:
        poly_candidate = polygons[idx]
        is_duplicate = False

        for kept_idx in kept_indices:
            poly_kept = polygons[kept_idx]
            iou = polygon_iou(poly_candidate, poly_kept)
            if iou > iou_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            kept_indices.append(idx)

    kept_polys = [polygons[i] for i in kept_indices]
    kept_confs = [confidences[i] for i in kept_indices]
    kept_synths = [synthetic_flags[i] for i in kept_indices]

    return kept_polys, kept_confs, kept_synths


def transform_pixel_to_geo(
    pixel_polygon: Polygon,
    transform: Affine,
) -> Polygon:
    """Transforms a polygon from pixel coordinates to real-world coordinates using Affine matrix.

    Affine formula: x_geo = a*col + b*row + c, y_geo = d*col + e*row + f
    Shapely affine_transform takes [a, b, d, e, xoff, yoff] = [a, b, d, e, c, f]
    """
    matrix = [
        transform.a,
        transform.b,
        transform.d,
        transform.e,
        transform.c,
        transform.f,
    ]
    return affine_transform(pixel_polygon, matrix)


def compute_crown_area_sqm(
    poly_geo: Polygon,
    crs: Optional[str],
    resolution_m: float = 0.1,
    poly_px_area: float = 0.0,
) -> float:
    """Calculates ground projection area in square meters.

    If CRS is geographic (degrees, EPSG:4326), applies latitude-dependent metric scaling.
    If CRS is projected (meters), uses poly_geo.area directly.
    If unreferenced, scales pixel area by resolution_m^2.
    """
    if crs and "4326" in crs:
        # Convert degrees^2 to m^2 using centroid latitude
        lat = poly_geo.centroid.y
        lat_rad = math.radians(lat)
        # 1 deg lat ~ 110,540 m; 1 deg lon ~ 111,320 m * cos(lat)
        m_per_deg_lat = 110540.0
        m_per_deg_lon = 111320.0 * math.cos(lat_rad)
        area_sqm = poly_geo.area * (m_per_deg_lat * m_per_deg_lon)
        return max(1.0, round(area_sqm, 2))
    elif crs:
        # Projected CRS in meters (e.g. UTM)
        return max(1.0, round(poly_geo.area, 2))
    else:
        # Unreferenced pixels
        px_area = poly_px_area if poly_px_area > 0 else poly_geo.area
        return max(1.0, round(px_area * (resolution_m ** 2), 2))


def stitch_and_deduplicate(
    pixel_polygons: List[Polygon],
    confidences: List[float],
    synthetic_flags: List[bool],
    raster_transform: Affine,
    crs: Optional[str],
    resolution_m: float = 0.1,
    iou_threshold: float = 0.35,
) -> List[StitchedTree]:
    """Applies Polygon NMS and converts surviving crowns into georeferenced StitchedTree instances.

    Args:
        pixel_polygons: List of crown polygons in global image pixel coordinates.
        confidences: Corresponding detection confidences.
        synthetic_flags: Flags indicating if each detection is synthetic.
        raster_transform: Master Affine transform of the raster.
        crs: Coordinate reference system string (e.g. "EPSG:4326").
        resolution_m: Ground sampling distance in meters per pixel.
        iou_threshold: Overlap IoU threshold for duplicate elimination.

    Returns:
        List of deduplicated StitchedTree instances.
    """
    import json
    from shapely.geometry import mapping

    # 1. Run Polygon NMS in pixel space
    surviving_polys, surviving_confs, surviving_synths = polygon_nms(
        pixel_polygons,
        confidences,
        synthetic_flags,
        iou_threshold=iou_threshold,
    )

    stitched_trees: List[StitchedTree] = []

    for poly_px, conf, is_synth in zip(surviving_polys, surviving_confs, surviving_synths):
        # 2. Transform polygon coordinates to real-world CRS or keep pixel
        if crs is not None and not raster_transform.is_identity:
            poly_geo = transform_pixel_to_geo(poly_px, raster_transform)
            cx, cy = float(poly_geo.centroid.x), float(poly_geo.centroid.y)
        else:
            poly_geo = poly_px
            cx, cy = float(poly_px.centroid.x), float(poly_px.centroid.y)

        # 3. Calculate crown area in square meters
        area_sqm = compute_crown_area_sqm(
            poly_geo=poly_geo,
            crs=crs,
            resolution_m=resolution_m,
            poly_px_area=poly_px.area,
        )

        geojson_str = json.dumps(mapping(poly_geo))

        stitched_trees.append(
            StitchedTree(
                polygon_geojson=geojson_str,
                centroid_x=cx,
                centroid_y=cy,
                crown_area_sqm=area_sqm,
                confidence=round(conf, 4),
                is_synthetic=is_synth,
            )
        )

    return stitched_trees
