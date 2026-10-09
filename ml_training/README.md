# 🌲 VrikshaVision ML Model Training Suite

This folder provides everything needed to train, fine-tune, and evaluate state-of-the-art computer vision models (**YOLOv8** and **DeepForest**) on aerial drone imagery for individual tree crown (ITC) detection and canopy instance segmentation.

---

## 📁 Directory Structure

```text
vrikshavision/ml_training/
├── prepare_dataset.py       # Slices drone orthomosaics into 640x640 tiles & creates labels
├── train_yolo.py            # Fine-tunes YOLOv8 on canopy tiles
├── infer_yolo.py            # Runs real-time inference on test tiles or camera stream
├── train_deepforest.py      # Fine-tunes DeepForest (RetinaNet) on canopy tiles
├── dataset/                 # Generated image tiles and label annotations (ignored in git)
│   ├── images/train/
│   ├── images/val/
│   ├── labels/train/
│   ├── labels/val/
│   └── dataset.yaml         # YOLO dataset configuration
└── models/                  # Exported weights (.pt) (ignored in git)
    └── vrikshavision_yolo_tree.pt
```

---

## 🚀 Quickstart: Windows (PowerShell) Commands

### 1. Open PowerShell & Navigate to the Training Folder
```powershell
cd $HOME\vrikshavision\backend

# Activate your virtual environment
.\.venv\Scripts\Activate.ps1

# Navigate to ml_training
cd ..\ml_training
```

### 2. Prepare the Training Dataset
Extracts tiles from aerial surveys and creates annotations in YOLO and DeepForest formats:
```powershell
python prepare_dataset.py
```

### 3. Train the YOLOv8 Canopy Model
Fine-tunes the YOLOv8 architecture on the prepared drone tiles:
```powershell
python train_yolo.py 5
```
*(The number `5` specifies the number of training epochs. Increase to `30-50` for production).*

### 4. Test Real-Time Inference on a Single Tile
Runs the newly trained model on validation tiles and outputs detected tree coordinates and confidence scores:
```powershell
python infer_yolo.py
```

### 5. Run Full Orthomosaic Tiling & Export GeoJSON Digital Twin
Runs windowed sliding tiling across an entire aerial GeoTIFF drone survey, performs Non-Maximum Suppression (NMS), computes tree crown area, DBH, and carbon stock, and outputs a standard GIS GeoJSON:
```powershell
python predict_orthomosaic.py ..\backend\data\demo_aerial_tile.tif
```
*(The output GeoJSON file is saved to `ml_training\outputs\predicted_stand.geojson` ready to be visualized directly on the map).*

---

## 🎯 Fine-Tuning DeepForest

If you wish to use DeepForest:
```powershell
# Install DeepForest
pip install deepforest albumentations

# Run training
python train_deepforest.py 5
```

---

## 🔄 Active Learning Loop with VrikshaVision

1. Fly drone & upload GeoTIFF via the VrikshaVision frontend (**Surveys Page**).
2. The model detects tree crowns across the stand.
3. Crowns with epistemic uncertainty appear in the **Audit Queue** (**Verify Page**).
4. As human foresters **Approve**, **Reject**, or **Edit** crowns, these verified records are exported back to `dataset/` to continuously retrain and improve your AI model!
