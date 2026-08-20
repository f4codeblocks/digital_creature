"""Slice a multi-pose reference sheet (one row of poses for a single
animation state -- e.g. a walk cycle or a talk cycle) into numbered,
background-removed, aligned PNG frames ready to drop into
assets/<character>/<state>/, exactly like Cognimon's idle/walk/thinking/
talking frames were built.

This is a superset of the project's scripts/make_sprite_frames.py: same
default behavior (equal-width columns, flat white threshold) for clean
sheets, plus a "floodfill" mode for messier sheets -- textured/patterned
paper, scanned line art, or sheets with pose labels/arrows/numbers between
frames -- reusing the border-connected flood fill from
digimind_test_creature's clean_character.py so near-white highlights on the
character (glow lines, eye whites) survive while the actual background does
not -- plus a "components" mode for sheets where poses aren't in neat
columns at all: action poses with effects (beams, speed lines, portals)
that visually reach past where a column cut would land, so a column-based
crop (even a hand-picked frame_boxes one) slices the effect in half and
leaves a disconnected fragment glued to the wrong frame.

Usage: python slice_sheet_frames.py <spec.json>

spec.json fields:
  source        path to the source sheet image (required)
  out_dir       directory to write numbered frames into, e.g.
                "assets/curimon/walk" (required)
  prefix        filename prefix, e.g. "walk" -> walk_01.png, walk_02.png...
                (required)
  n_frames      number of equal-width columns to slice the sheet into
                (column modes), or the number of poses to detect
                (components mode). Required unless frame_boxes is given.
  frame_boxes   optional list of [x0,y0,x1,y1] boxes (source coordinates),
                one per frame, for sheets where poses aren't evenly spaced
                but ARE still cleanly separable by a vertical cut. Overrides
                n_frames. Use grid_overlay.py to read these off. Ignored in
                components mode.
  erase_boxes   optional list of [x0,y0,x1,y1] boxes (source coordinates)
                painted solid white BEFORE slicing -- use for labels,
                arrows, pose numbers, or a title sitting between/above the
                poses that isn't part of any character frame.
  mode          "simple" (default), "floodfill", or "components".
                simple: flat per-pixel white-ish threshold, same as
                  make_sprite_frames.py. Fast, and correct whenever the
                  sheet background is actually clean white/near-white AND
                  no pose's effects reach past its column boundary.
                floodfill: border-connected flood fill per frame, same
                  algorithm as clean_character.py. Use when the background
                  has texture, soft shadows, or the character has near-
                  white highlight details that a flat threshold would eat.
                components: ignores column position entirely. Labels every
                  non-white connected blob, takes the n_frames largest as
                  the main poses (sorted left-to-right), and assigns every
                  smaller blob (a beam, a spark, a speed line, a shadow) to
                  whichever main pose's center it's closest to. Each frame
                  then keeps only its own assigned blobs -- everything else
                  painted transparent -- so an effect that visually
                  overlaps a neighboring pose's column still lands whole in
                  the right frame. Use this whenever grid_overlay.py shows
                  poses that aren't in neat, evenly-inked columns (uneven
                  spacing, motion lines/beams trailing toward another pose,
                  one frame dramatically bigger than the others).
  threshold     simple mode only: RGB minimum to treat as background
                (default 240).
  strict_threshold  floodfill mode only: [r,g,b] minimums for the first
                    background pass (default [205,195,195]).
  loose_threshold   floodfill mode only: [r,g,b] minimums for a second,
                    looser pass that catches soft shadows (default
                    [190,130,130]).
  gap_min_size      floodfill mode only: enclosed regions at/above this
                     pixel count are treated as background gaps in the
                     silhouette, e.g. between legs (default 3000).
  gap_fill_size     floodfill mode only: enclosed regions at/above this
                     size AND with fill ratio above gap_fill_ratio are also
                     treated as gaps (default 1000).
  gap_fill_ratio    see above (default 0.3).
  component_threshold  components mode only: RGB minimum to treat as
                        background when labeling blobs (default 235).
  padding       padding in px kept around each frame's trimmed content,
                and (when align is true) around the shared canvas all
                frames are aligned to (default 10).
  align         true (default) or false. true pads every frame onto ONE
                shared canvas size (bottom-aligned, centered horizontally)
                so the character doesn't jump around when frames are
                cycled at runtime -- the right choice for a looping
                ambient state (idle/walk/talking). Set false for a one-shot
                transition where the frames are deliberately very different
                sizes (e.g. a character shrinking into a portal on exit) --
                forcing those onto one shared canvas would make every OTHER
                frame look tiny and empty; with align false each frame is
                just trimmed to its own content + padding.

Always inspect the frames before wiring them in: run frames_to_gif.py with
--check on the resulting out_dir to composite them on solid green, since a
leftover pale background patch is invisible composited on white.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def slice_boxes(img: Image.Image, spec: dict) -> list:
    if "frame_boxes" in spec:
        return [tuple(b) for b in spec["frame_boxes"]]
    n = spec["n_frames"]
    w, h = img.size
    col_w = w // n
    return [(i * col_w, 0, w if i == n - 1 else (i + 1) * col_w, h) for i in range(n)]


def group_by_component(img: Image.Image, spec: dict) -> list:
    """Split img into n_frames RGBA layers by connected-component grouping
    instead of column position -- see the components-mode docstring above."""
    threshold = spec.get("component_threshold", 235)
    n = spec["n_frames"]

    arr = np.array(img)
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    fg = ~((r >= threshold) & (g >= threshold) & (b >= threshold))

    lbl, count = ndimage.label(fg, structure=np.ones((3, 3)))
    sizes = ndimage.sum(fg, lbl, range(1, count + 1))
    objs = ndimage.find_objects(lbl)

    ranked = sorted(range(count), key=lambda i: -sizes[i])
    main_indices = ranked[:n]
    main_indices.sort(key=lambda i: (objs[i][1].start + objs[i][1].stop) / 2)
    main_centers = [(objs[i][1].start + objs[i][1].stop) / 2 for i in main_indices]
    main_labels = [i + 1 for i in main_indices]

    group_of = {}
    for i in range(count):
        this_label = i + 1
        if this_label in main_labels:
            group_of[this_label] = main_labels.index(this_label)
            continue
        cx = (objs[i][1].start + objs[i][1].stop) / 2
        dists = [abs(cx - mc) for mc in main_centers]
        group_of[this_label] = dists.index(min(dists))

    rgba_full = np.array(img.convert("RGBA"))
    frames = []
    for gi in range(len(main_indices)):
        keep_labels = [lb for lb, g in group_of.items() if g == gi]
        mask = np.isin(lbl, keep_labels)
        data = rgba_full.copy()
        data[~mask, 3] = 0
        frames.append(Image.fromarray(data, "RGBA"))
    return frames


def remove_white_simple(frame_rgb: Image.Image, threshold: int) -> Image.Image:
    rgba = frame_rgb.convert("RGBA")
    pixels = rgba.getdata()
    new_pixels = [
        (r, g, b, 0) if (r >= threshold and g >= threshold and b >= threshold) else (r, g, b, a)
        for r, g, b, a in pixels
    ]
    rgba.putdata(new_pixels)
    return rgba


def remove_background_floodfill(frame_rgb: Image.Image, spec: dict) -> Image.Image:
    arr = np.array(frame_rgb)
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)

    st = spec.get("strict_threshold", [205, 195, 195])
    lt = spec.get("loose_threshold", [190, 130, 130])
    gap_min_size = spec.get("gap_min_size", 3000)
    gap_fill_size = spec.get("gap_fill_size", 1000)
    gap_fill_ratio = spec.get("gap_fill_ratio", 0.3)

    strict = (r >= st[0]) & (g >= st[1]) & (b >= st[2])
    lbl1, n1 = ndimage.label(strict)
    border1 = set(lbl1[0, :]) | set(lbl1[-1, :]) | set(lbl1[:, 0]) | set(lbl1[:, -1])
    border1.discard(0)
    bg_border = np.isin(lbl1, list(border1))

    sizes1 = ndimage.sum(strict, lbl1, range(1, n1 + 1))
    objs = ndimage.find_objects(lbl1)
    gap_labels = []
    for i in range(n1):
        lbl = i + 1
        if lbl in border1:
            continue
        size = sizes1[i]
        sl = objs[i]
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        fill = size / (w * h) if w * h else 0
        if size > gap_min_size or (size > gap_fill_size and fill > gap_fill_ratio):
            gap_labels.append(lbl)
    bg_gaps = np.isin(lbl1, gap_labels)

    loose = (r >= lt[0]) & (g >= lt[1]) & (b >= lt[2])
    lbl2, _ = ndimage.label(loose)
    border2 = set(lbl2[0, :]) | set(lbl2[-1, :]) | set(lbl2[:, 0]) | set(lbl2[:, -1])
    border2.discard(0)
    bg_loose = np.isin(lbl2, list(border2))

    bg_mask = bg_border | bg_gaps | bg_loose

    rgba = frame_rgb.convert("RGBA")
    data = np.array(rgba)
    data[bg_mask, 3] = 0
    return Image.fromarray(data, "RGBA")


def trim_and_align(frames_rgba: list, padding: int) -> list:
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


def trim_individually(frames_rgba: list, padding: int) -> list:
    trimmed = []
    for frame in frames_rgba:
        bbox = frame.split()[3].getbbox() or (0, 0, frame.width, frame.height)
        l = max(0, bbox[0] - padding)
        t = max(0, bbox[1] - padding)
        r = min(frame.width, bbox[2] + padding)
        b = min(frame.height, bbox[3] + padding)
        trimmed.append(frame.crop((l, t, r, b)))
    return trimmed


def slice_sheet_frames(spec: dict) -> list:
    img = Image.open(spec["source"]).convert("RGB")

    for box in spec.get("erase_boxes", []):
        img.paste((255, 255, 255), tuple(box))

    mode = spec.get("mode", "simple")
    if mode == "simple":
        threshold = spec.get("threshold", 240)
        boxes = slice_boxes(img, spec)
        raw_frames = [img.crop(box) for box in boxes]
        cleaned = [remove_white_simple(f, threshold) for f in raw_frames]
    elif mode == "floodfill":
        boxes = slice_boxes(img, spec)
        raw_frames = [img.crop(box) for box in boxes]
        cleaned = [remove_background_floodfill(f, spec) for f in raw_frames]
    elif mode == "components":
        cleaned = group_by_component(img, spec)
    else:
        raise ValueError(f"Unknown mode {mode!r}, expected 'simple', 'floodfill', or 'components'")

    padding = spec.get("padding", 10)
    aligned = trim_and_align(cleaned, padding) if spec.get("align", True) else trim_individually(cleaned, padding)

    out_dir = Path(spec["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = spec["prefix"]

    paths = []
    for i, frame in enumerate(aligned, start=1):
        dest = out_dir / f"{prefix}_{i:02d}.png"
        frame.save(dest, "PNG")
        paths.append(dest)
    return paths


if __name__ == "__main__":
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)
    paths = slice_sheet_frames(spec)
    for p in paths:
        print(f"Saved {p}")
