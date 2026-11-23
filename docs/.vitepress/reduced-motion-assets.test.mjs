import assert from 'node:assert/strict'
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  REDUCED_MOTION_ASSETS,
  reducedMotionImageRenderer,
  withoutSvgMotion,
  writeReducedMotionAssets,
} from './reduced-motion-assets.mjs'

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const circuitAssets = path.join(docsDir, 'circuits', 'assets')
const viewportStyles = readFileSync(path.join(docsDir, '.vitepress', 'theme', 'custom.css'), 'utf8')

function imageRule(tokens, index) {
  const token = tokens[index]
  return `<img src="${token.attrGet('src')}" width="800" height="650" loading="lazy">`
}

function renderImage(source, base = '/BMS-Z/') {
  const md = { renderer: { rules: { image: imageRule } } }
  reducedMotionImageRenderer(md, base)
  const token = { attrGet: (name) => (name === 'src' ? source : null) }
  return md.renderer.rules.image([token], 0, {}, {}, md.renderer)
}

test('supported circuit images receive a reduced-motion source', () => {
  const html = renderImage('../circuits/assets/cc-cv.svg')
  assert.match(html, /^<picture\b/)
  assert.match(html, /role="region" tabindex="0" aria-label=/)
  assert.match(html, /class="bms-motion-diagram"[^>]*style="--bms-motion-width: 800px"/)
  assert.match(html, /:srcset="'\/BMS-Z\/circuits\/reduced-motion\/cc-cv\.reduce\.svg'"/)
  assert.match(html, /media="\(prefers-reduced-motion: reduce\)"/)
  assert.match(html, /<img src="\.\.\/circuits\/assets\/cc-cv\.svg" width="800" height="650" loading="lazy">/)

  assert.match(renderImage('assets/precharge.svg'), /precharge\.reduce\.svg/)
  assert.match(renderImage('assets/passive-balancing.svg'), /passive-balancing\.reduce\.svg/)
  assert.match(renderImage('assets/active-balancing.svg', '/'), /:srcset="'\/circuits\/reduced-motion\/active-balancing\.reduce\.svg'"/)
  assert.equal(renderImage('assets/other.svg'), imageRule([{ attrGet: () => 'assets/other.svg' }], 0))
  assert.equal(renderImage('https://example.test/cc-cv.svg'), imageRule([{ attrGet: () => 'https://example.test/cc-cv.svg' }], 0))
})

test('static SVG generation strips SMIL and keeps the full static teaching layer', () => {
  const temporary = mkdtempSync(path.join(os.tmpdir(), 'bms-motion-'))
  const sourceDir = path.join(temporary, 'source')
  const publicDir = path.join(temporary, 'public')
  const outputDir = path.join(publicDir, 'circuits', 'reduced-motion')
  const playback = '<g class="playback"><path d="M0 0 L1 1"><animate attributeName="opacity" values="0;1"/></path></g>'
  const staticLayer = '<path class="static-curve" d="M2 2 L3 3"/><text>恒流 → 恒压 → 截止</text>'
  const source = `<svg xmlns="http://www.w3.org/2000/svg">${playback}${staticLayer}</svg>`

  try {
    mkdirSync(sourceDir, { recursive: true })
    for (const name of REDUCED_MOTION_ASSETS) writeFileSync(path.join(sourceDir, name), source)

    const generated = writeReducedMotionAssets(sourceDir, publicDir)
    assert.equal(generated.length, REDUCED_MOTION_ASSETS.length)
    const still = readFileSync(path.join(outputDir, 'cc-cv.reduce.svg'), 'utf8')
    assert.doesNotMatch(still, /<(?:animate|animateMotion|animateTransform|set|discard)\b/)
    assert.match(still, /class="playback" opacity="0"/)
    assert.match(still, /class="static-curve"/)
    assert.match(still, /恒流 → 恒压 → 截止/)
  } finally {
    rmSync(temporary, { recursive: true, force: true })
  }
})

test('the generated variants keep motion groups hidden and preserve each static teaching summary', () => {
  const temporary = mkdtempSync(path.join(os.tmpdir(), 'bms-motion-source-'))
  const sourceDir = path.join(temporary, 'source')
  const publicDir = path.join(temporary, 'public')
  const outputDir = path.join(publicDir, 'circuits', 'reduced-motion')
  const staticText = {
    'cc-cv.svg': ['① 恒流 CC', '② 恒压 CV', '③ 截止'],
    'precharge.svg': ['K1 断 · K2 断', '② 限流预充', '保持 K1 断开'],
    'passive-balancing.svg': ['② 闭合放热', '③ 停止泄放', '闭合时约 0.18 W'],
    'active-balancing.svg': ['① 高节 → 电感', '② 电感 → 低节', '切换到低节'],
  }

  try {
    mkdirSync(sourceDir, { recursive: true })
    cpSync(circuitAssets, sourceDir, { recursive: true })
    const generated = writeReducedMotionAssets(sourceDir, publicDir)
    assert.equal(generated.length, Object.keys(staticText).length)

    for (const [name, phrases] of Object.entries(staticText)) {
      const source = readFileSync(path.join(circuitAssets, name), 'utf8')
      const still = readFileSync(path.join(outputDir, name.replace(/\.svg$/, '.reduce.svg')), 'utf8')
      assert.doesNotMatch(still, /<(?:animate|animateMotion|animateTransform|set|discard)\b/, name)
      assert.match(still, /<g\b[^>]*class="playback"[^>]*opacity="0"/, name)
      for (const phrase of phrases) assert.ok(still.includes(phrase), `${name}: static summary lost ${phrase}`)
      assert.match(source, /<g\b[^>]*class="playback"/, name)
    }
  } finally {
    rmSync(temporary, { recursive: true, force: true })
  }
})

test('mobile motion images keep intrinsic width inside a keyboard-scrollable region', () => {
  assert.match(viewportStyles, /picture\.bms-motion-diagram\s*\{[^}]*overflow-x:\s*auto/s)
  assert.match(viewportStyles, /picture\.bms-motion-diagram:focus-visible\s*\{[^}]*outline:/s)
  assert.match(viewportStyles, /@media\s*\(max-width:\s*767px\)[\s\S]*?picture\.bms-motion-diagram\s*>\s*img\s*\{[^}]*width:\s*var\(--bms-motion-width\)[^}]*max-width:\s*none/s)
  assert.match(viewportStyles, /picture\.bms-motion-diagram\s*>\s*img\s*\{[^}]*width:\s*min\(var\(--bms-motion-width\),\s*100%\)/s)
})

test('the live SVGs retain accessible titles and descriptions', () => {
  for (const name of REDUCED_MOTION_ASSETS) {
    const source = readFileSync(path.join(circuitAssets, name), 'utf8')
    const still = withoutSvgMotion(source)
    assert.match(source, /<title\b[^>]*>[^<]+<\/title>/, name)
    assert.match(source, /<desc\b[^>]*>[^<]+<\/desc>/, name)
    assert.ok(still.includes('<title'), `${name}: static source lost its title`)
  }
})
