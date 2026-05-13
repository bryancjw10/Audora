# Connects everything together: PDF -> YOLO -> OCR -> TTS

import os
import json
from datetime import datetime

import config
from core.detector import DocumentDetector
from core.pdf_handler import pdf_to_images
from core.ocr import ocr_regions, ocr_fullpage
from core.tts import generate_audio


class AudoraPipeline:

    def __init__(self):
        self.detector = DocumentDetector()

    def process_page(self, image, page_num, doc_id):
        """Process one page: detect text regions -> OCR -> generate audio."""

        # Step 1: Detect text regions using YOLO
        detections = self.detector.detect(image)

        # Step 2: Extract text using Tesseract
        if detections[0]["class"] == "full_page":
            text = ocr_fullpage(image)
        else:
            ocr_results = ocr_regions(image, detections)

            # Check if YOLO missed the top of the page
            h = image.shape[0]
            first_y = detections[0]["bbox"][1]
            if first_y > h * 0.15:
                top_region = image[0:first_y, :]
                from core.ocr import preprocess
                import pytesseract
                top_text = pytesseract.image_to_string(
                    preprocess(top_region), lang=config.OCR_LANG
                ).strip()
                if top_text:
                    ocr_results = [r for r in ocr_results if r["bbox"][1] >= first_y]
                    ocr_results.insert(0, {
                        "bbox": (0, 0, image.shape[1], first_y),
                        "class": "fallback_top",
                        "text": top_text,
                    })

            text = "\n\n".join(r["text"] for r in ocr_results)

        # Step 3: Save extracted text to file
        text_path = os.path.join(config.TEXT_DIR, f"{doc_id}_page{page_num}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Step 4: Generate audio from text
        audio_path = os.path.join(config.AUDIO_DIR, f"{doc_id}_page{page_num}.wav")
        if text.strip():
            generate_audio(text, audio_path)
        else:
            audio_path = ""

        return {
            "page": page_num,
            "text": text,
            "audio_path": audio_path,
        }

    def process_document(self, pdf_path, progress_callback=None):
        """Process an entire PDF file, page by page. Skips pages already cached."""

        doc_id = self._make_doc_id(pdf_path)
        images = pdf_to_images(pdf_path)
        total = len(images)

        results = []
        for i, img in enumerate(images):
            page_num = i + 1

            if progress_callback:
                progress_callback(page_num, total)

            # Check if this page was already processed
            text_path = os.path.join(config.TEXT_DIR, f"{doc_id}_page{page_num}.txt")
            audio_path = os.path.join(config.AUDIO_DIR, f"{doc_id}_page{page_num}.wav")

            if os.path.exists(text_path) and os.path.exists(audio_path):
                with open(text_path, "r", encoding="utf-8") as f:
                    text = f.read()
                results.append({
                    "page": page_num,
                    "text": text,
                    "audio_path": audio_path,
                })
                continue

            result = self.process_page(img, page_num, doc_id)
            results.append(result)

        self._save_to_library(pdf_path, doc_id, total)
        return results
    
    def _make_doc_id(self, pdf_path):
        name = os.path.splitext(os.path.basename(pdf_path))[0]
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)

    # --- Library functions (saves reading progress) ---

    def _load_library(self):
        if os.path.exists(config.LIBRARY_JSON):
            with open(config.LIBRARY_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_library(self, library):
        with open(config.LIBRARY_JSON, "w", encoding="utf-8") as f:
            json.dump(library, f, indent=2)

    def _save_to_library(self, pdf_path, doc_id, total_pages):
        library = self._load_library()
        library[doc_id] = {
            "path": os.path.abspath(pdf_path),
            "filename": os.path.basename(pdf_path),
            "total_pages": total_pages,
            "last_page": 1,
            "last_opened": datetime.now().isoformat(),
        }
        self._save_library(library)

    def get_library(self):
        return self._load_library()

    def update_progress(self, doc_id, page_num):
        library = self._load_library()
        if doc_id in library:
            library[doc_id]["last_page"] = page_num
            library[doc_id]["last_opened"] = datetime.now().isoformat()
            self._save_library(library)