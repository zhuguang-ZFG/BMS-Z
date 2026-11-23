"""Protect the visual meaning and generated source of the chapter 2 map."""

from pathlib import Path
import runpy
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "{http://www.w3.org/2000/svg}"


def test_six_jobs_map_matches_generator_and_has_six_distinct_roles():
    generator = runpy.run_path(str(ROOT / "generate_concept_figures.py"))
    generated = generator["fig_02_six_jobs"]().encode("utf-8")
    asset = ROOT / "assets/concepts/02-six-jobs-map.svg"
    assert asset.read_bytes() == generated, "Committed chapter 2 map is out of date"

    svg = ET.fromstring(generated)
    job_ids = [
        node.get("id")
        for node in svg.iter(SVG_NS + "g")
        if (node.get("id") or "").startswith("ch02-job-")
    ]
    assert job_ids == [
        "ch02-job-measure",
        "ch02-job-estimate",
        "ch02-job-protect",
        "ch02-job-coordinate",
        "ch02-job-communicate",
        "ch02-job-record",
    ]
    assert not any(node.tag == SVG_NS + "text" for node in svg.iter())

    all_ids = [node.get("id") for node in svg.iter() if node.get("id")]
    assert len(all_ids) == len(set(all_ids)), "SVG IDs must be unique"
    assert all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", value) for value in all_ids), (
        "SVG IDs must be XML names for EPUB readers"
    )
    description = svg.find(SVG_NS + "desc")
    assert description is not None
    assert "记录本" in "".join(description.itertext())
    assert "固定芯片划分" in "".join(description.itertext())
