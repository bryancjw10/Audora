#Uses YOLOv11 to find text regions in a document image
# Loads trained YOLO model once at startup (expensive to reload per page)
# Filters output to only paragraph + title classes for OCR

import numpy as np
from ultralytics import YOLO
import config


class DocumentDetector:
    """Loads the trained YOLO model and detects text regions."""

    def __init__(self):
        # Load the trained model
        self.model = YOLO(config.YOLO_MODEL_PATH)
        self.class_names = self.model.names

        # Filter to only text-related classes
        self.text_ids = set()
        for i, name in self.class_names.items():
            if name.lower() in config.TEXT_CLASSES:
                self.text_ids.add(i)

    def detect(self, image):
        """
        Takes a page image, returns list of detected text regions.
        Each region has bbox coordinates, class name, and confidence.
        """
        h, w = image.shape[:2]

        # Run YOLO prediction
        results = self.model.predict(
            source=image,
            conf=config.YOLO_CONFIDENCE,
            iou=config.YOLO_IOU,
            imgsz=config.YOLO_IMG_SIZE,
            verbose=False,
        )

        boxes = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls_id = int(box.cls[0])

                # Skip non-text classes like figures or tables
                if cls_id not in self.text_ids:
                    continue

                # Get bounding box coordinates
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # Keep coordinates within image bounds
                x1 = max(0, int(x1))
                y1 = max(0, int(y1))
                x2 = min(w, int(x2))
                y2 = min(h, int(y2))

                # Skip boxes that are too small
                if (x2 - x1) < 10 or (y2 - y1) < 10:
                    continue

                boxes.append({
                    "bbox": (x1, y1, x2, y2),
                    "class": self.class_names[cls_id],
                    "conf": round(float(box.conf[0]), 3),
                })

        # If nothing detected, use the whole page as fallback
        if not boxes:
            return [{"bbox": (0, 0, w, h), "class": "full_page", "conf": 0.0}]

        # Sort in reading order with column detection
        if boxes:
            # Check if there are two distinct clusters of x1 positions
            x1_values = sorted([b["bbox"][0] for b in boxes])
            max_gap = 0
            gap_pos = 0
            for i in range(1, len(x1_values)):
                gap = x1_values[i] - x1_values[i-1]
                if gap > max_gap:
                    max_gap = gap
                    gap_pos = (x1_values[i-1] + x1_values[i]) / 2

            # 20% threshold, below 0.2 give false splits
            if max_gap > w * 0.2:
                left_cols = [b for b in boxes if b["bbox"][0] < gap_pos]
                right_cols = [b for b in boxes if b["bbox"][0] >= gap_pos]

                print(f"  USING TWO-COLUMN SORT - left={len(left_cols)} right={len(right_cols)} gap={max_gap:.0f}")

                left_cols.sort(key=lambda b: b["bbox"][1])
                right_cols.sort(key=lambda b: b["bbox"][1])
                boxes = left_cols + right_cols
            else:
                print(f"  USING SINGLE COLUMN SORT - max_gap={max_gap:.0f}")

                boxes.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

        # DEBUG - for diagnosing reading order issues
        for b in boxes:
            print(f"  [{b['class']}] x1={b['bbox'][0]} y1={b['bbox'][1]} text_side={'LEFT' if b['bbox'][0] < w/2 else 'RIGHT'}")
        print(f"  Page width={w}, midpoint={w/2}")

        print(f"  SORTED y1 values: {[b['bbox'][1] for b in boxes[:5]]}")

        return boxes