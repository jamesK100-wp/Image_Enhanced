"""Choose photo folders and launch a 50-image pilot in the console."""
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

def main():
    root = tk.Tk()
    root.withdraw()
    source = filedialog.askdirectory(title="Choose original restaurant photo folder")
    if not source:
        return
    output = filedialog.askdirectory(title="Choose separate enhanced-output folder")
    if not output:
        return
    crop = messagebox.askyesno("16:9 crop", "Crop to 16:9? This can cut off objects at the edges. Choose No to preserve the full frame.")
    master = messagebox.askyesno("Master copies", "Also save large JPEG master copies? These use more disk space. Upscaling does not restore missing detail.")
    root.destroy()
    command = [sys.executable, str(Path(__file__).with_name("enhance.py")), source, output, "--limit", "50"]
    if crop:
        command.append("--crop")
    if master:
        command.append("--master")
    print("Starting 50-image pilot. People and animals are unchanged.", flush=True)
    result = subprocess.run(command)
    print("Pilot finished." if result.returncode == 0 else "Please check the errors above.")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
