"""Freeze each reviewed SVG animation at a declared time for accessible print use.

Requires Playwright + Edge locally. The checked-in snapshots make reader builds
independent of browser automation. SVG nodes remain vector content in the PDF.
"""
from pathlib import Path
import json

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "bms-book"
entries = json.loads((BOOK / "visuals.json").read_text(encoding="utf-8"))
output = BOOK / "assets/print"
output.mkdir(exist_ok=True)
freeze = r"""(seconds) => {
  const svg = document.querySelector('svg');
  svg.pauseAnimations();
  svg.setCurrentTime(seconds);
  const animations = [...svg.querySelectorAll('animate, animateMotion, animateTransform, set')];
  const changes = [];
  for (const animation of animations) {
    const element = animation.parentElement;
    const attribute = animation.getAttribute('attributeName');
    if (animation.tagName === 'animateMotion' || animation.tagName === 'animateTransform') {
      const parent = element.parentElement;
      if (parent.getCTM && element.getCTM()) {
        const local = parent.getCTM().inverse().multiply(element.getCTM());
        changes.push([element, 'transform', `matrix(${local.a} ${local.b} ${local.c} ${local.d} ${local.e} ${local.f})`]);
      }
    } else if (attribute) {
      const property = element[attribute];
      const animated = property?.animVal;
      const value = animated?.value ?? (typeof animated === 'string' ? animated : null)
        ?? getComputedStyle(element).getPropertyValue(attribute);
      if (value !== '') changes.push([element, attribute, String(value)]);
    }
  }
  animations.forEach(animation => animation.remove());
  for (const [element, name, value] of changes) {
    element.setAttribute(name, value);
    if (['opacity','fill','stroke','stroke-dashoffset','stroke-dasharray'].includes(name)) {
      element.style.setProperty(name, value);
    }
  }
  // Explanatory rows in the top narrative panel must all be legible in print.
  svg.querySelectorAll('text').forEach(text => {
    const y = Number(text.getAttribute('y'));
    if (y < 0 || (y >= 60 && y <= 150 && Number(text.getAttribute('x')) === 40 && text.hasAttribute('opacity'))) {
      text.style.opacity = '1';
      text.setAttribute('opacity', '1');
    }
  });
  // Keep only one of any overlaid animated labels in a print snapshot.
  const groups = new Map();
  for (const text of svg.querySelectorAll('text[opacity]')) {
    if (Number(text.getAttribute('y')) < 0) continue;
    const key = `${text.parentElement.tagName}:${text.getAttribute('x')}:${text.getAttribute('y')}`;
    const group = groups.get(key) ?? [];
    group.push(text); groups.set(key, group);
  }
  for (const group of groups.values()) {
    if (group.length > 1) {
      const best = group.reduce((a,b) => Number(getComputedStyle(a).opacity) >= Number(getComputedStyle(b).opacity) ? a : b);
      group.forEach(text => { text.style.opacity = text === best ? '1' : '0'; text.setAttribute('opacity', text === best ? '1' : '0'); });
    }
  }
  svg.setAttribute('data-snapshot-time', String(seconds));
  return new XMLSerializer().serializeToString(svg);
}"""
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(color_scheme="light", viewport={"width": 1000, "height": 1100})
    for entry in entries:
        page.goto((ROOT / "docs/circuits/assets" / entry["file"]).as_uri(), wait_until="load")
        svg = page.evaluate(freeze, entry["time"])
        svg = "\n".join(line.rstrip() for line in svg.splitlines()) + "\n"
        (output / entry["file"]).write_text(svg, encoding="utf-8", newline="\n")
    browser.close()
print(f"prepared {len(entries)} vector snapshots")
