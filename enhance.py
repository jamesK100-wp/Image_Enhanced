"""Conservative, resumable photo exports. Originals are never modified."""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

VERSION = 1
SIZES = {"card": (960, 540), "cover": (1920, 1080), "master": (3840, 2160)}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

def process(source, destination, crop=False, master=False, brightness=1.03):
    with Image.open(source) as opened:
        im = ImageOps.exif_transpose(opened).convert("RGB")
        # Normalize embedded color profiles to sRGB when available.
        if opened.info.get("icc_profile"):
            import io
            from PIL import ImageCms
            im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(opened.info["icc_profile"])), ImageCms.createProfile("sRGB"), outputMode="RGB")
        original_size = im.size
        im = ImageEnhance.Brightness(im).enhance(brightness)
        im = ImageEnhance.Contrast(im).enhance(1.02)
        im = im.filter(ImageFilter.UnsharpMask(radius=1, percent=35, threshold=3))
        outputs = []
        for name, size in SIZES.items():
            if name == "master" and not master:
                continue
            # Contain preserves all content; crop is an explicit opt-in.
            out = ImageOps.fit(im, size, method=Image.Resampling.LANCZOS) if crop else ImageOps.contain(im, size, method=Image.Resampling.LANCZOS)
            path = destination / (name + (".jpg" if name == "master" else ".webp"))
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            out.save(temporary, format="JPEG" if name == "master" else "WEBP", quality=92 if name == "master" else 85)
            temporary.replace(path)
            outputs.append(str(path))
        return {"source_size": original_size, "outputs": outputs, "review": "Check crop and exposure. People/animals are unchanged. Upscaling does not recover missing detail."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--crop", action="store_true", help="Opt into a centered 16:9 crop; review important edges.")
    p.add_argument("--master", action="store_true", help="Also export a 4K-sized JPEG (exact 3840x2160 requires --crop).")
    p.add_argument("--brightness", type=float, default=1.03)
    p.add_argument("--limit", type=int, help="Process a small pilot batch first.")
    args = p.parse_args()
    src, dst = args.input.resolve(), args.output.resolve()
    if not src.is_dir():
        p.error("Input must be an existing folder.")
    if src == dst or src in dst.parents or dst in src.parents:
        p.error("Input and output must be separate, non-nested folders.")
    if not 0.5 <= args.brightness <= 1.5 or (args.limit is not None and args.limit < 1):
        p.error("Brightness must be 0.5–1.5 and limit must be positive.")
    dst.mkdir(parents=True, exist_ok=True)
    config = json.dumps([VERSION, args.crop, args.master, args.brightness])
    db = sqlite3.connect(dst / "progress.sqlite3")
    db.execute("CREATE TABLE IF NOT EXISTS jobs (source TEXT PRIMARY KEY, signature TEXT, result TEXT)")
    files = sorted(f for f in src.rglob("*") if f.is_file() and f.suffix.lower() in EXTENSIONS)
    if args.limit:
        files = files[:args.limit]
    failures = 0
    with (dst / "report.jsonl").open("a", encoding="utf-8") as report:
        for index, path in enumerate(files, 1):
            try:
                digest = hashlib.sha256(config.encode())
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                signature = digest.hexdigest()
                row = db.execute("SELECT signature,result FROM jobs WHERE source=?", (str(path),)).fetchone()
                if row and row[0] == signature and all(Path(x).exists() for x in json.loads(row[1])["outputs"]):
                    print(f"[{index}/{len(files)}] Skipped: {path.name}")
                    continue
                result = process(path, dst / path.relative_to(src), args.crop, args.master, args.brightness)
                db.execute("INSERT OR REPLACE INTO jobs VALUES (?,?,?)", (str(path), signature, json.dumps(result)))
                db.commit()
                report.write(json.dumps({"source": str(path), "status": "done", **result}) + "\n")
                print(f"[{index}/{len(files)}] Done: {path.name}")
            except Exception as error:
                failures += 1
                report.write(json.dumps({"source": str(path), "status": "error", "error": str(error)}) + "\n")
                print(f"[{index}/{len(files)}] ERROR: {path.name}: {error}")
            report.flush()
    db.close()
    print(f"Finished: {len(files)} files considered; {failures} failed. Report: {dst / 'report.jsonl'}")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
