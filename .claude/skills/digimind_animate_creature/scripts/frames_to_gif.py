"""Assemble a folder of already-transparent, aligned PNG frames (the output
of slice_sheet_frames.py, or an existing assets/<character>/<state>/
folder) into a GIF -- either a --check GIF composited on solid green to
sanity-check transparency (a leftover pale background patch is invisible
composited on white, but glaring on green), or a real transparent preview
GIF for sharing outside the app.

Usage: python frames_to_gif.py <frames_glob> <out.gif> [duration_ms] [--ping-pong] [--check]

<frames_glob> is a directory (all *.png inside, sorted) or an explicit glob
pattern like "assets/curimon/walk/walk_*.png".
"""
import glob
import sys
from pathlib import Path

from PIL import Image


def load_frames(frames_glob: str) -> list:
    p = Path(frames_glob)
    paths = sorted(p.glob("*.png")) if p.is_dir() else sorted(Path(f) for f in glob.glob(frames_glob))
    if not paths:
        raise FileNotFoundError(f"No PNG frames matched {frames_glob!r}")
    return [Image.open(path).convert("RGBA") for path in paths]


def composite_on_green(frames: list) -> list:
    out = []
    for frame in frames:
        bg = Image.new("RGB", frame.size, (0, 255, 0))
        bg.paste(frame, (0, 0), frame)
        out.append(bg)
    return out


def make_gif(frames_glob: str, out_path: str, duration_ms: int = 150, ping_pong: bool = False, check: bool = False) -> None:
    frames = load_frames(frames_glob)
    if ping_pong and len(frames) > 2:
        frames = frames + frames[-2:0:-1]

    if check:
        frames = composite_on_green(frames)
        frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=duration_ms, loop=0)
    else:
        frames[0].save(
            out_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration_ms,
            loop=0,
            disposal=2,
            transparency=0,
        )
    print(f"Saved {out_path} ({len(frames)} frames, {duration_ms}ms each{', check mode' if check else ''})")


if __name__ == "__main__":
    frames_glob = sys.argv[1]
    out = sys.argv[2]
    rest = sys.argv[3:]
    positional = [a for a in rest if not a.startswith("--")]
    duration = int(positional[0]) if positional and positional[0].isdigit() else 150
    make_gif(frames_glob, out, duration, ping_pong="--ping-pong" in rest, check="--check" in rest)
