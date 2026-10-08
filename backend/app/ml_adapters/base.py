"""Abstract Base Class and data structures for Tree Detection ML Adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np


@dataclass
class RawDetection:
    """Represents a raw tree detection in tile-local pixel coordinates."""

    # Box coordinates in tile pixels: (xmin, ymin, xmax, ymax)
    bbox: Tuple[float, float, float, float]
    confidence: float
    # Optional 2D binary mask for the crown in tile coordinates
    mask: Optional[np.ndarray] = None
    # Flag indicating whether this detection came from synthetic mock model
    is_synthetic: bool = False
    # Predicted crown area in square pixels
    area_px: float = 0.0


class BaseTreeDetector(ABC):
    """Abstract interface that all detector backends must implement."""

    @abstractmethod
    def load(self) -> None:
        """Loads weights, warm-up tensors, and initializes the model."""
        pass

    @abstractmethod
    def predict_tile(self, tile_image: np.ndarray) -> List[RawDetection]:
        """Runs tree crown detection on a single RGB tile.

        Args:
            tile_image: np.ndarray of shape (H, W, C) with uint8 RGB values.

        Returns:
            List of RawDetection objects with tile-local pixel coordinates.
        """
        pass

    @property
    @abstractmethod
    def is_synthetic(self) -> bool:
        """Returns True if the detector generates synthetic/mock predictions."""
        pass
