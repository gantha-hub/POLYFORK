"""ML Adapters package for VrikshaVision.

Provides model backends (MockModel and TorchModel) with automatic fallback and factory instantiation.
"""

from app.config import settings
from app.ml_adapters.base import BaseTreeDetector, RawDetection
from app.ml_adapters.mock_model import MockModel
from app.ml_adapters.torch_model import TorchModel

_active_detector: BaseTreeDetector | None = None


def get_detector() -> BaseTreeDetector:
    """Returns the singleton detector instance based on settings.MODEL_BACKEND."""
    global _active_detector
    if _active_detector is None:
        if settings.MODEL_BACKEND == "torch":
            _active_detector = TorchModel(weights_path=settings.WEIGHTS_PATH)
        else:
            _active_detector = MockModel()
        _active_detector.load()
    return _active_detector


def reset_detector() -> None:
    """Resets the singleton detector (useful for unit tests)."""
    global _active_detector
    _active_detector = None


__all__ = [
    "BaseTreeDetector",
    "RawDetection",
    "MockModel",
    "TorchModel",
    "get_detector",
    "reset_detector",
]
