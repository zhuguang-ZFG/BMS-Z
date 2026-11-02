import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import { buildStage3Pages, extractSegment, readingSegments } from './prepare-stage3.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-3-AFE-MCU智能BMS.md'), 'utf8')
const pages = buildStage3Pages(source)

test('阶段 3 的十段正文各进入且只进入一个阅读页', () => {
  for (const [name, range] of Object.entries(readingSegments)) assert.equal(pages.filter((page) => page.content.includes(extractSegment(source, range))).length, 1, name)
})
test('阶段 3 三篇主线都低于 1.5 万字符', () => {
  for (const page of pages.filter((item) => item.file.includes('主线'))) assert.ok(page.content.length < 15000, page.file)
})
test('AFE 主线保留扫描、CRC、时间预算和菊花链', () => {
  const page = pages.find((item) => item.file === 'stage-3-主线-AFE与采样.md')
  for (const term of ['MUX', 'CRC', '扫描时间预算', '隔离菊花链']) assert.match(page.content, new RegExp(term))
  assert.doesNotMatch(page.content, /3\.4 固件分层/)
})
test('固件主线保留状态机、锁存、看门狗和高低边开关', () => {
  const page = pages.find((item) => item.file === 'stage-3-主线-固件与功率开关.md')
  for (const term of ['状态机', '故障锁存', '看门狗', '高边与低边']) assert.match(page.content, new RegExp(term))
})
test('PCB 主线以任务和验收收尾，不混入完整自测', () => {
  const page = pages.find((item) => item.file === 'stage-3-主线-PCB调试与验收.md')
  for (const term of ['3.6 原理图', '3.7 调试', '3.9 动手任务', '3.10 验收清单']) assert.match(page.content, new RegExp(term.replace('.', '\\.')))
  assert.doesNotMatch(page.content, /3\.8 自测题/)
})
