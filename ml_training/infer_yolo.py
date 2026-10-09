#!/usr/bin/env python3
"""Run real-time inference using the fine-tuned YOLO tree canopy model.

Predicts tree crowns on drone tiles or live drone video feed.
"""

import os
import sys
from ultralytics import YOLO

def run_inference(image_path: str, model_path: str = None):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if model_path is None:
        model_path = os.path.join(base_dir, "models", "vrikshavision_yolo_tree.pt")
        if not os.path.exists(model_path):
            model_path = "yolov8n.pt"

    print(f"Loading model: {model_path}")
    model = YOLO(model_path)

    print(f"Running inference on: {image_path}")
    results = model.predict(source=image_path, conf=0.25, save=False)

    for i, r in enumerate(results):
        boxes = r.boxes
        print(f"\nDetection Results for {image_path}:")
        print(f"  Total tree crowns detected: {len(boxes)}")
        for box in boxes:
            coords = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            print(f"  - Tree [xmin={coords[0]:.1f}, ymin={coords[1]:.1f}, xmax={coords[2]:.1f}, ymax={coords[3]:.1f}] Confidence: {conf*100:.1f}%")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_img = os.path.join(base_dir, "dataset", "images", "val", "canopy_tile_000.png")
    if len(sys.argv) > 1:
        test_img = sys.argv[1]

    if not os.path.exists(test_img):
        print(f"Test image not found at {test_img}. Run prepare_dataset.py first.")
        sys.exit(1)

    run_inference(test_img)
