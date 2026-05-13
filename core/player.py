# Handles audio playback with pause/resume

import os
import time
import threading
import sounddevice as sd
import soundfile as sf


class AudioPlayer:

    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self._data = None
        self._samplerate = None
        self._frame = 0
        self._current_file = None
        self._thread = None
        self._start_time = 0

    def play(self, audio_path):
        """Play or resume audio."""
        if not audio_path or not os.path.exists(audio_path):
            return False

        if self.is_paused and self._current_file == audio_path:
            self.is_paused = False
            self.is_playing = True
            self._play_from_frame()
            return True

        self.stop()
        self._current_file = audio_path
        self._data, self._samplerate = sf.read(audio_path)
        self._frame = 0
        self.is_playing = True
        self._play_from_frame()
        return True

    def _play_from_frame(self):
        """Play from current frame position."""
        def _worker():
            remaining = self._data[self._frame:]
            self._start_time = time.time()
            try:
                sd.play(remaining, self._samplerate)
                sd.wait()
                if not self.is_paused:
                    self.is_playing = False
                    self._frame = 0
            except Exception:
                self.is_playing = False

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def pause(self):
        """Pause and save position."""
        if self.is_playing:
            elapsed = time.time() - self._start_time
            frames_played = int(elapsed * self._samplerate)
            self._frame = self._frame + frames_played
            if self._frame >= len(self._data):
                self._frame = 0
            sd.stop()
            self.is_paused = True
            self.is_playing = False

    def stop(self):
        """Stop and reset."""
        sd.stop()
        self.is_playing = False
        self.is_paused = False
        self._frame = 0
        self._current_file = None

    def is_busy(self):
        return self.is_playing