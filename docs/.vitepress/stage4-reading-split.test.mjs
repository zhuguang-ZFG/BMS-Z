import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import {
  buildStage4Pages,
  extractSegment,
  readingSegments,
} from './prepare-stage4.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-4-SOC-SOH算法.md'), 'utf8')
const pages = buildStage4Pages(source)

test('阶段 4 的十四段正文各进入一个阅读页', () => {
  for (const [name, range] of Object.entries(readingSegments)) {
    const segment = extractSegment(source, range)
    const owners = pages.filter((page) => page.content.includes(segment))
    assert.equal(owners.length, 1, `${name} 应有且只有一个阅读页`)
  }
})

test('阶段 4 三篇主线都低于 1.5 万字符', () => {
  const mainPages = pages.filter((page) => page.file.includes('主线'))
  assert.equal(mainPages.length, 3)
  for (const page of mainPages) assert.ok(page.content.length < 15000, page.file)
})

test('SOC 主线只走安时积分与 OCV 校正', () => {
  const page = pages.find((item) => item.file === 'stage-4-主线-SOC估算.md')
  assert.match(page.content, /4\.2 安时积分/)
  assert.match(page.content, /4\.3 OCV 校正/)
  assert.doesNotMatch(page.content, /4\.4 等效电路/)
  assert.doesNotMatch(page.content, /4\.6 SOH/)
})

test('模型主线保留等效电路和卡尔曼，不混入在线辨识', () => {
  const page = pages.find((item) => item.file === 'stage-4-主线-模型与校正.md')
  assert.match(page.content, /4\.4 等效电路/)
  assert.match(page.content, /4\.5 卡尔曼滤波/)
  assert.doesNotMatch(page.content, /4\.4b 在线辨识/)
})

test('SOH/SOP 主线以动手任务和验收收尾', () => {
  const page = pages.find((item) => item.file === 'stage-4-主线-SOH与SOP.md')
  for (const text of ['4.6 SOH', '4.7 SOP', '4.10 动手任务', '4.11 验收清单']) {
    assert.match(page.content, new RegExp(text.replace('.', '\\.')))
  }
  assert.doesNotMatch(page.content, /4\.7b 充电地图/)
  assert.doesNotMatch(page.content, /4\.9 自测题/)
})
