"""PyTorch Model Adapter for real tree crown detection weights."""

from pathlib import Path
from typing import List, Optional
import numpy as np
import torch
from app.ml_adapters.base import BaseTreeDetector, RawDetection
from app.ml_adapters.mock_model import MockModel
from app.core.logging import logger


class TorchModel(BaseTreeDetector):
    """Deep learning detector that loads PyTorch weights from disk with CPU/GPU fallback."""

    def __init__(self, weights_path: str = "./weights/tree_detector_weights.pt"):
        self.weights_path = Path(weights_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[torch.nn.Module] = None
        self._fallback_mock: Optional[MockModel] = None
        self._is_synthetic_fallback: bool = False

    def load(self) -> None:
        """Loads weights from weights_path. 

        If weights file does not exist, logs a notice and initializes MockModel fallback.
        """
        logger.info(f"Targeting PyTorch device: {self.device}")

        if not self.weights_path.exists():
            logger.warning(
                f"Weights file not found at '{self.weights_path}'. "
                "Falling back to MockModel with 'is_synthetic=True' to ensure results are never fabricated."
            )
            self._fallback_mock = MockModel()
            self._fallback_mock.load()
            self._is_synthetic_fallback = True
            return

        try:
            logger.info(f"Loading PyTorch model weights from {self.weights_path}...")
            # Try loading as TorchScript first, fallback to standard torch.load
            try:
                self.model = torch.jit.load(str(self.weights_path), map_location=self.device)
            except Exception:
                loaded_obj = torch.load(str(self.weights_path), map_location=self.device)
                if isinstance(loaded_obj, torch.nn.Module):
                    self.model = loaded_obj
                else:
                    logger.warning("Loaded object is a state_dict without model definition. Using fallback.")
                    self._fallback_mock = MockModel()
                    self._fallback_mock.load()
                    self._is_synthetic_fallback = True
                    return

            self.model.to(self.device)
            self.model.eval()
            self._is_synthetic_fallback = False
            logger.info("PyTorch weights loaded successfully into memory.")
        except Exception as exc:
            logger.error(f"Failed to load PyTorch weights: {exc}. Activating safe MockModel fallback.")
            self._fallback_mock = MockModel()
            self._fallback_mock.load()
            self._is_synthetic_fallback = True

    @property
    def is_synthetic(self) -> bool:
        """Returns True if running in fallback mock mode, False if using real weights."""
        return self._is_synthetic_fallback

    def predict_tile(self, tile_image: np.ndarray) -> List[RawDetection]:
        """Runs PyTorch inference on tile tensor.

        Args:
            tile_image: np.ndarray (H, W, C), uint8 RGB.

        Returns:
            List of RawDetection instances.
        """
        if self._is_synthetic_fallback or self.model is None:
            if self._fallback_mock is None:
                self.load()
            return self._fallback_mock.predict_tile(tile_image)

        # Preprocess input array: (H, W, C) -> (1, C, H, W) float32 normalized
        tensor = torch.from_numpy(tile_image).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        tensor = tensor.to(self.device)

        with torch.no_grad():
            output = self.model(tensor)

        # Standard bounding box / instance decoding from model output
        detections: List[RawDetection] = []
        # If output is a list of dicts (torchvision standard detection format)
        if isinstance(output, (list, tuple)) and len(output) > 0 and isinstance(output[0], dict):
            preds = output[0]
            boxes = preds.get("boxes", torch.empty((0, 4))).cpu().numpy()
            scores = preds.get("scores", torch.empty(0)).cpu().numpy()
            masks = preds.get("masks", None)
            if masks is not None:
                masks = masks.squeeze(1).cpu().numpy() > 0.5

            for idx in range(len(scores)):
                conf = float(scores[idx])
                if conf < 0.40:
                    continue
                box = boxes[idx]
                mask_i = masks[idx] if masks is not None else None
                area = float(np.sum(mask_i)) if mask_i is not None else float((box[2] - box[0]) * (box[3] - box[1]))
                detections.append(
                    RawDetection(
                        bbox=(float(box[0]), float(box[1]), float(box[2]), float(box[3])),
                        confidence=round(conf, 4),
                        mask=mask_i,
                        is_synthetic=False,
                        area_px=area,
                    )
                )

        return detections
