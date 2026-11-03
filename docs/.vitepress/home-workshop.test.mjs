import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = path.dirname(fileURLToPath(import.meta.url))
const component = readFileSync(path.join(root, 'theme', 'VoltageNotebook.vue'), 'utf8')
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
