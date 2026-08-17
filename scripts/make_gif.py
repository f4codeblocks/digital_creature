"""Slice a multi-pose reference sheet (equal-width frames on a white background)
into an animated preview GIF.

Usage: python scripts/make_gif.py <sheet.jpg> <n_frames> <out.gif> [duration_ms] [--ping-pong]
"""
import sys

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


def trim_and_align(frames: list[Image.Image], padding: int = 12) -> list[Image.Image]:
    bboxes = []
    for frame in frames:
        gray = frame.convert("L")
        mask = gray.point(lambda p: 255 if p < 245 else 0)
        bboxes.append(mask.getbbox() or (0, 0, frame.width, frame.height))

    max_w = max(b[2] - b[0] for b in bboxes) + padding * 2
    max_h = max(b[3] - b[1] for b in bboxes) + padding * 2

    aligned = []
    for frame, bbox in zip(frames, bboxes):
        cropped = frame.crop(bbox)
        canvas = Image.new("RGB", (max_w, max_h), (255, 255, 255))
        offset_x = (max_w - cropped.width) // 2
        offset_y = max_h - padding - cropped.height
        canvas.paste(cropped, (offset_x, offset_y))
        aligned.append(canvas)
    return aligned


def make_gif(sheet_path: str, n_frames: int, out_path: str, duration_ms: int = 150, ping_pong: bool = False) -> None:
    frames = trim_and_align(slice_frames(sheet_path, n_frames))
    if ping_pong and len(frames) > 2:
        frames = frames + frames[-2:0:-1]

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
    )
    print(f"Saved {out_path} ({len(frames)} frames, {duration_ms}ms each)")


if __name__ == "__main__":
    sheet = sys.argv[1]
    n = int(sys.argv[2])
    out = sys.argv[3]
    duration = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 150
    ping_pong = "--ping-pong" in sys.argv
    make_gif(sheet, n, out, duration, ping_pong)
