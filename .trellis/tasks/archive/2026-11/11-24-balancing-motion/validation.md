# Validation record

- Work commit: `a515580f60be200ba6f1d9ad58067a243e2f1438`.
- Pull request: `zhuguang-ZFG/BMS-Z#114`, base `main`.
- Related Python tests: 479 passed. Node/site tests: 77 passed.
- Ruff, motion contracts, curriculum map, document consistency and textbook
  structure checks passed. Full site build passed on retry with the Node memory
  limit set; built-site links and search checks also passed.
- Edge review covered both diagrams in light/dark appearance, key motion frames,
  static variants, active-balancing waveform peak and phase switching, 375 px
  rendering, reduced-motion source selection and keyboard horizontal scrolling.
- Evidence: `.local/balancing-preview/` and
  `.local/build-balancing-motion.log`.
- CI: all 20 of 20 checks passed. The initial PR browser/offline regression job
  stalled while fetching the 61.2 MB CJK font package; its retry installed the
  package and completed browser checks successfully without changing the checks.
- PR #114 was merged into `main` on 2026-11-24 at 05:24 (Asia/Shanghai), after
  confirming all checks passed and using head SHA
  `a515580f60be200ba6f1d9ad58067a243e2f1438`. Merge commit:
  `9af2391ff74ae0f8662b0021804471fbfb3e1b73`.
- The external link checker encountered a transient GitHub 503; rerunning the
  failed job passed without weakening the check.
- Local PDF/EPUB files were not regenerated in this round.
- Existing `package-lock.json` edits are outside this task. Local Trellis setup
  and records stay uncommitted; preserve the initialized bootstrap task.
