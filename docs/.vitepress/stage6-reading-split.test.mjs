import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import {
  buildStage6Pages,
  extractSegment,
  readingSegments,
} from './prepare-stage6.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-6-精通与毕业项目.md'), 'utf8')
const pages = buildStage6Pages(source)

test('阶段 6 的十一段正文各进入一个阅读页', () => {
  for (const [name, range] of Object.entries(readingSegments)) {
    const segment = extractSegment(source, range)
    const owners = pages.filter((page) => page.content.includes(segment))
    assert.equal(owners.length, 1, `${name} 应有且只有一个阅读页`)
  }
})

test('阶段 6 两篇主线都低于 1.5 万字符', () => {
  const mainPages = pages.filter((page) => page.file.includes('主线'))
  assert.equal(mainPages.length, 2)
  for (const page of mainPages) assert.ok(page.content.length < 15000, page.file)
})

test('高压主线不混入并簇、云端和法规旁支', () => {
  const page = pages.find((item) => item.file === 'stage-6-主线-高压与安全.md')
  assert.match(page.content, /6\.1\.2 预充回路/)
  assert.match(page.content, /6\.4\.1 过充案例/)
  assert.doesNotMatch(page.content, /6\.1\.5 并簇与环流/)
  assert.doesNotMatch(page.content, /6\.2\.6 云端诊断/)
  assert.doesNotMatch(page.content, /6\.5b 法规门槛/)
})

test('量产主线保留 DTC、标定、OTA、追溯和验收', () => {
  const page = pages.find((item) => item.file === 'stage-6-主线-量产与毕业.md')
  for (const text of ['故障管理（DTC 体系）', '参数与标定系统', 'Bootloader 与 OTA', '产线追溯', '毕业验收']) {
    assert.match(page.content, new RegExp(text))
  }
  assert.doesNotMatch(page.content, /6\.7 自测题/)
})
