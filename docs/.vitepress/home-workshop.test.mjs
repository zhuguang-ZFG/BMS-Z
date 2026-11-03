import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const component = readFileSync(path.join(root, 'theme', 'VoltageNotebook.vue'), 'utf8')
const home = readFileSync(path.join(root, 'theme', 'HomeWorkshop.vue'), 'utf8')
const styles = readFileSync(path.join(root, 'theme', 'home.css'), 'utf8')

test('带载时电流点沿完整回路运动，0 A 时由状态类停下', () => {
  assert.match(component, /'is-current-flowing': current > 0/)
  assert.match(component, /drawing-charge drawing-charge--outbound/)
  assert.match(component, /drawing-charge drawing-charge--return/)
  assert.match(styles, /notebook-current-outbound 1\.4s linear infinite/)
  assert.match(styles, /notebook-current-return 1\.4s \.7s linear infinite/)
})

test('电流动画遵守系统的减少动态效果设置', () => {
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)/)
  assert.match(styles, /\.voltage-notebook\.is-current-flowing \.drawing-charge \{ animation: none; opacity: 0; \}/)
})

test('首页第一屏只有三个入口：零基础开始 / 按目标选路线 / 查一个问题', () => {
  assert.match(home, /零基础：从第 0 天开始/)
  assert.match(home, /pageLink\('\/stages\/getting-started'\)/)
  assert.match(home, /按目标选路线/)
  assert.match(home, /pageLink\('\/stages\/按目标选路线'\)/)
  assert.match(home, /查一个问题/)
  assert.match(home, /pageLink\('\/核心问题地图'\)/)
})

test('新读者从首页到第一课不超过三次点击', () => {
  // 首页 → 前两周页（1 次点击）→ 阶段 0 主线第一课（2 次点击）。
  const started = readFileSync(path.join(root, '..', 'stages', 'getting-started.md'), 'utf8')
  const match = started.match(/\[阶段 0 主线：电芯与保护\]\(([^)]+)\)/)
  assert.ok(match, '前两周页必须直接链到阶段 0 主线第一课')
  const lesson = path.resolve(path.join(root, '..', 'stages'), match[1])
  assert.ok(existsSync(lesson), `第一课页面不存在：${match[1]}`)
})
