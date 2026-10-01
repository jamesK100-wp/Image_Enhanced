# Restaurant Image Enhancer

Local batch processor for restaurant website photos. Start with 50 photos before running your full collection. Original files are never overwritten.

## Windows / VS Code setup

On the original setup computer, Python and Pillow are already configured. Double-click **Start Enhancer.cmd** to select input/output folders and run a 50-image pilot. The console shows progress. The launcher does not remove people or animals.

Install Python 3.11 or newer and a complete Git for Windows installation if they are not available. Open `Image_Enhanced.code-workspace` in VS Code, then use its PowerShell terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe enhance.py "D:\RestaurantPhotos" "D:\EnhancedPhotos" --limit 50
```

For explicit centered 16:9 crops and a 4K master:

```powershell
.\.venv\Scripts\python.exe enhance.py "D:\RestaurantPhotos" "D:\EnhancedPhotos" --crop --master --limit 50
```

Remove `--limit 50` after checking the pilot. Repeat the same command to resume. SQLite records source hashes and settings; unchanged successful files with existing outputs are skipped. Subfolder structure and original filename are retained as output directories, preventing collisions. Do not run multiple processes against the same output directory.

## What works

- EXIF orientation, embedded-profile conversion to sRGB, gentle brightness/contrast and sharpening.
- WebP card and cover exports; optional high-quality JPEG master.
- Original aspect ratio by default; explicit center crop when requested.
- Per-image errors, an append-only JSONL report, and resumable processing.

## Important limits

This starter does **not** detect/remove people or animals, perform AI restoration, or recover lost detail. Those features need a separately selected local model or paid API. Ordinary resizing is not AI super-resolution. Check cropped edges, signs, and exposure manually. Unsupported formats such as HEIC and RAW need conversion first. Outputs omit original EXIF metadata. Keep the original archive.

## GitHub connection

The local `origin` is configured as `https://github.com/jamesK100-wp/Image_Enhanced.git`. The installed Git for Windows successfully contacted the remote and verified it had no existing branches during setup. Photos, generated output, secrets and virtual environments should stay outside Git; `.gitignore` provides defaults for `input/` and `processed/`.
