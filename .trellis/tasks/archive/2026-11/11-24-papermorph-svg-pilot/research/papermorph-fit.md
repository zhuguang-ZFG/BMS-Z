# Papermorph fit for the BMS SVG pilot

Research checked 2026-11-24 against the official repository at
`https://github.com/DozenTwelve/Papermorph`, `main` commit
`839a62cad3c74446944a167faff07c994f33e5b7` (MIT code license).

## Official project facts

- The README describes deliverables as static web pages that need no server,
  database, or account; its listed installation command uses `--agent claude-code`
  or `--agent opencode`.
- The Skill describes textbook lessons as SVG stages and a player. Its lessons
  documentation models a movable figure as one shared state rendered through a
  single `draw()` function, with reader input changing state through one setter.
- The lesson figure guidance covers drag/touch, keyboard actions, state reset,
  question grading and browser tests. It specifically calls for pointer capture,
  usable touch targets and keyboard equivalents.
- The README lists `uv`, FFmpeg and Playwright browsers as requirements. Edge TTS
  or local Kokoro can provide narration; selected image, video or acted-voice
  steps use optional model APIs and may cost money.

Primary references:

- `https://github.com/DozenTwelve/Papermorph/blob/main/README.md`
- `https://github.com/DozenTwelve/Papermorph/blob/main/.claude/skills/papermorph/SKILL.md`
- `https://github.com/DozenTwelve/Papermorph/blob/main/.claude/skills/papermorph/references/lessons/figures.md`

## Local project fit

- `bms-book/reader.js` already has `mountBookLab(panel)` with per-experiment
  branches, native disabled-until-mounted range inputs, immediate output updates
  and reset behavior.
- `docs/.vitepress/theme/index.ts` mounts those panels with the existing
  `v-book-lab` directive. `bms-book/build_html.py` embeds that same reader in the
  single-file offline edition.
- `bms-book/book/09-均衡.md` already explains the 4 V / 100 Ω / 1 Ah passive
  example and asks what changes at 50 Ω. `bms-book/code/balancing_energy.py`
  asserts the existing 40 mA, 25 h and 4 Wh baseline.
- `bms-book/book/10-模型OCV四项.md` and `reader.js` provide an existing precedent
  for a parameter-controlled inline SVG curve.

## Planning implication

Build the pilot on the current BookLab/inline-SVG path first; it already reaches
both the VitePress chapter and offline HTML without new packages. Keep Papermorph
out of the dependency graph. The evaluation should ask whether its narration,
beat player and figure-level questions provide a clear learning benefit beyond
this pilot, and whether the documented agent setup works for this Codex workflow.
