#Audora entry point. Run this file to start.

import sys
import os

# Make sure imports work from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pipeline import AudoraPipeline
from core.player import AudioPlayer

# Used mostly for testing pipleine without GUI
def main():
    # Check if user provided a PDF path
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_pdf>")
        print("Example: python main.py document.pdf")
        return

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        return

    print(f"\n{'='*50}")
    print(f"  AUDORA - Processing: {os.path.basename(pdf_path)}")
    print(f"{'='*50}\n")

    # Start the pipeline
    pipeline = AudoraPipeline()

    def on_progress(page, total):
        print(f"  Processing page {page} of {total}...")

    results = pipeline.process_document(pdf_path, progress_callback=on_progress)

    print(f"\n  Done! {len(results)} pages processed.\n")

    # Ask user if they want to listen
    player = AudioPlayer()
    for r in results:
        if r["audio_path"]:
            ans = input(f"  Play page {r['page']}? (y/n/q to quit): ").strip().lower()
            if ans == "q":
                break
            if ans == "y":
                player.play(r["audio_path"])
                input("  Press Enter for next page...")
                player.stop()

# With args = CLI mode, no args = GUI mode 
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        from ui.app import launch_app
        launch_app()