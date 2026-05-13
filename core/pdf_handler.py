# Converts PDF pages into images for processing

import numpy as np
import fitz  # To call PyMuPDF

# 300 dpi is sweet spot
def pdf_to_images(pdf_path, dpi=300):
    """
    Opens a PDF and converts each page into an image.
    Returns a list of images (as numpy arrays), one per page.
    """
    doc = fitz.open(pdf_path)
    images = []

    zoom = dpi / 72  # Default PDF resolution is 72 DPI
    matrix = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=matrix)

        # Convert to numpy array
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)

        # If image has 4 channels (RGBA), keep only RGB
        if pix.n == 4:
            img = img[:, :, :3]

        images.append(img.copy())

    doc.close()
    return images


def get_page_count(pdf_path):
    """Returns total number of pages in a PDF."""
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count