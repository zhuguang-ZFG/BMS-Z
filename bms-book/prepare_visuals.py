"""Print an apply_patch for manuscript figures; chapter edits stay reviewable.

Run: python bms-book/prepare_visuals.py
The motion asset remains in docs/circuits/assets/; the print snapshot lives in
bms-book/assets/print/. Do not duplicate the original animation.
"""
from pathlib import Path
import json
import re
import sys
import difflib

ROOT = Path(__file__).resolve().parent
entries = json.loads((ROOT / "visuals.json").read_text(encoding="utf-8"))
patch = ["*** Begin Patch"]
for chapter in sorted({entry["chapter"] for entry in entries}):
    manuscript = next((ROOT / "book").glob(f"{chapter}-*.md"))
    source = manuscript.read_text(encoding="utf-8")
    original = source
    sequence = 0
    for entry in (entry for entry in entries if entry["chapter"] == chapter):
        if f'data-animation="{entry["file"]}"' in source:
            continue
        sequence += 1
        anchor = next(line for line in source.splitlines() if line.startswith(entry["before"] + " "))
        animation = f'../../docs/circuits/assets/{entry["file"]}'
        snapshot = f'../assets/print/{entry["file"]}'
        figure = [
            f'<figure class="book-motion" data-animation="{entry["file"]}" data-mode="static">',
            f'<img src="{snapshot}" alt="{entry["caption"]}" data-motion-src="{animation}">',
            '<button type="button" data-book-motion v-book-motion aria-pressed="false" hidden>播放动画</button>',
            f'<figcaption>图 {int(chapter)}-{sequence}　{entry["caption"]}</figcaption>',
            f'<p class="visual-guide"><strong>先看哪里：</strong>{entry["observe"]}</p>',
            f'<p class="visual-question"><strong>看完追问：</strong>{entry["question"]}</p>',
            '</figure>',
            '',
        ]
        source = source.replace(anchor, "\n".join(figure) + "\n" + anchor, 1)
    sequence = 0
    def renumber(match, chapter_number=int(chapter)):
        global sequence
        sequence += 1
        return f'<figcaption>图 {chapter_number}-{sequence}'
    source = re.sub(r'<figcaption>图 \d+-\d+', renumber, source)
    if source != original:
        patch += [f"*** Update File: {manuscript}"]
        difference = list(difflib.unified_diff(original.splitlines(), source.splitlines(), n=2))[2:]
        patch += ["@@" if line.startswith("@@") else line for line in difference]
patch.append("*** End Patch")
sys.stdout.reconfigure(encoding="utf-8")
print("\n".join(patch))
