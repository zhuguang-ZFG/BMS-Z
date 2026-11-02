import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import {
  buildStage5Pages,
  extractSegment,
  readingSegments,
} from './prepare-stage5.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const source = readFileSync(path.resolve(here, '../stages/stage-5-通信与集成.md'), 'utf8')
const pages = buildStage5Pages(source)

test('阶段 5 的十段正文各进入且只进入一个阅读页', () => {
  for (const [name, range] of Object.entries(readingSegments)) {
    const segment = extractSegment(source, range)
    const owners = pages.filter((page) => page.content.includes(segment))
    assert.equal(owners.length, 1, `${name} 应有且只有一个阅读页`)
  }
})

test('阶段 5 三篇主线都低于 1.5 万字符', () => {
  const mainPages = pages.filter((page) => page.file.includes('主线'))
  assert.equal(mainPages.length, 3)
  for (const page of mainPages) assert.ok(page.content.length < 15000, page.file)
})

test('串口主线只讲通信分层、UART 和 Modbus', () => {
  const page = pages.find((item) => item.file === 'stage-5-主线-串口与Modbus.md')
  for (const text of ['5.1 通信', '5.2 UART', '5.3 RS485']) {
    assert.match(page.content, new RegExp(text.replace('.', '\\.')))
  }
  assert.doesNotMatch(page.content, /5\.4 CAN/)
})

test('CAN 主线保留 DBC、GB/T 27930、SMBus 和 BLE', () => {
  const page = pages.find((item) => item.file === 'stage-5-主线-CAN与外部接口.md')
  for (const text of ['5.4 CAN', 'DBC', 'GB/T 27930', '5.5 SMBus', 'BLE']) {
    assert.match(page.content, new RegExp(text.replace('.', '\\.')))
  }
  assert.doesNotMatch(page.content, /5\.6 协议逆向/)
})

test('逆向主线包含安全、任务和验收，不混入完整自测', () => {
  const page = pages.find((item) => item.file === 'stage-5-主线-协议逆向与安全.md')
  for (const text of ['5.6 协议逆向', '5.6b 通信安全', '5.8 动手任务', '5.9 验收清单']) {
    assert.match(page.content, new RegExp(text.replace('.', '\\.')))
  }
  assert.doesNotMatch(page.content, /5\.7 自测题/)
})
