## app.py - Audora GUI using tkinter

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.pipeline import AudoraPipeline
from core.player import AudioPlayer


class AudoraApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Audora - Offline Screen Reader")
        self.root.geometry("850x650")
        self.root.configure(bg="#1e1e2e")

        self.pipeline = AudoraPipeline()
        self.player = AudioPlayer()

        self.current_results = []
        self.current_page = 0
        self.current_doc_id = ""
        self.is_processing = False

        self._build_ui()
        self._show_library()

    def _build_ui(self):
        bg = "#1e1e2e"
        fg = "#cdd6f4"
        accent = "#89b4fa"
        btn_bg = "#313244"

        # Main layout: sidebar + content
        main_frame = tk.Frame(self.root, bg=bg)
        main_frame.pack(fill="both", expand=True)

        # --- Sidebar (Library) ---
        sidebar = tk.Frame(main_frame, bg="#181825", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Library", font=("Segoe UI", 13, "bold"),
                 bg="#181825", fg=accent, pady=10).pack(fill="x")

        self.library_frame = tk.Frame(sidebar, bg="#181825")
        self.library_frame.pack(fill="both", expand=True, padx=5)

        tk.Label(sidebar, text="Tip: Right-click to delete",
                 bg="#181825", fg="#6c7086",
                 font=("Segoe UI", 8)).pack(side="bottom", pady=(0, 5))

        tk.Button(sidebar, text="+ Open PDF", command=self._open_file,
                  bg=accent, fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=8).pack(fill="x", padx=10, pady=10)

        # --- Content area ---
        content = tk.Frame(main_frame, bg=bg)
        content.pack(side="right", fill="both", expand=True)

        # Top bar
        top = tk.Frame(content, bg=bg, pady=10)
        top.pack(fill="x", padx=20)

        tk.Label(top, text="AUDORA", font=("Segoe UI", 18, "bold"),
                 bg=bg, fg=accent).pack(side="left")

        # Status label
        self.status_var = tk.StringVar(value="Open a PDF to begin")
        tk.Label(content, textvariable=self.status_var,
                 bg=bg, fg=fg, font=("Segoe UI", 10)).pack(pady=5)

        # Text display
        text_frame = tk.Frame(content, bg=bg)
        text_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.text_display = tk.Text(text_frame, wrap="word", bg="#313244", fg=fg,
                                     font=("Consolas", 11), relief="flat",
                                     padx=10, pady=10)
        self.text_display.pack(fill="both", expand=True)
        self.text_display.insert("1.0", "Extracted text will appear here...")
        self.text_display.config(state="disabled")

        # Playback controls
        controls = tk.Frame(content, bg=bg, pady=15)
        controls.pack(fill="x")

        btn_style = {"bg": btn_bg, "fg": fg, "font": ("Segoe UI", 12),
                     "relief": "flat", "width": 6, "pady": 5}

        tk.Button(controls, text="Prev", command=self._prev_page,
                  **btn_style).pack(side="left", padx=10, expand=True)

        self.btn_play = tk.Button(controls, text="Play", command=self._toggle_play,
                                   bg=accent, fg="#1e1e2e",
                                   font=("Segoe UI", 13, "bold"), relief="flat",
                                   width=8, pady=5)
        self.btn_play.pack(side="left", padx=10, expand=True)

        tk.Button(controls, text="Next", command=self._next_page,
                  **btn_style).pack(side="left", padx=10, expand=True)

        # Page indicator
        self.page_var = tk.StringVar(value="")
        tk.Label(content, textvariable=self.page_var,
                 bg=bg, fg=fg, font=("Segoe UI", 10)).pack(pady=(0, 10))

    # --- Library ---

    def _show_library(self):
        """Display saved PDFs in the sidebar."""
        for widget in self.library_frame.winfo_children():
            widget.destroy()

        library = self.pipeline.get_library()

        if not library:
            tk.Label(self.library_frame, text="No documents yet",
                     bg="#181825", fg="#6c7086",
                     font=("Segoe UI", 9)).pack(pady=20)
            return

        sorted_docs = sorted(library.items(),
                             key=lambda x: x[1].get("last_opened", ""),
                             reverse=True)

        for doc_id, info in sorted_docs:
            filename = info.get("filename", doc_id)
            pages = info.get("total_pages", "?")
            last_page = info.get("last_page", 1)

            item = tk.Frame(self.library_frame, bg="#313244", pady=5, padx=8)
            item.pack(fill="x", pady=2)

            tk.Label(item, text=filename, bg="#313244", fg="#cdd6f4",
                     font=("Segoe UI", 9, "bold"),
                     anchor="w").pack(fill="x")

            tk.Label(item, text=f"{pages} pages | Last: p.{last_page}",
                     bg="#313244", fg="#6c7086",
                     font=("Segoe UI", 8), anchor="w").pack(fill="x")

            # Left click to open
            path = info.get("path", "")
            item.bind("<Button-1>", lambda e, p=path: self._process_file(p))
            for child in item.winfo_children():
                child.bind("<Button-1>", lambda e, p=path: self._process_file(p))

            # Right click to delete
            item.bind("<Button-3>", lambda e, d=doc_id, f=filename: self._delete_cache(d, f))
            for child in item.winfo_children():
                child.bind("<Button-3>", lambda e, d=doc_id, f=filename: self._delete_cache(d, f))

# --- For right-clicking menu on library items ---

    def _delete_cache(self, doc_id, filename):
        """Right-click to delete cached files for a document."""
        confirm = tk.messagebox.askyesno(
            "Delete Cache",
            f"Delete all cached data for {filename}?"
        )
        if not confirm:
            return

        # Delete text files
        for f in os.listdir(config.TEXT_DIR):
            if f.startswith(doc_id):
                os.remove(os.path.join(config.TEXT_DIR, f))

        # Delete audio files
        for f in os.listdir(config.AUDIO_DIR):
            if f.startswith(doc_id):
                os.remove(os.path.join(config.AUDIO_DIR, f))

        # Remove from library
        library = self.pipeline.get_library()
        if doc_id in library:
            del library[doc_id]
            self.pipeline._save_library(library)

        self._show_library()
        self.status_var.set(f"Deleted cache for {filename}")

    # --- File handling ---

    def _open_file(self):
        if self.is_processing:
            return
        path = filedialog.askopenfilename(
            title="Select a PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        if path:
            self._process_file(path)

    def _process_file(self, pdf_path):
        if self.is_processing:
            return
        if not os.path.exists(pdf_path):
            self.status_var.set("Error: file not found")
            return

        self.is_processing = True
        self.status_var.set(f"Processing: {os.path.basename(pdf_path)}...")

        def worker():
            try:
                results = self.pipeline.process_document(
                    pdf_path, progress_callback=self._on_progress
                )
                self.current_results = results
                self.current_doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
                self.current_doc_id = "".join(
                    c if c.isalnum() or c in "-_" else "_" for c in self.current_doc_id
                )
                self.current_page = 0

                # Check saved progress
                library = self.pipeline.get_library()
                if self.current_doc_id in library:
                    saved = library[self.current_doc_id].get("last_page", 1)
                    self.current_page = min(saved - 1, len(results) - 1)

                self.root.after(0, self._on_done)
            except Exception as e:
                self.root.after(0, lambda err=str(e): self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_progress(self, page, total):
        self.root.after(0, lambda: self.status_var.set(f"Page {page} of {total}..."))

    def _on_done(self):
        self.is_processing = False
        self._show_page(self.current_page)
        self._show_library()
        self.status_var.set("Ready - press Play to listen")

    def _on_error(self, msg):
        self.is_processing = False
        self.status_var.set(f"Error: {msg}")

    # --- Page display ---

    def _show_page(self, index):
        if not self.current_results:
            return
        index = max(0, min(index, len(self.current_results) - 1))
        self.current_page = index
        result = self.current_results[index]

        self.text_display.config(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("1.0", result["text"] or "(No text extracted)")
        self.text_display.config(state="disabled")

        total = len(self.current_results)
        self.page_var.set(f"Page {index + 1} / {total}")

        self.pipeline.update_progress(self.current_doc_id, index + 1)

    # --- Playback ---

    def _toggle_play(self):
        if not self.current_results:
            return
        if self.player.is_playing:
            self.player.pause()
            self.btn_play.config(text="Play")
        else:
            audio = self.current_results[self.current_page].get("audio_path", "")
            if audio and self.player.play(audio):
                self.btn_play.config(text="Pause")

    def _stop(self):
        self.player.stop()
        self.btn_play.config(text="Play")

    def _next_page(self):
        if self.current_page < len(self.current_results) - 1:
            self._show_page(self.current_page + 1)

    def _prev_page(self):
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.player.stop()
        self.root.destroy()


def launch_app():
    app = AudoraApp()
    app.run()