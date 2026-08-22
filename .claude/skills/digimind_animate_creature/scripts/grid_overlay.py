"""Overlay a labeled coordinate grid on a source image so its pixel
coordinates can be read visually. Use this first, on the raw pose sheet, to
find where each pose/frame column starts and ends, and to spot any labels,
arrows, or pose numbers between frames that will need to be erased before
background removal.

Usage: python grid_overlay.py <source.jpg> <out_grid.png> [step_px]
"""
import sys

from PIL import Image, ImageDraw


def make_grid(src_path: str, out_path: str, step: int = 50) -> None:
    img = Image.open(src_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=(0, 150, 255), width=1)
        draw.text((x + 2, 2), str(x), fill=(0, 120, 255))
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=(0, 150, 255), width=1)
        draw.text((2, y + 2), str(y), fill=(0, 120, 255))
    img.save(out_path)
    print(f"Saved {out_path} ({w}x{h}, grid every {step}px)")


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    make_grid(src, out, step)
