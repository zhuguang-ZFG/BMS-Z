import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const docs = path.join(repoRoot, 'docs')
const task = readFileSync(path.join(docs, '陌生读者试读任务.md'), 'utf8')
const host = readFileSync(path.join(docs, '陌生读者试读记录.md'), 'utf8')

test('读者页包含四项任务且不泄露判分答案', () => {
  for (const title of [
    '任务 1：解释一条采样链',
    '任务 2：手算粘连检查窗口',
    '任务 3：找出 HIL 证据缺口',
    '任务 4：自己找下一步',
  ]) assert.match(task, new RegExp(title))

  for (const leaked of ['约 362 V', '约 2.7 V', '照片中没有被测 BMS', '顺序扫描造成时间差']) {
    assert.doesNotMatch(task, new RegExp(leaked), `读者页泄露完成标准：${leaked}`)
  }
  assert.match(task, /不要接真电池/)
})

test('主持页保留完成标准、逐字记录和安全门槛', () => {
  for (const required of [
    '顺序扫描造成时间差',
    '0.1 s 后约 362 V',
    '照片中没有被测 BMS',
    '安全性错误出现一次',
    '首次答案原话',
    '提交 SHA 或版本号',
  ]) assert.match(host, new RegExp(required.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))
  assert.match(host, /本文不预填结果，也不接受模拟读者数据/)
})

test('试读指定的书章和小节仍然存在', () => {
  const cases = [
    ['06-AFE.md', ['## 6.1 ', '## 6.4 ']],
    ['08-硬件失效与二次保护.md', ['## 8.2 ', '## 8.3 ']],
    ['25-功能安全与量产.md', ['## 25.4 ', '## 25.5 ']],
  ]
  for (const [file, headings] of cases) {
    const source = readFileSync(path.join(repoRoot, 'bms-book', 'book', file), 'utf8')
    for (const heading of headings) assert.ok(source.includes(heading), `${file} 缺 ${heading.trim()}`)
  }

  for (const file of [
    'stage-2-主线-单节保护板.md',
    'stage-3-主线-AFE与采样.md',
    'stage-6-主线-高压与安全.md',
  ]) readFileSync(path.join(docs, 'stages', file), 'utf8')
})

test('完整讲义的主题页脚与手写主线路径一致', () => {
  const cases = [
    ['stage-0-前置知识.md', '/stages/getting-started', '/stages/stage-1-认识BMS'],
    ['stage-2-保护板实践.md', '/stages/stage-1-认识BMS', '/stages/stage-3-主线-AFE与采样'],
    ['stage-3-AFE-MCU智能BMS.md', '/stages/stage-2-主线-实测与验收', '/stages/stage-4-主线-SOC估算'],
    ['stage-4-SOC-SOH算法.md', '/stages/stage-3-主线-PCB调试与验收', '/stages/stage-5-主线-串口与Modbus'],
    ['stage-5-通信与集成.md', '/stages/stage-4-主线-SOH与SOP', '/stages/stage-6-主线-高压与安全'],
  ]
  for (const [file, prev, next] of cases) {
    const source = readFileSync(path.join(docs, 'stages', file), 'utf8')
    assert.match(source, new RegExp(`link: ${prev}`))
    assert.match(source, new RegExp(`link: ${next}`))
  }

  const finalStage = readFileSync(path.join(docs, 'stages', 'stage-6-精通与毕业项目.md'), 'utf8')
  assert.match(finalStage, /link: \/stages\/stage-5-主线-协议逆向与安全/)
  assert.match(finalStage, /next: false/)
})
