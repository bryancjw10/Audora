import os

# Adjust all parameters here #
# Retrain YOLO or change voice, update values here #

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
TEXT_DIR = os.path.join(OUTPUT_DIR, "text")
LIBRARY_DIR = os.path.join(BASE_DIR, "library")
LIBRARY_JSON = os.path.join(LIBRARY_DIR, "library.json")

# YOLO
YOLO_MODEL_PATH = os.path.join(MODELS_DIR, "yolov11", "best.pt")
YOLO_CONFIDENCE = 0.30 # 0.25 leaks figures, 0.5 misses some paragaphs #
YOLO_IOU = 0.50
YOLO_IMG_SIZE = 640
TEXT_CLASSES = {"paragraph", "title"} # Removed "header" & "footer" so YOLO skips watermarks.

# Tesseract - install path
TESSERACT_CMD = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
OCR_LANG = "eng"
OCR_MIN_CONFIDENCE = 40

# TTS
TTS_ENGINE = "pyttsx3"
PYTTSX3_RATE = 170 # TTS speed

# Create folders if they don't exist
for _d in [MODELS_DIR, AUDIO_DIR, TEXT_DIR, LIBRARY_DIR]:
    os.makedirs(_d, exist_ok=True)