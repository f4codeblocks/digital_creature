---
name: digimind_test_creature
description: Turns a raw character reference-sheet image (a JPG/PNG with a creature illustration plus surrounding decorative title/stat-box/icon/card artwork on a white or patterned background) into a clean transparent PNG of just the character, and generates+runs a standalone creature_test/show_<name>.py script that floats that character in a transparent always-on-top window on the desktop, reusing the digital_creature project's BobAnimation. Use this whenever the user drops a new character card image into images/ and asks to clean it up, remove its background/decorations, isolate the character, or preview/test it floating on the desktop -- even if they don't say "skill" or name this skill directly. Pushy trigger: any request to prep a new creature image for the desktop-pet prototype should go through this workflow.
---

# Digimind test creature

Turn a new character reference-sheet image into (1) a clean transparent PNG of just the character and (2) a running desktop preview, following the exact recipe validated in this project on Curimon and Amicimon.

## Why this needs more than "remove white background"

These reference sheets are card layouts: a title, a logo, two columns of stat/description text, a couple of small icons, and a bottom info banner, all surrounding the character on a white or pale patterned background. Two things make naive approaches fail:

- **A flat white-ish threshold eats the character's own details.** Character art usually has near-white highlights baked in -- glow lines, eye whites, claw tips, a glowing chest emblem. Those pixels are just as "near-white" as the background, so a simple threshold punches holes in the character.
- **A flat crop can't dodge the decorations.** Limbs, tails, and wings usually splay out diagonally close to the side text boxes, so there's rarely a rectangle that contains the whole character but excludes all the surrounding text.

The fix used here: manually identify and paint over the decorative regions (they're spatially separate from the character, even if a plain crop can't isolate them), then remove the remaining background using **connectivity to the image border**, not just color. A near-white pixel that's reachable from the image edge without crossing the character is real background. A near-white pixel sealed inside the character's silhouette (a highlight, a glow line) is not, even though the color looks the same.

## Workflow

### 1. Inspect the source image

Run the grid overlay so pixel coordinates are readable:

```bash
python .claude/skills/digimind_test_creature/scripts/grid_overlay.py images/<name>.jpg /tmp/<name>_grid.png 50
```

Read the resulting image (it has a blue grid every 50px with axis labels). Identify:
- The character's bounding box (top of ears/horns to bottom of feet/shadow, leftmost to rightmost point of any outstretched limb or tail).
- The bounding box of every decorative element that is NOT the character: title text, logo icon, tagline, left/right stat-description text boxes, small badge/heart/target icons scattered around, the bottom info banner.

Zoom into ambiguous spots (crop a small region and read it) rather than guessing -- getting an erase box a few pixels wrong either clips the character or leaves a visible text fragment, and both are easy to fix once you can see the exact pixels.

### 2. Write the spec and clean the character

Build a JSON spec (see `scripts/clean_character.py`'s docstring for the full field list) listing the erase boxes and the crop box, then run it:

```bash
python .claude/skills/digimind_test_creature/scripts/clean_character.py /tmp/<name>_spec.json
```

This paints the erase boxes white, crops to the character, and removes the background via border-connected flood fill (plus a second looser pass for soft shadows, and a gap-fill pass for enclosed pockets like the space between legs or under an arm -- see the docstring for why size/fill-ratio heuristics are used to tell a "gap in the silhouette" apart from a "highlight on the character"). It writes the final PNG to the `output` path in the spec, plus `<output>.check.png` composited on solid green.

**Always look at the `.check.png`, not just the PNG on its own.** Viewing an RGBA file directly (e.g. in a chat tool) usually composites it onto white, so a leftover pale-pink background patch can be invisible even though it's still opaque. Green makes any non-transparent leftovers obvious immediately.

If the check reveals leftovers:
- **Decorative text/icon fragments still visible** -> add/extend an erase box in the spec and rerun. Err small and iterate; it's cheap.
- **A gap in the silhouette (between legs, under an arm) still opaque** -> lower `gap_min_size` or `gap_fill_size`/`gap_fill_ratio` slightly, or add its bbox as an explicit erase box if it's a one-off.
- **A soft shadow/gradient still visible** -> loosen `loose_threshold` slightly (lower the G/B minimums), but check this doesn't start eating the character's own lighter/rim-lit red or highlight areas -- sample a few of those pixels first if unsure (`Image.open(...).getpixel((x,y))`) and keep the threshold below them.
- **A hole punched in a highlight the character should keep** (this means a background pass wrongly grabbed it) -> tighten whichever threshold caught it, or shrink `gap_min_size`/`gap_fill_size` back up if the gap-fill pass was the culprit.

Save the final output as `images/<name>_transparent.png`.

### 3. Generate the floating test script

```bash
python .claude/skills/digimind_test_creature/scripts/make_creature_script.py . <name> images/<name>_transparent.png 0.216
```

This writes `creature_test/show_<name>.py` from the project's standard template (same shape as the existing `show_creature.py` / `show_amicimon.py`): frameless/transparent/always-on-top PySide6 window, `character.animation.BobAnimation` for the gentle floating effect, bottom-right screen placement. The scale argument defaults to `0.216` to match the size other test creatures were tuned to in this project; ask the user if they want a different size, otherwise keep it consistent with the others already running.

### 4. Run it and confirm

```bash
python creature_test/show_<name>.py
```

Run in the background (this is a GUI window, it doesn't exit on its own). Check the background task's output for import/runtime errors. This tool cannot reliably screenshot the real OS desktop in this environment, so ask the user to confirm visually that the creature appears, floats, and looks clean -- don't claim success without that confirmation.

If other creature windows from this project are already running, mention that they may overlap (they all default to the same bottom-right anchor point) rather than assuming it's a bug.

## Notes

- The character's own package (`character.animation.BobAnimation`) is imported via a `sys.path` tweak in the generated script, since `creature_test/` is a subdirectory -- keep that import pattern when hand-editing generated scripts.
- If the same character needs walk/idle/thinking/talking sprite *animation* frames (not just a single floating still), that's a separate, heavier workflow (slicing a multi-pose sheet into aligned frames) -- this skill only covers the single-image "clean + float" case.
