# Converts extracted text into speech audio
# Supports Piper TTS (natural) and pyttsx3 (fallback)

import os
import subprocess
import config


def generate_audio(text, output_path):
    """Convert text to speech and save as .wav file."""
    if not text.strip():
        return ""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Try Piper first, fall back to pyttsx3
    piper_exe = os.path.join(config.MODELS_DIR, "piper", "piper.exe")
    piper_voice = os.path.join(config.MODELS_DIR, "piper", "en_US-amy-medium.onnx")

    if os.path.exists(piper_exe) and os.path.exists(piper_voice):
        return _generate_piper(text, output_path, piper_exe, piper_voice)
    else:
        return _generate_pyttsx3(text, output_path)


def _generate_piper(text, output_path, piper_exe, piper_voice):
    """Generate speech using Piper TTS (natural sounding, offline)."""
    try:
        proc = subprocess.run(
            [piper_exe, "--model", piper_voice, "--output_file", output_path],
            input=text,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            return output_path
        else:
            print(f"Piper error: {proc.stderr}")
            return _generate_pyttsx3(text, output_path)
    except Exception as e:
        print(f"Piper failed: {e}, falling back to pyttsx3")
        return _generate_pyttsx3(text, output_path)


def _generate_pyttsx3(text, output_path):
    """Fallback: generate speech using pyttsx3 (robotic but reliable)."""
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", config.PYTTSX3_RATE)
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    return output_path