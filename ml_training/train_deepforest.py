#!/usr/bin/env python3
"""Fine-tune DeepForest on Custom Aerial Tree Canopy Dataset.

This script fine-tunes the PyTorch RetinaNet backbone on drone tiles
using the deepforest annotations CSV.
"""

import os
import sys

def train_deepforest(annotations_csv: str, tiles_dir: str, epochs: int = 5):
    try:
        from deepforest import main
    except ImportError:
        print("DeepForest is not installed in this environment.")
        print("To install DeepForest on your machine, run:")
        print("  pip install deepforest albumentations")
        return

    print("=" * 65)
    print("🌲 VRIKSHAVISION: FINE-TUNING DEEPFOREST (RETINANET)")
    print("=" * 65)
    print(f"Annotations CSV: {annotations_csv}")
    print(f"Tiles Directory: {tiles_dir}")
    print(f"Epochs: {epochs}")

    model = main.deepforest()
    model.use_release()

    model.config["train"]["csv_file"] = annotations_csv
    model.config["train"]["root_dir"] = tiles_dir
    model.config["train"]["epochs"] = epochs
    model.config["train"]["lr"] = 0.001
    model.config["batch_size"] = 4

    model.create_trainer()
    print("Starting training passes...")
    model.trainer.fit(model)

    output_path = os.path.join(os.path.dirname(annotations_csv), "..", "models", "vrikshavision_deepforest.pt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.model.save(output_path)
    print(f"Saved fine-tuned DeepForest weights to: {output_path}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, "dataset", "deepforest_annotations.csv")
    tiles = os.path.join(base_dir, "dataset", "images", "train")
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    train_deepforest(csv_file, tiles, epochs=epochs)
