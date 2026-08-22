---
name: digimind_animate_creature
description: Turns a multi-pose reference sheet (a JPG/PNG with the same character drawn several times in a row -- a walk cycle, a talk cycle, an idle breathing loop, a thinking pose sequence, etc.) into a numbered set of transparent, aligned sprite-frame PNGs under assets/<character>/<state>/, plus a preview/QA GIF, exactly the way Cognimon's idle/walk/thinking/talking animations were built (see character/cognimon.py, character/animation.py, assets/cognimon/, images/cognimon/gifs/). Use this whenever the user provides an image containing several views/poses of a character and asks to turn it into an animation, a walk/talk/idle/thinking cycle, sprite frames, or a GIF -- even if they don't name this skill directly. Covers both clean white-background sheets (fast path) and messier sheets with texture, shadows, or labels/arrows between poses (floodfill path, reusing digimind_test_creature's background-removal approach). Does not cover single-image background cleanup with no animation involved -- that's digimind_test_creature.
---

# Digimind animate creature

Turn a reference sheet of a character in several poses into a real sprite-frame animation, following the exact recipe used to build Cognimon's `idle`, `walk`, `thinking`, and `talking` states.

## How Cognimon's animations actually work (read this first)

- Each state has a folder of numbered transparent PNGs: `assets/cognimon/<state>/<state>_01.png`, `_02.png`, ... (see `assets/cognimon/idle/`, `walk/`, `thinking/`, `talking/`).
- `ui/desktop.py`'s `_load_frames(state)` globs `assets/<character>/<state>/*.png` sorted by filename and loads them as `QPixmap`s -- so the numbering and folder name are load-bearing, not cosmetic.
- `character/animation.py`'s `FrameAnimation` cycles a `QLabel` through that frame list on a timer (optionally ping-ponging), and `BobAnimation` layers a vertical sine-wave float on top -- both run together per state (see `IDLE_FRAME_MS`, `WALK_FRAME_MS`, etc. and the `*_BOB` dicts in `character/cognimon.py`).
- `character/cognimon.py`'s `Cognimon` class wires one `FrameAnimation` + one `BobAnimation` per state and switches between them in `_enter_idle`/`_enter_walk`/`enter_thinking`/`enter_talking`.
- The raw source sheets that produced those frames live in `images/cognimon/cognimon_<state>.jpg` (e.g. `cognimon_walking.jpg`), and the quick preview GIFs built from them live in `images/cognimon/gifs/<state>.gif`.

So "turn this reference sheet into an animation" means: raw sheet -> numbered transparent aligned frames in `assets/<character>/<state>/` -> (if it's a new character or new state) wire a `FrameAnimation`/`BobAnimation` pair into the state machine the same way `cognimon.py` does.

## Workflow

### 1. Inspect the sheet

```bash
python .claude/skills/digimind_animate_creature/scripts/grid_overlay.py images/<character>/<character>_<state>.jpg /tmp/<state>_grid.png 50
```

Read the grid image and determine:
- How many poses/frames are in the row, and whether they're evenly spaced (equal-width columns) or not.
- Whether the background is clean white/near-white (like Cognimon's source sheets) or has texture, shadows, or a label/arrow/number between poses that isn't part of any frame.

This decides which mode you use in step 3.

### 2. (Optional) quick raw preview

For a fast sanity check of pose order and spacing before investing in cleanup, slice the raw sheet directly with the project's existing generic script -- it trims to content and pads onto a shared canvas, but leaves the white background in:

```bash
python scripts/make_gif.py images/<character>/<character>_<state>.jpg <n_frames> /tmp/<state>_raw_preview.gif 150 --ping-pong
```

Drop `--ping-pong` for cycles that already loop on their own (walk, idle); keep it for back-and-forth motions. Use this to confirm frame count and order match what you expect before spending time on background removal.

### 3. Slice into clean, aligned transparent frames

Build a JSON spec (full field list in `scripts/slice_sheet_frames.py`'s docstring) and run it:

```bash
python .claude/skills/digimind_animate_creature/scripts/slice_sheet_frames.py /tmp/<state>_spec.json
```

Minimal spec for a clean, evenly-spaced sheet (mirrors how Cognimon's own frames were made):

```json
{
  "source": "images/<character>/<character>_<state>.jpg",
  "out_dir": "assets/<character>/<state>",
  "prefix": "<state>",
  "n_frames": 3,
  "mode": "simple"
}
```

If the sheet has texture/shadows/near-white highlights on the character, or labels/arrows/numbers between poses, switch to floodfill mode (same border-connectivity approach as `digimind_test_creature`'s `clean_character.py`: a near-white pixel reachable from the image edge without crossing the character is real background; one sealed inside the silhouette -- a highlight, a glow line -- is not):

```json
{
  "source": "images/<character>/<character>_<state>.jpg",
  "out_dir": "assets/<character>/<state>",
  "prefix": "<state>",
  "n_frames": 4,
  "mode": "floodfill",
  "erase_boxes": [[10, 5, 180, 40]]
}
```

Use `frame_boxes` instead of `n_frames` when poses aren't evenly spaced (read the boxes off the grid image from step 1).

### 4. QA the frames before trusting them

Composite the actual output frames on solid green -- viewing transparent PNGs directly (e.g. in a chat tool) usually composites them on white, so a leftover pale background patch can be invisible even though it's still opaque:

```bash
python .claude/skills/digimind_animate_creature/scripts/frames_to_gif.py assets/<character>/<state> /tmp/<state>_check.gif 150 --check
```

If leftovers show up, iterate the same way as `digimind_test_creature`:
- Decorative fragment still visible -> add/extend an `erase_box` and rerun.
- Gap in the silhouette (between legs, under an arm) still opaque -> lower `gap_min_size`/`gap_fill_size`/`gap_fill_ratio` (floodfill mode), or add its bbox as an `erase_box`.
- Soft shadow still visible -> loosen `loose_threshold` slightly, but sample a few of the character's own light pixels first (`Image.open(...).getpixel((x, y))`) to make sure you don't start eating real highlight areas.
- A highlight got punched out -> tighten whichever threshold caught it.

Once clean, also render the real (non-check) preview GIF for sharing/review:

```bash
python .claude/skills/digimind_animate_creature/scripts/frames_to_gif.py assets/<character>/<state> images/<character>/gifs/<state>.gif 150 --ping-pong
```

(match the existing convention: `images/cognimon/gifs/idle.gif`, `walk.gif`, `thinking.gif`, `talking.gif`).

### 5. Wire it in

- **Existing character that already uses the `_load_frames` convention (e.g. Cognimon), new or replaced state:** dropping numbered frames into `assets/<character>/<state>/` is enough for the loader to pick them up automatically -- but if it's a brand-new state name (not idle/walk/thinking/talking), add it to `character/cognimon.py`: a `FrameAnimation`/`BobAnimation` pair, a `*_FRAME_MS` timing constant, an `enter_<state>` method, and register it in `_all_animations`, following the existing idle/walk/thinking/talking pattern exactly.
- **Brand-new character, not yet wired into the desktop app:** this skill only produces the assets. Follow `character/cognimon.py` + `character/animation.py` + `ui/desktop.py`'s `_load_frames`/`ASSETS_ROOT` pattern to give the new character its own state machine, or ask the user whether they want that wiring done now or just want the frames/GIF for now.

### 6. Confirm visually

This tool cannot reliably screenshot the real OS desktop in this environment. If the character is already running in the desktop app (or via a `creature_test/show_*.py` script), ask the user to confirm the new animation looks right in motion -- frame count and alignment can look fine frame-by-frame but still jitter or feel wrong at speed.

## Notes

- `slice_sheet_frames.py`'s `simple` mode is literally `scripts/make_sprite_frames.py`'s algorithm (flat white threshold) generalized to accept explicit `frame_boxes` and `erase_boxes`; keep using the project's plain `scripts/make_sprite_frames.py` directly if a sheet is clean and evenly spaced and you don't need either of those.
- Frame timing (`*_FRAME_MS` in `character/cognimon.py`) is a separate tuning step from slicing -- more/fewer frames in the source sheet doesn't by itself fix motion that reads as too fast/slow; adjust the interval too.
- `walk` frames get horizontally mirrored at runtime for the opposite direction (`ui/desktop.py`'s `walk_frames_flipped`) -- don't draw or slice a separate leftward-facing sheet for a walk cycle unless the motion is asymmetric.
