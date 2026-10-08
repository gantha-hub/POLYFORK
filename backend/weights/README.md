# VrikshaVision ML Model Weights Directory

This directory stores real trained deep-learning model weights for tree crown detection and instance segmentation.

## Expected Formats
You can place your trained PyTorch weights here:
- **PyTorch State Dictionary or TorchScript**: `tree_detector_weights.pt` or `tree_detector_weights.pth`
- **Supported Architectures**: Mask R-CNN, DeepForest, YOLOv8-seg, or U-Net instance segmentation models.

## How to Enable Real Weights
1. Place your trained model file into this directory:
   ```
   vrikshavision/backend/weights/tree_detector_weights.pt
   ```
2. Update your `.env` file:
   ```bash
   MODEL_BACKEND=torch
   WEIGHTS_PATH=./weights/tree_detector_weights.pt
   ```
3. Restart the backend service. The `TorchModel` adapter will load these weights into memory (supporting CPU fallback or CUDA GPU if available).

## Default Behavior without Weights
If no weights file is present or `MODEL_BACKEND=mock` is set, the system uses the built-in `MockModel` adapter.
All API responses will explicitly report:
```json
"data_source": "synthetic"
```
and PDF exports will display a prominent **"SYNTHETIC DATA DEMO"** watermark to prevent unverified results from being mistaken for real survey data.
