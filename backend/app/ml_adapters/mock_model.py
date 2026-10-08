"""Mock Model Adapter providing reproducible synthetic tree detections.

Explicitly marks all outputs with is_synthetic=True to ensure honest ML reporting.
Identifies tree crowns via vegetative index and local spatial clustering.
"""

from typing import List, Tuple
import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter
from app.ml_adapters.base import BaseTreeDetector, RawDetection
from app.core.logging import logger


class MockModel(BaseTreeDetector):
    """Synthetic tree crown detector for development and testing without GPU or real weights."""

    def __init__(self, min_confidence: float = 0.60, max_confidence: float = 0.98):
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self._loaded = False

    def load(self) -> None:
        """Initializes mock detector state."""
        self._loaded = True
        logger.info("MockModel initialized. All detections will be flagged as 'is_synthetic=True'.")

    @property
    def is_synthetic(self) -> bool:
        """Always True for MockModel."""
        return True

    def predict_tile(self, tile_image: np.ndarray) -> List[RawDetection]:
        """Generates synthetic tree detections based on green vegetation response and local maxima.

        Args:
            tile_image: np.ndarray of shape (H, W, C), uint8 RGB.

        Returns:
            List of RawDetection instances with is_synthetic=True.
        """
        if not self._loaded:
            self.load()

        h, w = tile_image.shape[:2]
        if h < 16 or w < 16:
            return []

        # If RGB, compute Excess Green Index (ExG = 2*G - R - B)
        if tile_image.ndim == 3 and tile_image.shape[2] >= 3:
            r = tile_image[:, :, 0].astype(np.float32)
            g = tile_image[:, :, 1].astype(np.float32)
            b = tile_image[:, :, 2].astype(np.float32)
            exg = 2.0 * g - r - b
        else:
            # Fallback for grayscale
            exg = tile_image[:, :, 0].astype(np.float32) if tile_image.ndim == 3 else tile_image.astype(np.float32)

        # Smooth to find canopy peaks
        smoothed = gaussian_filter(exg, sigma=4.0)

        # Find local peaks
        local_max = maximum_filter(smoothed, size=25) == smoothed
        val_range = float(np.max(smoothed) - np.min(smoothed))
        if val_range < 5.0:
            threshold = float(np.mean(smoothed)) + 15.0
        else:
            threshold = float(np.percentile(smoothed, 80))

        peaks = np.logical_and(local_max, smoothed >= threshold)
        y_indices, x_indices = np.where(peaks)

        # Cap max detections per 512x512 tile to top 100 for efficiency
        if len(x_indices) > 100:
            peak_vals = smoothed[y_indices, x_indices]
            top_k = np.argsort(peak_vals)[-100:]
            y_indices = y_indices[top_k]
            x_indices = x_indices[top_k]

        detections: List[RawDetection] = []


        # Deterministic pseudo-random generation based on coordinate seeds
        for idx in range(len(x_indices)):
            cx = float(x_indices[idx])
            cy = float(y_indices[idx])

            # Edge margin guard
            if cx < 8 or cx > w - 8 or cy < 8 or cy > h - 8:
                continue

            # Deterministic pseudo-random radius between 8px and 35px
            seed_val = int((cx * 13 + cy * 37 + idx * 101)) % 1000
            radius = 10.0 + (seed_val % 25)

            xmin = max(0.0, cx - radius)
            ymin = max(0.0, cy - radius)
            xmax = min(float(w), cx + radius)
            ymax = min(float(h), cy + radius)

            # Deterministic confidence between min_confidence and max_confidence
            conf = self.min_confidence + (seed_val / 1000.0) * (self.max_confidence - self.min_confidence)

            # Circular crown mask in tile coordinate space
            yy, xx = np.ogrid[:h, :w]
            dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
            crown_mask = dist_sq <= (radius ** 2)

            area_px = float(np.sum(crown_mask))

            detections.append(
                RawDetection(
                    bbox=(xmin, ymin, xmax, ymax),
                    confidence=round(conf, 4),
                    mask=crown_mask,
                    is_synthetic=True,
                    area_px=area_px,
                )
            )

        return detections
