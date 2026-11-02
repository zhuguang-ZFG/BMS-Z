import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import {
  buildStage2Pages,
  extractSegment,
  readingSegments,
} from './prepare-stage2.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-2-保护板实践.md'), 'utf8')
const pages = buildStage2Pages(source)

test('阶段 2 的九段正文各进入且只进入一个阅读页', () => {
  for (const [name, range] of Object.entries(readingSegments)) {
    const segment = extractSegment(source, range)
    const owners = pages.filter((page) => page.content.includes(segment))
    assert.equal(owners.length, 1, `${name} 应有且只有一个阅读页`)
  }
})

test('阶段 2 三篇主线都低于 1.5 万字符', () => {
  const mainPages = pages.filter((page) => page.file.includes('主线'))
  assert.equal(mainPages.length, 3)
  for (const page of mainPages) assert.ok(page.content.length < 15000, page.file)
})

test('单节主线只讲器件、电流路径和 DW01', () => {
  const page = pages.find((item) => item.file === 'stage-2-主线-单节保护板.md')
  assert.match(page.content, /2\.1 识别保护板器件与端子/)
  assert.match(page.content, /2\.2 DW01/)
  assert.doesNotMatch(page.content, /2\.3 多节保护/)
  assert.doesNotMatch(page.content, /2\.6 保护板实测/)
})

test('多节主线保留采样、MOS、NTC 和 ID', () => {
  const page = pages.find((item) => item.file === 'stage-2-主线-多节与接口.md')
  for (const text of ['2.3 多节保护', '2.4 MOS', '2.5 NTC']) {
    assert.match(page.content, new RegExp(text.replace('.', '\\.')))
  }
  assert.doesNotMatch(page.content, /2\.7 自测题/)
})

test('实测主线以动手任务和验收收尾，不混入完整自测', () => {
  const page = pages.find((item) => item.file === 'stage-2-主线-实测与验收.md')
  for (const text of ['2.6 保护板实测', '2.8 动手任务', '2.9 验收清单']) {
    assert.match(page.content, new RegExp(text.replace('.', '\\.')))
  }
  assert.doesNotMatch(page.content, /2\.7 自测题/)
})
