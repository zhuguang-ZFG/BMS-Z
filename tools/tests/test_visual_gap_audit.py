"""Coverage counts must describe images readers see, including lazy HTML photos."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import visual_gap_audit as audit  # noqa: E402


def test_lazy_photo_interrupts_prose_and_is_not_double_counted_in_figure(tmp_path):
    page = tmp_path / "stage-0-主线-电池.md"
    page.write_text(
        "# 认电池\n\n" + "先看外壳。" * 30
        + '\n<img loading="lazy" src="cell.jpg" width="600" height="400" alt="圆柱电芯">\n'
        + "再看接线。" * 30
        + '\n<figure><img src="board.jpg" alt="保护板"><figcaption>板上端子</figcaption></figure>\n',
        encoding="utf-8",
    )
    result = audit.audit_stage(page, gap_limit=180)
    assert result.figures == 2
    assert result.max_evidence_gap < 180
    assert not result.flags


def test_quotas_ignore_links_code_missing_files_and_reused_stills(tmp_path):
    def put(name, content):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    put("docs/教材彻底改造SPEC.md", (ROOT / "docs/教材彻底改造SPEC.md").read_text(encoding="utf-8"))
    put("docs/circuits/handraw/manifest.json", json.dumps({"entries": [{"slug": "cause", "status": "archived"}]}))
    put("docs/circuits/handraw/exports/cause.webp", "animation, validated by the manifest gate")
    put("docs/circuits/handraw/exports/cause-start.webp", "static")
    put("docs/circuits/handraw/exports/cause-end.webp", "static")
    put("docs/circuits/assets/photos/PHOTOS.md", "`cell.jpg`\n`linked.jpg`\n`example.jpg`\n`ovms-dashboard.jpg`\n"
        "`libresolar-bms-c1.jpg`\n`libresolar-sampling-connector.jpg`")
    for name in ("cell.jpg", "linked.jpg", "example.jpg", "ovms-dashboard.jpg",
                 "libresolar-bms-c1.jpg", "libresolar-sampling-connector.jpg"):
        put(f"docs/circuits/assets/photos/{name}", "licensed visual asset")
    put("docs/circuits/assets/moving.svg", '<svg><animate attributeName="x"/></svg>')
    put("docs/circuits/assets/cause.svg", '<svg><animate attributeName="x"/></svg>')
    put("docs/stages/assets/s0-mechanism.svg", "<svg/>")
    first = put("docs/stages/stage-0-主线-电池.md", '''# 认物
![实物](../circuits/assets/photos/cell.jpg)
[普通链接](../circuits/assets/photos/linked.jpg)
![不存在](../circuits/assets/photos/missing.jpg)
![屏幕截屏](../circuits/assets/photos/ovms-dashboard.jpg)
![外链](https://example.org/cell.jpg)
![全板](../circuits/assets/photos/libresolar-bms-c1.jpg)
![同图裁剪](../circuits/assets/photos/libresolar-sampling-connector.jpg)
```html
<img src="../circuits/assets/photos/example.jpg">
```
<img loading="lazy" src="../circuits/handraw/exports/cause.webp">
![首帧](../circuits/handraw/exports/cause-start.webp)
![末帧](../circuits/handraw/exports/cause-end.webp)
![动态](../circuits/assets/moving.svg)
![迁移中同源](../circuits/assets/cause.svg)
![机制](assets/s0-mechanism.svg)
''')
    second = put("docs/stages/stage-0-主线-电量.md", first.read_text(encoding="utf-8"))
    result = audit.stage_quota_report([first, second], tmp_path)[0]
    assert result["pages"] == 2
    assert result["photos"] == 2
    assert result["animations"] == 2
    assert result["mechanisms"] == 2
    assert "animations" in result["flags"]
