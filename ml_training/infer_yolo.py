#!/usr/bin/env python3
"""Run real-time inference using the fine-tuned YOLO tree canopy model on ANY image.

Predicts tree crowns on any JPG, PNG, WEBP, drone orthomosaic tile, or video.
Draws bounding boxes and saves the visual result to outputs/detection_result.jpg.
"""

import os
import sys
from PIL import Image
from ultralytics import YOLO

def run_inference(image_path: str, model_path: str = None, conf: float = 0.20):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    outputs_dir = os.path.join(base_dir, "outputs")
    os.makedirs(outputs_dir, exist_ok=True)

    if model_path is None:
        model_path = os.path.join(base_dir, "models", "vrikshavision_yolo_tree.pt")
        if not os.path.exists(model_path):
            model_path = "yolov8n.pt"

    print("=" * 65)
    print("🌲 VRIKSHAVISION: PREDICTING TREE CANOPY CROWNS")
    print("=" * 65)
    print(f"Input Image : {image_path}")
    print(f"Model Path  : {model_path}")
    print(f"Confidence  : {conf * 100:.0f}% threshold")
    print("-" * 65)

    model = YOLO(model_path)
    results = model.predict(source=image_path, conf=conf, verbose=False)

    for i, r in enumerate(results):
        boxes = r.boxes
        total_detected = len(boxes)
        print(f"\n🎉 Detection Complete:")
        print(f"  Total tree crowns detected: {total_detected}")

        for idx, box in enumerate(boxes):
            coords = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            print(f"  [{idx + 1:02d}] Tree Crown at [X: {coords[0]:.1f} → {coords[2]:.1f}, Y: {coords[1]:.1f} → {coords[3]:.1f}] | Conf: {confidence*100:.1f}%")

        # Save annotated image with bounding boxes drawn
        annotated_bgr = r.plot() # Draws bounding boxes, confidence tags, and labels
        annotated_rgb = annotated_bgr[..., ::-1] # BGR to RGB
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        output_file = os.path.join(outputs_dir, f"detected_{base_name}.jpg")
        
        pil_img = Image.fromarray(annotated_rgb)
        pil_img.save(output_file)

        print("-" * 65)
        print(f"👉 Visual annotated image saved to:")
        print(f"   {output_file}")
        print("=" * 65)
        return output_file

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Default fallback image
    test_img = os.path.join(base_dir, "dataset", "images", "val", "canopy_tile_000.png")
    if len(sys.argv) > 1:
        test_img = sys.argv[1]

    if not os.path.exists(test_img):
        print(f"Error: File not found at '{test_img}'")
        print("Usage:")
        print("  python infer_yolo.py path/to/your_image.jpg")
        sys.exit(1)

    confidence_level = float(sys.argv[2]) if len(sys.argv) > 2 else 0.20
    run_inference(test_img, conf=confidence_level)
