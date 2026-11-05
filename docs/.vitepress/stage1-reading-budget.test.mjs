import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-1-认识BMS.md'), 'utf8')

test('阶段 1 主线低于 1.5 万字符', () => {
  assert.ok(source.length < 15000, `stage-1-认识BMS.md: ${source.length}`)
})

test('阶段 1 保留完整任务链和视觉证据', () => {
  for (const text of ['1.1 从一节电池', '1.4 五大保护', '1.7 保护决策逻辑', '1.8 均衡初步', '1.11 验收清单']) {
    assert.match(source, new RegExp(text.replace('.', '\\.')))
  }

  const localFigures = source.match(/!\[[^\]]+\]\(\.\.\/circuits\/(?:assets|handraw\/exports)\/[^)]+\)/g) ?? []
  assert.ok(localFigures.length >= 12, `本地视觉点只剩 ${localFigures.length} 个`)
  assert.match(source, /photos\/laptop-pack-internals\.jpg/)
})

test('阶段 1 不恢复已删除的模板提示', () => {
  assert.doesNotMatch(source, /练完你会怎样|看动画时盯住哪里/)
})
