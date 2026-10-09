#!/usr/bin/env python3
"""Train YOLOv8 on Aerial Tree Canopy Dataset.

Loads a pre-trained YOLOv8 backbone and fine-tunes on drone tree canopy tiles.
Saves the resulting best weights to models/vrikshavision_yolo_tree.pt.
"""

import os
import sys
from ultralytics import YOLO

def train_canopy_model(dataset_yaml: str, epochs: int = 3, imgsz: int = 640):
    """Fine-tunes YOLOv8 on aerial tree canopy dataset."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    print("=" * 65)
    print("🌲 VRIKSHAVISION: TRAINING YOLOV8 TREE CANOPY MODEL")
    print("=" * 65)
    print(f"Dataset config: {dataset_yaml}")
    print(f"Epochs: {epochs}")
    print(f"Image Size: {imgsz}x{imgsz}")
    print("-" * 65)

    print("[1/3] Loading pre-trained YOLOv8 backbone...")
    model = YOLO("yolov8n.pt")

    print("[2/3] Starting transfer learning training loop...")
    results = model.train(
        data=dataset_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=4,
        workers=0,
        name="canopy_run",
        project=os.path.join(base_dir, "runs"),
        exist_ok=True,
        verbose=True,
    )

    output_model_path = os.path.join(models_dir, "vrikshavision_yolo_tree.pt")
    model.save(output_model_path)

    print("=" * 65)
    print("🎉 TRAINING COMPLETE!")
    print(f"👉 Model weights saved to: {output_model_path}")
    print("=" * 65)
    return output_model_path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_yaml = os.path.join(base_dir, "dataset", "dataset.yaml")
    
    if not os.path.exists(default_yaml):
        from prepare_dataset import generate_sample_canopy_tiles
        generate_sample_canopy_tiles(os.path.join(base_dir, "dataset"), num_tiles=16)

    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    train_canopy_model(default_yaml, epochs=epochs)
