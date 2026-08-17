"""One-off utility: convert a white-background JPG into a transparent PNG.

Usage: python scripts/make_transparent.py <input.jpg> <output.png> [threshold]
"""
import sys
from PIL import Image


def remove_white_background(src_path: str, dst_path: str, threshold: int = 245) -> None:
    img = Image.open(src_path).convert("RGBA")
    pixels = img.getdata()

    new_pixels = []
    for r, g, b, a in pixels:
        if r >= threshold and g >= threshold and b >= threshold:
            new_pixels.append((r, g, b, 0))
        else:
            new_pixels.append((r, g, b, a))

    img.putdata(new_pixels)
    img.save(dst_path, "PNG")


if __name__ == "__main__":
    src = sys.argv[1]
    dst = sys.argv[2]
    thresh = int(sys.argv[3]) if len(sys.argv) > 3 else 245
    remove_white_background(src, dst, thresh)
    print(f"Saved {dst}")
