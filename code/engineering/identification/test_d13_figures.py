"""Check the plotted intervals and observations against the D13 report."""
import xml.etree.ElementTree as ET

import d13_ekf
import make_d13_figures as figures


def test_published_and_regenerated_markers_match_diagnostics():
    report = d13_ekf.build_report()
    sources = [(figures.OUT / figures.FILENAME).read_text(encoding="utf-8"),
               figures.diagnostic_figure(report)]
    for svg in sources:
        root = ET.fromstring(svg)
        assert root.findtext("{*}title") and root.findtext("{*}desc")
        labels = {node.text for node in root.findall(".//{*}text")}
        for sample in (report["whitening"], report["boundary"]["whitening"]):
            for key, value, within in (("nis", "nis_mean", "within_95"),
                                       ("ar1", "ar1", "ar1_within_limit")):
                prefix = f"{key}-{sample['n']}"
                point = root.find(f".//*[@id='{prefix}-point']//{{*}}use")
                ends = root.findall(f".//*[@id='{prefix}-band']//{{*}}use")
                assert point is not None and len(ends) == 2
                low, high = (float(cap.get("x")) for cap in ends)
                assert (low <= float(point.get("x")) <= high) == sample[within]
                assert f"{sample[value]:.4f}" in labels
