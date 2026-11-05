import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-7-BMS与AI.md'), 'utf8')

test('阶段 7 主线低于 1.5 万字符', () => {
  assert.ok(source.length < 15000, `stage-7-BMS与AI.md: ${source.length}`)
})

test('阶段 7 保留边界、证据、判定和探针任务链', () => {
  for (const text of ['三圈边界', '证据与印象', '谁签字', '五种失败模式', '最小签字记录', '选 **A**']) {
    assert.match(source, new RegExp(text.replaceAll('*', '\\*')))
  }
})

test('阶段 7 的四张机制图不堆叠', () => {
  // 机制动画在迁往 handraw/exports，两种位置都认（只数张数，不锁路径前缀）
  const figures = [...source.matchAll(/^!\[[^\]]+\]\(\.\.\/circuits\/(?:assets|handraw\/exports)\/ai-[^)]+\)$/gm)]
  assert.equal(figures.length, 4)

  for (let index = 1; index < figures.length; index += 1) {
    const previousEnd = figures[index - 1].index + figures[index - 1][0].length
    assert.ok(figures[index].index - previousEnd >= 400, `第 ${index}、${index + 1} 张图间距不足`)
  }
})

test('阶段 7 不恢复逐图模板说明', () => {
  assert.doesNotMatch(source, /看动画时盯住哪里|> \*\*图说\*\*/)
})
