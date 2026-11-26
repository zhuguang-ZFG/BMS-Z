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
- For prose-only revisions, follow `docs/教学设计规范.md` and compare headings, fenced code, equations, tables and generated `kp-backlink` blocks against the baseline. Record any evidence-backed technical correction separately and synchronize its captions, alt text and SVG labels; wording checks are not readability tests.

## Frame evidence and compatibility

1. **Scope / trigger:** changing chapter 18/29 CRC terminology, timing examples or protocol animation assets.
2. **Signatures:** `crc8_smbus(data)` / `CRC8_SMBUS` in `code/protocol/crc.py`; legacy `crc8_atm` / `CRC8_ATM` remain compatible. `python tools/gen_frame_evidence.py [--out DIR]` writes two static SVGs; `python tools/gen_protocol_storyboard.py [--out DIR]` writes six editable panels.
3. **Contracts:** width=8, poly=07, init=00, refin/refout=false, xorout=00. No wire change. `AA 55 01 03 02 0E 74 13` contains eight bytes; with three garbage bytes completion is at input index 10. Good and bit-flipped flows are independent replays.
4. **Validation / errors:** ASCII `123456789` -> F4; body `01 03 02 0E A0` -> 31. ATM HEC / I-432-1 uses xorout=55 -> A1, so changing the name must not silently select that algorithm. Generation fails on IO or mismatched byte/label cardinality.
5. **Cases:** duplicate reports leave the last accepted-new timestamp unchanged; age 199 ms is below this example's cutoff, age 200 ms reaches it. Check timeouts without arrivals. Mod-16 14->1 misses two frames; R24-11 P1 skips 15 and misses one.
6. **Tests:** CRC fixed vectors plus legacy entry points; `tools/tests/test_protocol_storyboard.py` verifies every displayed byte, single-bit corruption, completion and rejection. Regenerate SVGs into a temporary directory and compare bytes. Refresh storyboard WebP, animated export, stills and book print copy together, then inspect publication output.
7. **Wrong / correct:** omitting address/length while retaining a full-frame CRC produces an impossible diagram. Keep the full wire array and derive counters from the parser. Distinguish interval jitter from phase jitter, and protocol-specific recovery from the teaching parser's prefix scan.

## FigureSpec authoring command

1. **Scope / trigger:** generating an original book diagram from checked-in JSON, outside normal publication builds.
2. **Signature:** `python tools/render_book_figurespec.py SPEC OUTPUT --renderer PINNED_HELPER`.
3. **Contract:** local UTF-8 FigureSpec JSON, required `title` and `description`; helper SHA-256 must match `RENDERER_SHA256`. No network or global configuration. Output is SVG with role/title/desc and stable content.
4. **Validation / errors:** mismatched helper hash or upstream validation issue -> exit 2 before writing output; missing/malformed JSON -> fail. File IO errors propagate.
5. **Cases:** checked-in route spec + reviewed helper -> SVG; same inputs -> identical bytes; changed helper -> rejected.
6. **Verification:** render twice and compare bytes; inspect XML title/desc; modified helper must be rejected before import/output. Inspect the actual diagram and published pages.
7. **Wrong / correct:** editing generated SVG loses reproducibility; edit JSON and regenerate through the hash-checked helper instead.

## EKF teaching evidence

1. **Scope / trigger:** chapter 27 covariance, innovation allocation or operating-point explanations.
2. **Signatures:** `prediction_example()`, `innovation_allocations()`, `controlled_trace(current, residual, *, fixed_c, count=120)` in `bms-book/code/ekf_covariance_evidence.py`; `python tools/gen_ekf_evidence.py [--out DIR]` writes FigureSpec sources.
3. **Contract:** preserve `ekf_soc.run()`, `first_ticks()` and positional `Tick` compatibility. `Tick.kh` is C0*K0, the SOC voltage contribution, not total C*K. Fixed-C comparisons use a matching linear OCV model; nonlinear comparisons use the original curve and Jacobian.
4. **Validation / errors:** comparison SOC must stay strictly inside (0,1), without clipping. Nonfinite inputs and out-of-domain states fail. Report SOC variance and polarization variance separately in SOC² and V².
5. **Cases:** with the published parameters, polarization sigma falls 10→9.725049 mV during prediction; the second tick has C0*K0=0.882564449 and K1=-0.270402908, summing to C*K=0.612161541. Verify C*K=1-R/S using unrounded values.
6. **Verification:** compare every controlled tick to the repository NumPy estimator; fixed-C trajectories match across input changes, state-dependent C changes P. Regenerate JSON/SVG and compare bytes, then inspect site, offline, EPUB and print pages.
7. **Wrong / correct:** Q positive semidefinite does not imply P-minus-P is positive semidefinite. A covariance recurrence without explicit I/z can still depend on them through the EKF Jacobian. Two small NIS samples do not isolate R; deterministic sinusoidal noise is not an independent Gaussian sequence.

## Narrow-screen formula accessibility

MathJax's clipped `mjx-assistive-mml` can still widen a page after its visible SVG
has been resized. Keep the MathML accessible, constrain the invisible box to 1px,
and verify document scroll width at 375px with JavaScript both enabled and disabled.
Do not fix this by removing MathML or hiding it with `display:none`.

## NIS window evidence

- Use SciPy's public distribution APIs for chapter 17 reference quantiles;
  record the reviewed upstream version/commit and license. Keep the older
  standard-library ordering experiment independent of SciPy.
- State scalar iid standard normal innovations, predetermined equal-weight
  windows, and covariance specified without fitting that window. For N=512,
  the inclusive binomial count region is [16,36] (96.763925% coverage) and
  the mean-square region is [0.881243,1.126155]. These are separate reference
  regions, not a joint 95% rule or a confidence interval for a parameter.
- Same-window centering and RMS normalization fixes average square at 1;
  sorting preserves counts but changes temporal structure. The legacy seed
  5720 experiment has 24 exceedances, while the raw known-scale draws have 21.
- Finite-window effective sample count requires the full weighted covariance
  sum. For a stationary Gaussian AR(1), use rho^h for the mean and rho^(2h)
  for squared innovations; neither licenses exact chi-square thresholds for
  correlated data. Do not infer that model from a sorted series.
- Real-data diagnostics are time weighted. Do not compare their reported mean
  directly with an equal-weight iid-window band. Smaller windows widen the
  single-lag screening band, making a fixed correlation harder to detect.
- Validate probability coverage against independent binomial/gamma formulas,
  and effective counts against a full covariance matrix. Refresh animation,
  print snapshot, alt/caption/visual registry and technical fingerprint together.


## HPPC independent prediction evidence

1. **Scope / trigger:** D11 or chapter 13/28 HPPC fitting, finite-pulse correction, or validation figures.
2. **Signatures:** `r1_from_amplitude(a_v, i_pulse_a, *, tau_s, pulse_s)`; `joint_fit(observations, *, grid=TAU_GRID)`; `predict_tail(fit, pulse, calibration)`; `score_prediction(prediction, observation)`; `d11_joint_hppc.py [--out DIR] [--scipy]`; `make_d11d12_figures.py --unit d11 [--out DIR] [--book-out DIR]`.
3. **Contracts:** schema 2 separates `local_k_counterexample`, `noiseless`, `noisy`, `mismatch`, optional `scipy`. Fit A/B shares R1/tau with one free K per pulse. Predictor has no truth or observed-voltage input; calibration explicitly supplies OCV/Q and protocol supplies initial SOC. Discharge is positive. `leave_one_out_rmse_mv` was removed because the original score reused training voltage. Keep its old SVG filename as a stable publication entry only.
4. **Validation / errors:** empty or duplicate training IDs, nonfinite samples, non-increasing time, zero excitation, invalid tau/pulse duration or nonpositive inferred resistance raise ValueError. Prediction rejects training IDs; scoring rejects ID/time-grid mismatch. Grid endpoints and R1 bounds are reported; one-point tau evaluation is not a search. Missing SciPy fails only the explicitly requested optional path with an installation hint.
5. **Cases:** noiseless same-model fit recovers 45s/15mOhm. Fixed noisy grid fit is 44.5s/14.823814mOhm; training/independent prediction RMSE is 0.101542/0.104042mV. Changing only validation truth tau to70s gives0.552790mV with unchanged fit. The160mV local-K counterexample is separate, noiseless and same-protocol. These are synthetic evidence, not real-cell accuracy.
6. **Tests:** changing validation voltage changes scores only; non45s truth and a wrong grid test fitted-tau correction; post-pulse SOC determines K; dense-grid/SciPy comparisons use the same objective. Rebuild SVGs and compare, preserve D12 bytes, inspect label/curve bounds and publication output. Run D11 tests and registry checks in tests.yml site-build, not only local pytest. Site buildEnd already publishes engineering HTML/EPUB; local engineering PDF needs `tools/build_engineering.py --pdf`.

Engineering HTML must wrap long prose tokens (field lists, paths and source URLs) without widening the viewport. Preserve local scrolling for code, tables and equations; never hide document overflow to pass the gate. `book/check_compatibility.py` checks the complete engineering book at 320/375px, with JavaScript disabled, and with enlarged type.
7. **Wrong / correct:** fitting K or adjusting initial SOC from validation voltage before scoring the same tail is not independent prediction. Provide independent calibration before voltage is opened, or explicitly reserve an initialization window and evaluate only a later window. Use fitted tau in finite-pulse correction, never generator truth. Keep PyBOP source-reading status distinct from reproduced upstream notebooks; disclose its validation-SOC adjustment.

Engineering figure markup must start a separate Markdown block. The assembly test inspects every XHTML document for orphan captions and figures nested inside paragraphs; tests and Pages also run EPUBCheck on the engineering EPUB after site assembly.

## HPPC grid error evidence

1. **Scope:** chapter 28 table spacing, SOC coordinates, interpolation and calibration claims.
2. **API:** `interpolate_table(soc_nodes, temp_c_nodes, values_v, queries)` returns `(N,)` via SciPy RGI linear with bounds_error=True; `bilinear_bound(h_soc,h_temp_c,m_soc2,m_temp2)` returns V; `build_report()` schema 1; `hppc_grid_evidence.py [--out DIR]`; `gen_hppc_grid_evidence.py [--out DIR]`.
3. **Contract:** increasing finite axes with >=2 points, SOC in [0,1], values shape (n_soc,n_temperature), nonempty finite queries (N,2). Reject descending/repeated/singleton axes, wrong shapes and out-of-domain queries. Never silently reorder, transpose, clamp or extrapolate.
4. **Evidence:** grid spacing does not imply coordinate error. Local slope times displacement is an approximation unless slope is constant; a uniform derivative bound must cover the whole interval. C² interpolation uses supplied global pure second-derivative bounds; midpoint maximizes the geometric factor, not necessarily the actual error. Three-point differences and dense probes do not prove a global bound. Node error is a separate convex-weight term.
5. **Cases:** steep line interpolates exactly; nonlinear OCV finite change .05→.10 is221.029650732mV versus local340mV. Monotone hidden curve has collinear nodes but20mV independent midpoint errors. Analytic two-axis budgets3/2.625/1.125/.75mV; common+2mV gives5mV on original grid and persists after refinement. Synthetic claims only.
6. **Verification:** independent corner weights, non-square/nonuniform grids, exact affine and zT reproduction, boundary and nonfinite errors; compare figure geometry and budget bars to report, rebuild byte-identically. Inspect site/offline/EPUB/A4/16K,375px,dark,no-JS,grayscale. Keep original40/120s and D11 baselines.
7. **Sources:** FNC proves stability/convergence with a looser bound; derive1/8 separately. SciPy1.18.1 public API reused under BSD3. PyBaMM5307 was not merged and not a reproduced fix; source reading is not a full DFN run. Validation points used to choose new nodes need replacement final holdout data.
