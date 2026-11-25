# Book Evidence Assets

## Authoring contracts

- In BMS chapter HTML, write image attributes as `src`, `alt`, then optional
  dimensions. `docs/.vitepress/book-sources.mjs` recognizes this order when
  converting book-relative paths for VitePress. Run the image-resolution case
  in `book-reading-split.test.mjs` after adding images.
- New static volume I diagrams belong in `analog/assets/figures/`.
  `analog/assets/svg/` is the generated animation inventory, checked against
  its generator by `test_svg_assets.py`.
- Register volume I diagrams AND photos in
  `analog/docs/superpowers/visual/visual-manifest.yml`, with an authoring/source
  record under `prompts/`. A source photograph is not an AI-generated asset.
  Record only actual review status; do not invent user approval or scores.
- Use `book-photo-pair` / `book-photo-pair__images` for paired book evidence.
  Both VitePress and offline HTML must stack the pair on narrow screens.
- A capped photo inside the pair must retain `width:100%` when print changes
  generic image width to `auto`. An inline `max-width:320px` alone overrides the
  generic `max-width:100%` and lets the image cover its neighbor in print.
- Allow long captions to wrap on phones. Check document scroll width as well
  as image width: a caption can overflow even if all image boxes fit.
- Raw HTML captions may bypass Markdown math conversion in EPUB. Write simple
  formulas as readable text, or use the existing supported math conversion;
  verify the rendered EPUB, not just the Markdown source or ZIP membership.

## Evidence and licensing

- Keep photographs, instrument screenshots and authored diagrams distinct.
  Pin upstream GitHub commits and record document/image licenses separately
  from firmware or hardware licenses. Preserve image orientation and colors.
- State test current, voltage, ambient temperature, cooling and duration next
  to measured thermal images. Distinguish surface measurements, sensor traces,
  synthetic teaching models and extrapolations.
- Cite only book sections actually obtained and read. A failed Z-Library
  request or a catalogue title match does not establish access to book text.

## Validation

Run volume I `test-static` and `visual-check`, BMS checks, relevant Python and
Node regressions, then the unified book build. Inspect the affected pages in
the site, offline HTML, A4/16K PDF and extracted EPUB. Desktop, narrow, dark,
no-JavaScript and grayscale checks complement EPUBCheck; browser EPUB rendering
does not establish compatibility with a physical e-reader.

## Communication examples and editable figures

- State character format before deriving UART/RTU timing; do not transfer the 10-bit 8N1 example to the 11-bit RTU guide. Above 19200, distinguish recommended fixed RTU timers from computed character duration.
- Give healthy budgets and timeout configuration a common origin. A fault wait is not a healthy processing bound. State polling, retries and action-time exclusions.
- A CAN stuffing example must specify incoming count and bit pattern. Constant raw bits are not the maximum-stuffing pattern; real frames do not reset at data-field boundaries. Update curriculum source, generated navigation, animation labels/desc and narration together.
- Preserve source IDs used by other chapters; add a version-specific source entry instead of silently retargeting a shared reference.
- Keep editable FigureSpec JSON with its SVG. Pin and hash-check external renderers; include accessible title/desc and record the upstream license. Do not make normal book builds depend on a globally installed skill.
- On Windows, curriculum generation can rewrite historical mixed line endings. Restore unchanged bytes after verifying normalized content; preserve unrelated user changes.

## FigureSpec authoring command

1. **Scope / trigger:** generating an original book diagram from checked-in JSON, outside normal publication builds.
2. **Signature:** `python tools/render_book_figurespec.py SPEC OUTPUT --renderer PINNED_HELPER`.
3. **Contract:** local UTF-8 FigureSpec JSON, required `title` and `description`; helper SHA-256 must match `RENDERER_SHA256`. No network or global configuration. Output is SVG with role/title/desc and stable content.
4. **Validation / errors:** mismatched helper hash or upstream validation issue -> exit 2 before writing output; missing/malformed JSON -> fail. File IO errors propagate.
5. **Cases:** checked-in route spec + reviewed helper -> SVG; same inputs -> identical bytes; changed helper -> rejected.
6. **Verification:** render twice and compare bytes; inspect XML title/desc; modified helper must be rejected before import/output. Inspect the actual diagram and published pages.
7. **Wrong / correct:** editing generated SVG loses reproducibility; edit JSON and regenerate through the hash-checked helper instead.
