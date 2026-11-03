"""传播卡共用的任务级补充样式（guizang 模板之外，统一放这里）。"""

TASK_CSS = """
    /* BMS-Z spread cards · task-scoped additions */
    .poster .bms-ledger .ledger-row { grid-template-columns: 96px 1fr; align-items: start; }
    .poster .bms-ledger .ledger-title { margin: 8px 0 10px; }
    .poster .bms-ledger .ledger-note { margin: 0; max-width: 46ch; }
    .bms-num {
      font-family: var(--serif-zh); font-weight: 500; font-size: 104px;
      line-height: 1; letter-spacing: .01em; color: var(--ink);
    }
    .bms-unit { font-family: var(--mono); font-size: 28px; margin-left: 14px; color: var(--accent-ink); letter-spacing: .04em; }
    .bms-formula { font-family: var(--mono); font-size: 24px; color: var(--muted); margin: 10px 0 0; letter-spacing: .04em; }
    .bms-note { font-family: var(--serif-zh); font-size: 24px; line-height: 1.62; color: rgba(var(--ink-rgb), .72); margin: 0; }
    .bms-quote { font-family: var(--serif-zh); font-weight: 500; font-size: 46px; line-height: 1.34; color: var(--ink); margin: 0; }

    /* 每章一句话卡：宣言 + 三个小节名 */
    .poster .h-xl.bms-tight { font-size: 60px; line-height: 1.2; }
    .bms-line { font-family: var(--serif-zh); font-weight: 500; font-size: 42px; line-height: 1.42; color: var(--ink); margin: 0; }
    .bms-outline { display: flex; flex-direction: column; margin-top: 8px; }
    .bms-outline .bms-row {
      display: grid; grid-template-columns: 64px 1fr; gap: 20px; align-items: baseline;
      padding: 18px 0; border-top: 1px solid var(--line);
    }
    .bms-outline .bms-row:last-child { border-bottom: 1px solid var(--line); }
    .bms-outline .bms-idx { font-family: var(--mono); font-size: 20px; color: var(--accent-ink); letter-spacing: .08em; }
    .bms-stats { display: flex; gap: 28px; margin-top: auto; padding-top: 18px; }
    .bms-stats span { font-family: var(--serif-zh); font-size: 22px; color: var(--muted); letter-spacing: .02em; }
    .bms-stats b { font-family: var(--mono); font-weight: 500; font-size: 30px; color: var(--ink); margin-right: 8px; }
    .bms-outline .bms-item { font-family: var(--serif-zh); font-size: 26px; line-height: 1.45; color: rgba(var(--ink-rgb), .82); }
"""
