"""Instance segmentation service for canopy crowns.

Splits touching or overlapping tree crowns using Euclidean distance transform
and marker-controlled watershed segmentation.
Provides an extensible plug-in interface for alternate segmentation heads.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from scipy import ndimage as ndi
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.measure import find_contours
from shapely.geometry import Polygon
from app.core.logging import logger


@dataclass
class SegmentedInstance:
    """Represents an individual segmented crown instance within a tile."""

    polygon: Polygon
    area_px: float
    centroid_px: Tuple[float, float]
    confidence: float


class BaseInstanceSegmentationHead(ABC):
    """Abstract interface for instance segmentation heads."""

    @abstractmethod
    def segment(
        self,
        mask_or_prob: np.ndarray,
        base_confidence: float = 0.85,
    ) -> List[SegmentedInstance]:
        """Separates touching canopy masks into discrete tree instances."""
        pass


class WatershedInstanceHead(BaseInstanceSegmentationHead):
    """Marker-controlled watershed segmentation head for splitting clumped tree crowns."""

    def __init__(
        self,
        min_distance: int = 10,
        footprint_size: int = 7,
        min_area_px: float = 25.0,
    ):
        self.min_distance = min_distance
        self.footprint_size = footprint_size
        self.min_area_px = min_area_px

    def segment(
        self,
        mask_or_prob: np.ndarray,
        base_confidence: float = 0.85,
    ) -> List[SegmentedInstance]:
        """Runs distance transform and marker-controlled watershed on binary/probability mask.

        Args:
            mask_or_prob: 2D numpy array (bool or float) representing canopy mask.
            base_confidence: Initial detection confidence.

        Returns:
            List of discrete SegmentedInstance objects.
        """
        binary_mask = mask_or_prob > 0.5 if mask_or_prob.dtype != bool else mask_or_prob
        if not np.any(binary_mask):
            return []

        # 1. Euclidean distance transform: pixels further from background have higher values
        distance = ndi.distance_transform_edt(binary_mask)

        # 2. Find local peaks as tree crown centers/markers
        coords = peak_local_max(
            distance,
            min_distance=self.min_distance,
            labels=binary_mask,
        )

        # If no distinct peaks found, treat entire connected component as single instance
        if len(coords) == 0:
            coords = np.argwhere(distance == np.max(distance))
            if len(coords) == 0:
                return []

        # 3. Create boolean marker array
        mask_markers = np.zeros(distance.shape, dtype=bool)
        mask_markers[tuple(coords.T)] = True
        markers, _ = ndi.label(mask_markers)

        # 4. Marker-controlled watershed (flooding inverted distance map)
        labels = watershed(-distance, markers, mask=binary_mask)

        instances: List[SegmentedInstance] = []
        unique_labels = np.unique(labels)

        for lab in unique_labels:
            if lab == 0:
                continue  # Background

            instance_mask = labels == lab
            area = float(np.sum(instance_mask))
            if area < self.min_area_px:
                continue

            # Extract polygon contours
            contours = find_contours(instance_mask.astype(float), level=0.5)
            if not contours:
                continue

            # Take the largest outer contour
            largest_contour = max(contours, key=len)
            if len(largest_contour) < 3:
                continue

            # Note: find_contours returns (row, col) = (y, x). Flip to (x, y)
            coords_xy = [(float(pt[1]), float(pt[0])) for pt in largest_contour]
            try:
                poly = Polygon(coords_xy)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                if poly.is_empty or poly.area < self.min_area_px:
                    continue

                instances.append(
                    SegmentedInstance(
                        polygon=poly,
                        area_px=float(poly.area),
                        centroid_px=(float(poly.centroid.x), float(poly.centroid.y)),
                        confidence=base_confidence,
                    )
                )
            except Exception as exc:
                logger.debug(f"Failed to create polygon for contour: {exc}")
                continue

        return instances
