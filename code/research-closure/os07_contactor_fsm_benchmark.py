"""OS07 foxBMS 2 -> S7 benchmark: independent contactor FSM (no upstream OS lib).

Contract (research.md OS07 + snapshot.json F01-F05 / REF-FOX-01):
- command != feedback identity: with no feedback source feedback=currentSet is
  presumed only; an independent digital contact proves the physical contact.
- full FSM OFF / PRECHARGE / ON / FAULT: command ON with no feedback ON within
  N ms -> FAULT; command OFF with feedback still stuck ON -> FAULT; debounce
  time is a constructor parameter.
- clear-flag (diagnostic record only) / reset (back to OFF, no permission) /
  re-permit (the only operation that enables re-close) are independent.
- Upstream review covered only driver + diag callback; this benchmark does not
  claim to have traced its upper FSM or debounce timing. It recomputes the
  contract points independently with stdlib + numpy as an S7 acceptance base.
"""
import json
import math
import platform
from pathlib import Path

import numpy as np

EVIDENCE = Path(__file__).parent / "evidence" / "os07-contactor-fsm-benchmark.json"
DT_MS = 1.0

DEBOUNCE_MS = 10.0
FEEDBACK_TIMEOUT_MS = 50.0
STATES = ("OFF", "PRECHARGE", "ON", "FAULT")




class Debouncer:
    """Integrator debounce: a new level is accepted after `need` stable samples."""

    def __init__(self, debounce_ms, dt_ms, initial=False):
        self.need = int(math.ceil(debounce_ms / dt_ms))
        self.value = bool(initial)
        self.candidate = bool(initial)
        self.count = self.need

    def feed(self, raw):
        raw = bool(raw)
        if raw == self.candidate:
            self.count = min(self.count + 1, self.need)
        else:
            self.candidate = raw
            self.count = 1
        if self.count >= self.need:
            self.value = self.candidate
        return self.value


class ContactorFSM:
    """Four-state contactor FSM with command/feedback identity and recovery gates."""

    def __init__(self, debounce_ms=DEBOUNCE_MS, timeout_ms=FEEDBACK_TIMEOUT_MS,
                 dt_ms=DT_MS, feedback_source="digital"):
        self.dt_ms = float(dt_ms)
        self.timeout_ms = float(timeout_ms)
        self.feedback_source = feedback_source  # "digital" | "none"
        self.deb = Debouncer(debounce_ms, dt_ms)
        self.state = "OFF"
        self.cmd_phase = None      # "close" (precharge) / "open" (verify open)
        self.t_cmd = 0.0
        self.close_permit = True   # fresh system may close once; FAULT revokes it
        self.diag = {"feedback_not_on": False, "feedback_stuck_on": False}
        self.counters = {"fault_feedback_not_on": 0, "fault_feedback_stuck_on": 0,
                         "close_blocked": 0, "close_ok": 0, "open_ok": 0}
        self.history = []
        self.transitions = []

    def _enter_fault(self, key, event, t):
        prev = self.state
        self.state = "FAULT"
        self.cmd_phase = None
        self.close_permit = False
        self.diag[key] = True
        self.counters["fault_" + key] += 1
        self.transitions.append({"t_ms": float(t), "from": prev,
                                 "to": "FAULT", "event": event})
        return event

    def step(self, t, cmd, raw_fb):
        """Advance one dt step. cmd in {"ON","OFF"}; raw_fb is the sampled feedback."""
        t = float(t)
        cmd = str(cmd)
        prev = self.state
        event = None

        # feedback identity: no independent source -> feedback is presumed = command
        if self.feedback_source == "none":
            debounced = (cmd == "ON")
        else:
            debounced = self.deb.feed(raw_fb)

        if self.state == "FAULT":
            if cmd == "ON":
                self.counters["close_blocked"] += 1
                event = "CLOSE_BLOCKED"
        elif cmd == "ON":
            if not self.close_permit:
                self.counters["close_blocked"] += 1
                event = "CLOSE_BLOCKED"
            elif self.state == "OFF":
                self.state = "PRECHARGE"
                self.cmd_phase = "close"
                self.t_cmd = t
                event = "CLOSE_CMD"
            elif self.state == "ON" and self.cmd_phase == "open":
                self.cmd_phase = None
                event = "OPEN_ABORT"
        elif cmd == "OFF":
            if self.state == "ON":
                # 只在首次进入开断验证时起表；持续 OFF 不得重置超时
                if self.cmd_phase != "open":
                    self.cmd_phase = "open"
                    self.t_cmd = t
                    event = "OPEN_CMD"
            elif self.state == "PRECHARGE":
                self.state = "OFF"
                self.cmd_phase = None
                event = "CLOSE_ABORT"

        # feedback evaluation
        if self.state == "PRECHARGE":
            if debounced:
                self.state = "ON"
                self.cmd_phase = None
                self.counters["close_ok"] += 1
                event = "FEEDBACK_ON_OK"
            elif t - self.t_cmd >= self.timeout_ms:
                event = self._enter_fault("feedback_not_on", "FEEDBACK_TIMEOUT", t)
        elif self.state == "ON" and self.cmd_phase == "open":
            if not debounced:
                self.state = "OFF"
                self.cmd_phase = None
                self.counters["open_ok"] += 1
                event = "FEEDBACK_OFF_OK"
            elif t - self.t_cmd >= self.timeout_ms:
                event = self._enter_fault("feedback_stuck_on", "STUCK_CLOSED", t)

        if self.state != prev and event is None:
            event = "STATE_CHANGE"
        if self.state != prev and not any(
            tr["t_ms"] == t and tr["from"] == prev and tr["to"] == self.state
            for tr in self.transitions
        ):
            self.transitions.append({"t_ms": t, "from": prev,
                                     "to": self.state, "event": event})
        self.history.append({
            "t_ms": t, "cmd": cmd, "raw_fb": bool(raw_fb),
            "debounced_fb": bool(debounced), "state": self.state,
            "close_permit": bool(self.close_permit),
            "diag": dict(self.diag), "event": event,
        })

    def snapshot(self):
        return {"state": self.state, "close_permit": bool(self.close_permit),
                "diag": dict(self.diag)}

    def clear_diag(self):
        """Clear diagnostic record only; neither state nor permission changes."""
        for key in self.diag:
            self.diag[key] = False

    def reset(self):
        """Return to OFF and clear transient timing; permission is NOT restored."""
        self.state = "OFF"
        self.cmd_phase = None
        self.t_cmd = 0.0
        self.deb = Debouncer(DEBOUNCE_MS, self.dt_ms)

    def repermit(self):
        """The only operation that restores close permission; state unchanged."""
        self.close_permit = True


def _first_event(history, event):
    for rec in history:
        if rec["event"] == event:
            return rec["t_ms"]
    return None


def run_scenarios():
    """Run all scenarios; return (checks, traces, transitions, counters)."""
    checks = {}
    traces = {}
    transitions = []
    counters = {}

    # A: 正常闭合——命令 ON，独立反馈在去抖窗内转 ON
    fsm_a = ContactorFSM()
    for t in np.arange(0.0, 31.0, DT_MS):
        cmd = "ON" if t >= 1.0 else "OFF"
        raw = t >= 2.0
        fsm_a.step(float(t), cmd, raw)
    t_on = _first_event(fsm_a.history, "FEEDBACK_ON_OK")
    checks["normal_close_reaches_on"] = {
        "pass": bool(fsm_a.state == "ON" and t_on is not None
                     and t_on <= DEBOUNCE_MS + 2.0
                     and not any(fsm_a.diag.values())),
        "value": {"final_state": fsm_a.state, "t_feedback_on_ms": t_on,
                  "diag": dict(fsm_a.diag)},
        "note": "cmd ON 后独立反馈持续 ON，t=11ms 去抖采信转 ON，未置诊断",
    }
    traces["normal_close"] = fsm_a.history

    # B: 反馈粘连——命令 OFF 后反馈恒 ON，超时未断 → FAULT
    fsm_b = ContactorFSM()
    for t in np.arange(0.0, 101.0, DT_MS):
        cmd = "OFF" if t < 1.0 else ("ON" if t < 40.0 else "OFF")
        raw = t >= 2.0  # 触点闭合后粘连，反馈恒 ON
        fsm_b.step(float(t), cmd, raw)
    t_stuck = _first_event(fsm_b.history, "STUCK_CLOSED")
    checks["stuck_feedback_detected"] = {
        "pass": bool(fsm_b.state == "FAULT" and fsm_b.diag["feedback_stuck_on"]
                     and t_stuck == 90.0 and not fsm_b.close_permit),
        "value": {"final_state": fsm_b.state, "t_stuck_detected_ms": t_stuck,
                  "diag": dict(fsm_b.diag),
                  "close_permit": bool(fsm_b.close_permit)},
        "note": "cmd OFF 后反馈恒 ON，N=50ms 超时触发 STUCK_CLOSED 并撤销闭合许可",
    }
    traces["stuck_closed"] = fsm_b.history

    # C: 去抖两例——短毛刺被滤除，长毛刺被采信
    deb_short = Debouncer(DEBOUNCE_MS, DT_MS)
    short_trace = []
    for t in np.arange(0.0, 21.0, DT_MS):
        raw = bool(5.0 <= t < 10.0)  # 5 采样 < 10 去抖步
        short_trace.append({"t_ms": float(t), "raw_fb": raw,
                            "debounced_fb": bool(deb_short.feed(raw))})
    deb_long = Debouncer(DEBOUNCE_MS, DT_MS)
    long_trace = []
    for t in np.arange(0.0, 21.0, DT_MS):
        raw = bool(5.0 <= t < 17.0)  # 12 采样 >= 10 去抖步
        long_trace.append({"t_ms": float(t), "raw_fb": raw,
                           "debounced_fb": bool(deb_long.feed(raw))})
    short_on = any(r["debounced_fb"] for r in short_trace)
    accepted_t = next((r["t_ms"] for r in long_trace if r["debounced_fb"]), None)
    checks["debounce_short_glitch_filtered"] = {
        "pass": bool(not short_on),
        "value": {"glitch_ms": 5.0, "debounce_ms": DEBOUNCE_MS,
                  "debounced_ever_on": bool(short_on)},
        "note": "毛刺 5ms < 去抖 10ms：去抖输出恒 OFF，被滤除",
    }
    checks["debounce_long_glitch_accepted"] = {
        "pass": bool(accepted_t == 14.0),
        "value": {"glitch_ms": 12.0, "debounce_ms": DEBOUNCE_MS,
                  "first_accepted_t_ms": accepted_t},
        "note": "毛刺 12ms >= 去抖 10ms：连续 10 采样后 t=14ms 被采信",
    }
    traces["debounce_short"] = short_trace
    traces["debounce_long"] = long_trace

    # D: 三分恢复——复用 B 的 FAULT 实例，逐步验证清旗/复位/重新许可
    before = fsm_b.snapshot()
    fsm_b.clear_diag()
    after_clear = fsm_b.snapshot()
    fsm_b.step(101.0, "ON", True)
    after_fault_close = fsm_b.snapshot()
    blocked_in_fault = fsm_b.history[-1]["event"]
    fsm_b.reset()
    after_reset = fsm_b.snapshot()
    fsm_b.step(102.0, "ON", False)
    after_reset_close = fsm_b.snapshot()
    blocked_after_reset = fsm_b.history[-1]["event"]
    fsm_b.repermit()
    after_repermit = fsm_b.snapshot()
    for t in np.arange(103.0, 121.0, DT_MS):
        fsm_b.step(float(t), "ON", t >= 103.0)
    final_reclose = fsm_b.snapshot()

    checks["clear_flag_clears_diag_only"] = {
        "pass": bool(not any(after_clear["diag"].values())
                     and after_clear["state"] == before["state"] == "FAULT"
                     and after_clear["close_permit"] == before["close_permit"]
                     and after_clear["close_permit"] is False),
        "value": {"before": before, "after_clear_diag": after_clear},
        "note": "清旗只清诊断记录：仍停留 FAULT、闭合许可仍撤销",
    }
    checks["fault_latches_close"] = {
        "pass": bool(after_fault_close["state"] == "FAULT"
                     and blocked_in_fault == "CLOSE_BLOCKED"
                     and fsm_b.counters["close_blocked"] >= 1),
        "value": {"state": after_fault_close["state"],
                  "event": blocked_in_fault,
                  "blocked_count": fsm_b.counters["close_blocked"]},
        "note": "FAULT 锁存期间 cmd ON 被阻断，不自动恢复",
    }
    checks["reset_returns_off_without_permission"] = {
        "pass": bool(after_reset["state"] == "OFF"
                     and after_reset["close_permit"] is False
                     and after_reset_close["state"] == "OFF"
                     and blocked_after_reset == "CLOSE_BLOCKED"),
        "value": {"after_reset": after_reset,
                  "after_close_attempt": after_reset_close,
                  "event": blocked_after_reset},
        "note": "复位回 OFF 但不给许可：紧接着 cmd ON 仍被阻断",
    }
    checks["repermit_restores_permission_only"] = {
        "pass": bool(after_repermit["close_permit"] is True
                     and after_repermit["state"] == "OFF"
                     and not any(after_repermit["diag"].values())),
        "value": {"after_repermit": after_repermit},
        "note": "重新许可只恢复许可位，状态保持 OFF、诊断记录不动",
    }
    checks["repermit_enables_reclose"] = {
        "pass": bool(final_reclose["state"] == "ON"
                     and not any(final_reclose["diag"].values())),
        "value": {"final_state": final_reclose["state"],
                  "diag": dict(final_reclose["diag"]),
                  "t_reclose_ms": _first_event(fsm_b.history, "FEEDBACK_ON_OK")},
        "note": "重新许可后 cmd ON 才真正走完 PRECHARGE→ON",
    }

    # E: 无独立反馈——反馈=命令属推定，物理粘连不可检出
    fsm_e = ContactorFSM(feedback_source="none")
    for t in np.arange(0.0, 101.0, DT_MS):
        cmd = "OFF" if t < 1.0 else ("ON" if t < 40.0 else "OFF")
        raw = True  # 物理触点实际粘连，但无独立反馈源观测不到
        fsm_e.step(float(t), cmd, raw)
    checks["no_feedback_cannot_prove_open"] = {
        "pass": bool(fsm_e.state == "OFF"
                     and not any(fsm_e.diag.values())
                     and fsm_e.counters["fault_feedback_stuck_on"] == 0),
        "value": {"final_state": fsm_e.state, "diag": dict(fsm_e.diag),
                  "physical_contact_stuck": True,
                  "stuck_faults_detected": fsm_e.counters["fault_feedback_stuck_on"]},
        "note": "无反馈源 feedback=currentSet 属推定：物理粘连未检出，命令!=反馈身份",
    }


    # F: 反馈缺失——命令 ON 后 N ms 内反馈未变 ON → FAULT
    fsm_f = ContactorFSM()
    for t in np.arange(0.0, 61.0, DT_MS):
        cmd = "ON" if t >= 1.0 else "OFF"
        fsm_f.step(float(t), cmd, False)  # 反馈始终不来
    t_missing = _first_event(fsm_f.history, "FEEDBACK_TIMEOUT")
    checks["missing_feedback_timeout_fault"] = {
        "pass": bool(fsm_f.state == "FAULT"
                     and fsm_f.diag["feedback_not_on"]
                     and t_missing == 1.0 + FEEDBACK_TIMEOUT_MS
                     and not fsm_f.close_permit),
        "value": {"final_state": fsm_f.state,
                  "t_timeout_ms": t_missing,
                  "timeout_ms": FEEDBACK_TIMEOUT_MS,
                  "diag": dict(fsm_f.diag),
                  "close_permit": bool(fsm_f.close_permit)},
        "note": "cmd ON 后反馈恒 OFF，t=51ms 达 N=50ms 超时 → FEEDBACK_TIMEOUT 故障",
    }
    traces["missing_feedback"] = fsm_f.history
    traces["stuck_recovery"] = fsm_b.history
    traces["no_feedback"] = fsm_e.history

    for name, fsm in (("normal_close", fsm_a), ("stuck_recovery", fsm_b),
                      ("no_feedback", fsm_e), ("missing_feedback", fsm_f)):
        counters[name] = dict(fsm.counters)
        transitions.extend({"scenario": name, **tr} for tr in fsm.transitions)
    return checks, traces, transitions, counters


def main():
    checks, traces, transitions, counters = run_scenarios()
    result = {
        "source_id": "OS07",
        "benchmark": "foxBMS 2 接触器 FSM 独立基准：命令/反馈身份、四态状态机、去抖与三分恢复",
        "model": {
            "provenance": "独立教学实现，未追踪 foxBMS 上游 FSM/去抖时序；"
                          "debounce_ms=10 与 feedback_timeout_ms=50 为教学参数，非 foxBMS 实测配置",
            "upstream_ref": "foxbms-2@73dbde670f7e（仅语义参照，常数不对应上游）",
            "states": ["OFF", "PRECHARGE", "ON", "FAULT"],
            "dt_ms": 1.0, "debounce_ms": 10.0, "feedback_timeout_ms": 50.0,
        },
        "python": platform.python_version(),
        "dt_ms": DT_MS,
        "debounce_ms": DEBOUNCE_MS,
        "feedback_timeout_ms": FEEDBACK_TIMEOUT_MS,
        "states": list(STATES),
        "checks": checks,
        "injected_fault_counts": counters,
        "state_transitions": transitions,
        "traces": traces,
    }
    result["all_pass"] = bool(all(bool(c["pass"]) for c in checks.values()))
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(json.dumps({
        "all_pass": result["all_pass"],
        "checks": {name: c["pass"] for name, c in checks.items()},
        "injected_fault_counts": counters,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
