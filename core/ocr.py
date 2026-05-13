# Extracts text from detected regions using Tesseract OCR

import numpy as np
from PIL import Image, ImageOps
import pytesseract
import config

# Tell Python where Tesseract is installed
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


def is_dark_background(image):
    """Check if image has a dark background (e.g. dark mode documents)."""
    if len(image.shape) == 3:
        gray = np.mean(image, axis=2)
    else:
        gray = image
    return float(np.mean(gray)) < 127


def preprocess(image):
    """Convert to grayscale. If dark background, invert colours for better OCR."""
    pil_img = Image.fromarray(image).convert("L")
    if is_dark_background(np.array(pil_img)):
        pil_img = ImageOps.invert(pil_img)
    return pil_img


def ocr_single_region(image, bbox):
    """Crop a single region from the image and run OCR on it."""
    x1, y1, x2, y2 = bbox
    crop = image[y1:y2, x1:x2]

    if crop.size == 0:
        return ""

    processed = preprocess(crop)
    text = pytesseract.image_to_string(processed, lang=config.OCR_LANG)
    return text.strip()


def ocr_regions(image, detections):
    """
    Run OCR on all detected regions from a page.
    Skips regions in the bottom 10% of the page (watermarks/footers).
    """
    h = image.shape[0]
    cutoff = h * 0.90  # Ignore anything in the bottom 10%

    results = []
    for det in detections:
        # Skip regions near the bottom of the page
        if det["bbox"][1] > cutoff:
            continue

        text = ocr_single_region(image, det["bbox"])
        if text:
            results.append({
                "bbox": det["bbox"],
                "class": det["class"],
                "text": text,
            })
    return results


def ocr_fullpage(image):
    """
    OCR the entire page at once. Used as fallback when YOLO finds nothing.
    Filters out low-confidence words to reduce noise.
    """
    processed = preprocess(image)

    # Get word-level data with confidence scores
    data = pytesseract.image_to_data(
        processed, lang=config.OCR_LANG, output_type=pytesseract.Output.DICT
    )

    words = []
    for i, word in enumerate(data["text"]):
        conf = int(data["conf"][i])
        if conf >= config.OCR_MIN_CONFIDENCE and word.strip():
            words.append(word.strip())

    return " ".join(words)