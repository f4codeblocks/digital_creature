"""Turn a character reference-sheet image (illustration + surrounding card
decorations on a white/patterned background) into a clean transparent PNG
of just the character.

Background removal uses connected-component flood fill instead of a flat
per-pixel threshold, because character art usually contains near-white
highlight details (glow lines, eye whites, claw highlights) that must
survive, while the decorative background must not. A flat threshold can't
tell those apart; connectivity to the image border can.

Usage: python clean_character.py <spec.json>

spec.json fields:
  source           path to the source image (required)
  output           path to write the final transparent PNG (required)
  erase_boxes      list of [x0,y0,x1,y1] rectangles (in SOURCE image pixel
                    coordinates) to paint solid white before anything else.
                    Use grid_overlay.py on the source image first to read
                    off these coordinates for the title/logo/text boxes/
                    icons/bottom card -- anything that isn't the character.
                    Leave generous margin around the character's silhouette,
                    especially outstretched limbs/tails that reach toward
                    the side text boxes.
  crop             [x0,y0,x1,y1] bounding box (source coordinates) around
                    the character, generous padding is fine -- the result
                    gets auto-trimmed to content afterwards.
  strict_threshold  optional [r,g,b] minimums for the first background pass
                    (default [205,195,195]). Pixels at/above all three are
                    candidate background.
  loose_threshold   optional [r,g,b] minimums for a second, looser pass
                    that catches soft shadows/gradients the strict pass
                    misses (default [190,130,130]).
  gap_min_size      enclosed (non-border-touching) components at/above this
                    pixel count are treated as background gaps in the
                    silhouette -- e.g. the space between legs (default 3000)
  gap_fill_size     enclosed components at/above this size AND with fill
                    ratio (size / bbox area) above gap_fill_ratio are also
                    treated as gaps -- catches smaller gaps like under an
                    arm without eating thin/sparse highlight lines
                    (default 1000)
  gap_fill_ratio    see above (default 0.3)
  pad               padding in px kept around the trimmed alpha bbox
                    (default 8)

Always sanity-check the output: this script also writes
"<output>.check.png" with the result composited on solid green, since
transparent regions are easy to miss when eyeballing on a white canvas.
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def clean_character(spec: dict) -> str:
    img = Image.open(spec["source"]).convert("RGB")

    for box in spec.get("erase_boxes", []):
        img.paste((255, 255, 255), tuple(box))

    x0, y0, x1, y1 = spec["crop"]
    crop = img.crop((x0, y0, x1, y1))
    arr = np.array(crop)
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)

    st = spec.get("strict_threshold", [205, 195, 195])
    lt = spec.get("loose_threshold", [190, 130, 130])
    gap_min_size = spec.get("gap_min_size", 3000)
    gap_fill_size = spec.get("gap_fill_size", 1000)
    gap_fill_ratio = spec.get("gap_fill_ratio", 0.3)
    pad = spec.get("pad", 8)

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

    rgba = crop.convert("RGBA")
    data = np.array(rgba)
    data[bg_mask, 3] = 0
    out = Image.fromarray(data, "RGBA")

    bbox = out.split()[3].getbbox()
    if bbox:
        l = max(0, bbox[0] - pad)
        t = max(0, bbox[1] - pad)
        rr = min(out.width, bbox[2] + pad)
        bb = min(out.height, bbox[3] + pad)
        out = out.crop((l, t, rr, bb))

    out.save(spec["output"])

    check_path = spec["output"] + ".check.png"
    green_bg = Image.new("RGB", out.size, (0, 255, 0))
    green_bg.paste(out, (0, 0), out)
    green_bg.save(check_path)

    return spec["output"]


if __name__ == "__main__":
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        spec = json.load(f)
    output = clean_character(spec)
    print(f"Saved {output}")
    print(f"Saved {output}.check.png (composited on green -- inspect this to confirm transparency)")
