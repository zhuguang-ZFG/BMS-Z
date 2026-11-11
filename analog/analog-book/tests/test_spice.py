#!/usr/bin/env python3
"""SPICE 骨架：schema、测量解析、容差比较、真实运行与出图。"""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import plot_sim  # noqa: E402
import run_spice  # noqa: E402

REQUIRE = os.environ.get("BOOK_REQUIRE_NGSPICE") == "1"
NGSPICE = run_spice.find_ngspice()

# ngspice 42 默认不保存器件电流：`meas ... i(RL)` 会报 no such vector as i(rl)。
# 只有独立源支路电流（v*/i*）随时可取；器件电流要靠 @dev[i] + .option savecurrents。
REF_CURRENT = re.compile(r"(?<![\w.@])i\(\s*([A-Za-z_][\w.#]*)\s*\)", re.I)
DEV_CURRENT = re.compile(r"@([A-Za-z_][\w.#]*)\s*\[")


def _bad_current_refs(text: str) -> list[str]:
    return [name for name in REF_CURRENT.findall(text)
            if name[0].lower() not in "vi"]


def _tran_step(text: str) -> str | None:
    match = re.search(r"^\s*\.tran\s+(\S+)", text, re.M | re.I)
    return match.group(1) if match else None


class SchemaTests(unittest.TestCase):
    def test_discovers_simulation_cases(self):
        cases = {case.deck.name: case for case in run_spice.discover_cases()}
        self.assertEqual({"divider.cir", "rc.cir", "rectifier.cir",
                          "diffpair.cir", "pt100.cir", "probe.cir"}, set(cases))
        self.assertEqual({"vfinal", "vhalf", "trise"},
                         set(cases["rc.cir"].spec["metrics"]))
        self.assertEqual({"vout_open", "vout_load", "i_load"},
                         set(cases["divider.cir"].spec["metrics"]))
        self.assertEqual({"vavg", "vripple", "ipeak"},
                         set(cases["rectifier.cir"].spec["metrics"]))
        self.assertEqual({"vc1_0", "vc2_0", "vc1_cm", "vc2_cm"},
                         set(cases["diffpair.cir"].spec["metrics"]))
        self.assertEqual({"vout0", "vout50", "vout100"},
                         set(cases["pt100.cir"].spec["metrics"]))
        self.assertEqual({"vfinal1", "vfinal2", "trise1", "trise2"},
                         set(cases["probe.cir"].spec["metrics"]))

    def test_deck_has_no_external_models(self):
        text = (ROOT / "assets" / "spice" / "ch01" / "rc.cir").read_text(
            encoding="utf-8")
        self.assertIn(".control", text)
        self.assertIn("wrdata", text)
        self.assertNotIn(".include", text.lower())
        self.assertNotIn(".lib", text.lower())
        self.assertNotIn("http", text.lower())
        self.assertIn("PULSE(", text)

    def test_decks_never_ask_for_unstored_device_currents(self):
        """静态护栏：本地没装 ngspice 时 test_spice 整段 skip，这类错只会在 CI 暴露。"""
        self.assertEqual(["rl", "D1"],
                         _bad_current_refs("meas x find i(rl)\nprint i(D1)\n"))
        self.assertEqual([], _bad_current_refs("print i(vsense)\nlet k = i(v1)\n"))
        self.assertEqual([], _bad_current_refs("VPULSE in 0 PULSE(0 5 0 1n 1n 1m 2m)\n"),
                         "PULSE(...) 里的组合不能被当成电流引用")
        decks = sorted((ROOT / "assets" / "spice").glob("*/*.cir"))
        self.assertEqual(6, len(decks))
        for deck in decks:
            text = deck.read_text(encoding="utf-8")
            with self.subTest(deck=f"{deck.parent.name}/{deck.name}"):
                self.assertEqual([], _bad_current_refs(text),
                                 "改用 0V 检测源 i(v*) 或 @dev[i] + .option savecurrents")
                if DEV_CURRENT.search(text):
                    self.assertIn(".option savecurrents", text.lower())

    def test_tran_step_is_positive(self):
        text = (ROOT / "assets" / "spice" / "ch01" / "rc.cir").read_text(
            encoding="utf-8")
        step = _tran_step(text)
        self.assertIsNotNone(step, "deck 缺少 .tran 指令")
        number = re.match(r"([-+]?(?:\d+\.?\d*|\.\d+))", step)
        self.assertIsNotNone(number, "TSTEP 不是数值")
        self.assertGreater(float(number.group(1)), 0,
                           "TSTEP 必须大于 0，ngspice 拒绝 TSTEP=0")

    def test_tran_directive_is_case_insensitive(self):
        self.assertEqual("1u", _tran_step(".TRAN 1u 5m 0 1u\n"))

    def test_rejects_negative_tolerance(self):
        spec = json.loads(
            (ROOT / "assets" / "spice" / "ch01" / "assert.json").read_text(
                encoding="utf-8"))
        spec["metrics"]["vfinal"]["tolerance"] = -1
        with self.assertRaises(ValueError):
            run_spice.validate_spec(spec, Path("rc.cir"))

    def test_rejects_orphan_assertion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assert.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                run_spice.discover_cases(root)


class ParsingTests(unittest.TestCase):
    def test_parses_measurements_in_scientific_notation(self):
        text = """
vfinal = 5.000000e+00
vhalf = 7.034000e-05
trise = 2.197000e-04
"""
        values = run_spice.parse_measurements(text)
        self.assertAlmostEqual(5.0, values["vfinal"])
        self.assertAlmostEqual(70.34e-6, values["vhalf"])
        self.assertAlmostEqual(219.7e-6, values["trise"])

    def test_parser_ignores_the_from_at_suffix_of_avg_max_min(self):
        text = "vavg                =  8.250966e+00 from=  1.900000e+00 to=  2.000000e+00\n"
        self.assertAlmostEqual(8.250966, run_spice.parse_measurements(text)["vavg"])

    def test_compare_accepts_inside_tolerance(self):
        expected = {"vfinal": {"expected": 5.0, "tolerance": 0.02}}
        self.assertEqual([], run_spice.compare_metrics({"vfinal": 5.01}, expected))

    def test_compare_rejects_outside_tolerance_and_missing(self):
        expected = {"vfinal": {"expected": 5.0, "tolerance": 0.02}}
        self.assertTrue(run_spice.compare_metrics({"vfinal": 5.1}, expected))
        self.assertTrue(run_spice.compare_metrics({}, expected))

    def test_load_data_skips_header_and_requires_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rc.dat"
            path.write_text("time v(out)\n0 0\n1e-6 0.1\n2e-6 0.2\n",
                            encoding="utf-8")
            rows = run_spice.load_data(path, min_rows=3)
            self.assertEqual(3, len(rows))
            self.assertAlmostEqual(0.2, rows[-1][1])
            with self.assertRaises(ValueError):
                run_spice.load_data(path, min_rows=10)


class PlotTextTests(unittest.TestCase):
    def test_ascii_fallback_labels(self):
        labels = plot_sim.labels(False)
        self.assertEqual("Time / ms", labels["xlabel"])
        self.assertEqual("Simulation result", labels["default_title"])
        self.assertNotIn("时间", labels["note"])

    def test_cjk_labels(self):
        labels = plot_sim.labels(True)
        self.assertEqual("时间 / ms", labels["xlabel"])
        self.assertEqual("仿真结果", labels["default_title"])

    def test_chinese_title_falls_back_without_cjk_font(self):
        self.assertEqual("Simulation result",
                         plot_sim.safe_title("RC 一阶阶跃响应", False))
        self.assertEqual("RC 一阶阶跃响应",
                         plot_sim.safe_title("RC 一阶阶跃响应", True))

    def test_find_cjk_font_is_optional(self):
        name = plot_sim.find_cjk_font()
        self.assertTrue(name is None or isinstance(name, str))


@unittest.skipIf(NGSPICE is None and not REQUIRE,
                 "未安装 ngspice；设置 BOOK_REQUIRE_NGSPICE=1 可强制")
class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if NGSPICE is None:
            raise RuntimeError("BOOK_REQUIRE_NGSPICE=1 但找不到 ngspice")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.out = Path(cls.tmp.name)
        cls.cases = {case.deck.name: case for case in run_spice.discover_cases()}
        cls.results = {
            name: run_spice.run_case(case, NGSPICE,
                                     output_dir=cls.out / Path(name).stem)
            for name, case in cls.cases.items()}
        cls.case = cls.cases["rc.cir"]
        cls.result = cls.results["rc.cir"]

    def test_metrics_match_rc_theory(self):
        self.assertEqual([], self.result["problems"], self.result["log"])
        self.assertAlmostEqual(5.0, self.result["metrics"]["vfinal"], delta=0.02)
        self.assertAlmostEqual(69.3e-6, self.result["metrics"]["vhalf"],
                               delta=5e-6)
        self.assertAlmostEqual(219.7e-6, self.result["metrics"]["trise"],
                               delta=20e-6)

    def test_data_is_written_and_monotonic(self):
        path = self.out / "rc" / self.case.spec["data"]
        rows = run_spice.load_data(path, min_rows=200)
        self.assertGreaterEqual(len(rows), 200)
        self.assertTrue(all(b[0] > a[0] for a, b in zip(rows, rows[1:])))
        self.assertAlmostEqual(5.0, rows[-1][1], delta=0.03)

    def test_divider_metrics_match_theory(self):
        result = self.results["divider.cir"]
        self.assertEqual([], result["problems"], result["log"])
        self.assertAlmostEqual(6.0, result["metrics"]["vout_open"], delta=0.02)
        self.assertAlmostEqual(4.0, result["metrics"]["vout_load"], delta=0.02)
        self.assertAlmostEqual(0.0004, result["metrics"]["i_load"], delta=1e-5)

    def test_divider_data_is_written(self):
        case = self.cases["divider.cir"]
        path = self.out / "divider" / case.spec["data"]
        rows = run_spice.load_data(path, min_rows=200)
        self.assertGreaterEqual(len(rows), 200)
        self.assertAlmostEqual(6.0, rows[len(rows) // 4][1], delta=0.02)
        self.assertAlmostEqual(4.0, rows[-1][1], delta=0.02)

    def test_rectifier_metrics_match_filter_model(self):
        result = self.results["rectifier.cir"]
        self.assertEqual([], result["problems"], result["log"])
        self.assertAlmostEqual(8.0, result["metrics"]["vavg"], delta=0.6)
        self.assertAlmostEqual(0.4, result["metrics"]["vripple"], delta=0.2)
        self.assertAlmostEqual(0.55, result["metrics"]["ipeak"], delta=0.35)

    def test_rectifier_data_is_written(self):
        case = self.cases["rectifier.cir"]
        path = self.out / "rectifier" / case.spec["data"]
        rows = run_spice.load_data(path, min_rows=2000)
        self.assertGreaterEqual(len(rows), 2000)
        self.assertTrue(all(b[0] > a[0] for a, b in zip(rows, rows[1:])))

    def test_diffpair_metrics_match_dc_model(self):
        result = self.results["diffpair.cir"]
        self.assertEqual([], result["problems"], result["log"])
        self.assertAlmostEqual(6.81, result["metrics"]["vc1_0"], delta=0.08)
        self.assertAlmostEqual(7.19, result["metrics"]["vc2_0"], delta=0.08)
        self.assertAlmostEqual(6.805, result["metrics"]["vc1_cm"], delta=0.08)
        self.assertAlmostEqual(7.185, result["metrics"]["vc2_cm"], delta=0.08)

    def test_diffpair_data_is_written(self):
        case = self.cases["diffpair.cir"]
        path = self.out / "diffpair" / case.spec["data"]
        rows = run_spice.load_data(path, min_rows=50)
        self.assertGreaterEqual(len(rows), 50)

    def test_pt100_metrics_match_linear_rtd_model(self):
        result = self.results["pt100.cir"]
        self.assertEqual([], result["problems"], result["log"])
        self.assertAlmostEqual(8.0, result["metrics"]["vout0"], delta=0.15)
        self.assertAlmostEqual(8.77, result["metrics"]["vout50"], delta=0.15)
        self.assertAlmostEqual(9.54, result["metrics"]["vout100"], delta=0.15)

    def test_pt100_data_is_written(self):
        case = self.cases["pt100.cir"]
        path = self.out / "pt100" / case.spec["data"]
        rows = run_spice.load_data(path, min_rows=3)
        self.assertEqual(3, len(rows))
        self.assertAlmostEqual(8.0, rows[0][1], delta=0.15)

    def test_probe_metrics_match_probe_model(self):
        result = self.results["probe.cir"]
        self.assertEqual([], result["problems"], result["log"])
        self.assertAlmostEqual(0.909, result["metrics"]["vfinal1"], delta=0.01)
        self.assertAlmostEqual(0.990, result["metrics"]["vfinal2"], delta=0.01)
        self.assertAlmostEqual(20e-6, result["metrics"]["trise1"], delta=3e-6)
        self.assertAlmostEqual(2.2e-6, result["metrics"]["trise2"], delta=0.5e-6)

    def test_probe_data_is_written(self):
        case = self.cases["probe.cir"]
        path = self.out / "probe" / case.spec["data"]
        rows = run_spice.load_data(path, min_rows=200)
        self.assertGreaterEqual(len(rows), 200)
        self.assertAlmostEqual(0.909, rows[-1][1], delta=0.01)

    def test_plot_is_generated_from_simulation_data(self):
        path = self.out / "rc" / self.case.spec["data"]
        output = self.out / "rc-step.svg"
        plot_sim.plot(path, output, "RC 一阶阶跃响应")
        text = output.read_text(encoding="utf-8")
        self.assertIn("<svg", text)
        self.assertIn("ngspice", text)
        expected = plot_sim.safe_title(
            "RC 一阶阶跃响应", plot_sim.find_cjk_font() is not None)
        self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
