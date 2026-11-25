# Papermorph decision after the BMS pilot

Official project sources checked on 2026-11-24 against repository revision
`839a62cad3c74446944a167faff07c994f33e5b7`.

The official README documents a larger publishing workflow: storyboarded
chapters, timed narration, a player with pause/step/speed/captions, and MP4 or
SCORM exports. Its installer names Claude Code and OpenCode. It lists `uv`,
FFmpeg and Playwright browsers as prerequisites. Optional generation steps can
call paid media APIs; the README estimates about $10–18 in model usage for an
illustrated physics chapter.

| Need in the passive-balance pilot | Current BookLab path | Papermorph |
| --- | --- | --- |
| Adjustable circuit with a computed SVG and three linked values | Implemented in the existing chapter/reader pipeline | Lesson figure state is a natural fit |
| Immediate quantitative question feedback | Implemented with native controls in the chapter | Figure questions are a natural fit |
| Offline single-file HTML plus current print/EPUB paths | Shares existing `reader.js`; static HTML, PDF and EPUB stay in the current build pipeline | Publishes its own player and supports separate MP4/SCORM output; adapting it into both existing book readers adds an integration step |
| Timed narration, drawing by beat, and short films | Not provided by the chapter reader | A clear additional capability in the official workflow |
| Codex workflow and setup | Existing tooling, dependency graph and CI | Installer documents Claude Code/OpenCode. Codex would need a locally validated adapter. Core setup adds `uv`, FFmpeg and browsers; optional generated media adds API cost |

**Recommendation: do not install Papermorph for this project yet.** The measured
learning gain of the pilot is the connection between one adjustable resistor,
its current, dissipated power and ideal time, plus immediate feedback on one
prediction. The existing BookLab reader already supplies that in both the site
chapter and offline book. Review this pilot first; consider a separate
Papermorph trial if a lesson needs timed narration or an MP4/SCORM deliverable.
Before adopting it, test the Codex setup and the offline integration against a
concrete lesson, and account for the additional toolchain and optional model
cost.

Official sources:

- `https://github.com/DozenTwelve/Papermorph/blob/839a62cad3c74446944a167faff07c994f33e5b7/README.md`
- `https://github.com/DozenTwelve/Papermorph/blob/839a62cad3c74446944a167faff07c994f33e5b7/.claude/skills/papermorph/SKILL.md`
- `https://github.com/DozenTwelve/Papermorph/blob/839a62cad3c74446944a167faff07c994f33e5b7/.claude/skills/papermorph/references/lessons/figures.md`
