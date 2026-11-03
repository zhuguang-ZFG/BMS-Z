import assert from 'node:assert/strict'
import { existsSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import { loadLearningChecklists } from './learning-progress.mjs'
import { countCompletedChecklistItems } from './checklist.ts'

const docsDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const cells = loadLearningChecklists(docsDirectory, '/BMS-Z/')

test('七个主线阶段都指向实际有条目的验收清单', () => {
  assert.deepEqual(cells.map(cell => cell.index), ['00', '01', '02', '03', '04', '05', '06'])
  for (const cell of cells) {
    assert.ok(cell.total > 0, cell.name)
    assert.equal(cell.items.length, cell.total)
    assert.ok(cell.items.every(item => item.sources.length > 0), cell.name)
    const page = cell.link.replace('/BMS-Z/', '').split('#')[0].replace(/\.html$/, '.md')
    assert.ok(existsSync(path.join(docsDirectory, page)), page)
  }
  assert.equal(cells[6].page, 'bms-resources.md')
  assert.match(cells[6].link, /#精通自检清单$/)
})

test('拆分页与完整讲义的旧记录都能计入同一项验收', () => {
  const cell = cells.find(cell => cell.index === '02')
  const item = cell.items[0]
  const complete = item.sources.find(source => source.page === 'stages/stage-2-保护板实践.md')
  const split = item.sources.find(source => source.page === 'stages/stage-2-主线-实测与验收.md')
  assert.ok(complete)
  assert.ok(split)
  for (const source of [complete, split]) {
    assert.equal(countCompletedChecklistItems(cell.items, { [source.page]: { [source.key]: 1 } }), 1)
  }
  assert.equal(countCompletedChecklistItems(cell.items, {
    [complete.page]: { [complete.key]: 1 },
    [split.page]: { [split.key]: 1 },
  }), 1)
})

test('空记录、无关页和已失效条目不增加完成数', () => {
  const cell = cells[0]
  assert.equal(countCompletedChecklistItems(cell.items, {}), 0)
  assert.equal(countCompletedChecklistItems(cell.items, { 'other.md': { unknown: 1 } }), 0)
  assert.equal(countCompletedChecklistItems(cell.items, { [cell.page]: { unknown: 1 } }), 0)
})

test('所有有效条目都已勾选时恰好等于清单总数', () => {
  for (const cell of cells) {
    const store = {}
    for (const item of cell.items) {
      for (const source of item.sources) {
        store[source.page] ??= {}
        store[source.page][source.key] = 1
      }
    }
    assert.equal(countCompletedChecklistItems(cell.items, store), cell.total)
  }
})
