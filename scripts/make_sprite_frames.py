"""Slice a multi-pose reference sheet (equal-width frames on a white background)
into transparent, aligned PNG sprite frames ready for real frame animation.

Usage: python scripts/make_sprite_frames.py <sheet.jpg> <n_frames> <out_dir> <prefix> [white_threshold]
"""
import sys
from pathlib import Path

from PIL import Image


def slice_frames(sheet_path: str, n_frames: int) -> list[Image.Image]:
    img = Image.open(sheet_path).convert("RGB")
    w, h = img.size
    col_w = w // n_frames
    frames = []
    for i in range(n_frames):
        left = i * col_w
        right = w if i == n_frames - 1 else (i + 1) * col_w
        frames.append(img.crop((left, 0, right, h)))
    return frames


def remove_white(img_rgb: Image.Image, threshold: int = 240) -> Image.Image:
    rgba = img_rgb.convert("RGBA")
    pixels = rgba.getdata()
    new_pixels = [
        (r, g, b, 0) if (r >= threshold and g >= threshold and b >= threshold) else (r, g, b, a)
        for r, g, b, a in pixels
    ]
    rgba.putdata(new_pixels)
    return rgba


def trim_and_align(frames_rgba: list[Image.Image], padding: int = 10) -> list[Image.Image]:
    bboxes = [f.split()[3].getbbox() or (0, 0, f.width, f.height) for f in frames_rgba]
    max_w = max(b[2] - b[0] for b in bboxes) + padding * 2
    max_h = max(b[3] - b[1] for b in bboxes) + padding * 2

    aligned = []
    for frame, bbox in zip(frames_rgba, bboxes):
        cropped = frame.crop(bbox)
        canvas = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
        offset_x = (max_w - cropped.width) // 2
        offset_y = max_h - padding - cropped.height
        canvas.paste(cropped, (offset_x, offset_y), cropped)
        aligned.append(canvas)
    return aligned


def main() -> None:
    sheet_path, n_frames, out_dir, prefix = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    threshold = int(sys.argv[5]) if len(sys.argv) > 5 else 240

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    frames = [remove_white(f, threshold) for f in slice_frames(sheet_path, n_frames)]
    frames = trim_and_align(frames)

    for i, frame in enumerate(frames, start=1):
        dest = out_path / f"{prefix}_{i:02d}.png"
        frame.save(dest, "PNG")
        print(f"Saved {dest}")


if __name__ == "__main__":
    main()
