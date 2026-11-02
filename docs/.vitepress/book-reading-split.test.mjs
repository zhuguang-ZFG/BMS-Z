import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { splitBookReading, splitChapterFiles } from './book-reading-split.mjs'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')

function lineCounts(value) {
  const counts = new Map()
  for (const line of value.split(/\r?\n/).filter((item) => item.trim())) {
    counts.set(line, (counts.get(line) ?? 0) + 1)
  }
  return counts
}

for (const file of splitChapterFiles) {
  test(`${file} 拆分后不丢正文`, () => {
    const source = readFileSync(path.join(repoRoot, 'bms-book', 'book', file), 'utf8')
    const split = splitBookReading(file, source)
    const sourceLines = lineCounts(source)
    const outputLines = lineCounts(`${split.main}\n${split.deep}`)

    for (const [line, count] of sourceLines) {
      assert.ok((outputLines.get(line) ?? 0) >= count, `拆分后缺少：${line}`)
    }
    assert.match(split.main, /^# /)
    assert.match(split.deep, /^## /)
    assert.doesNotMatch(split.main, /^### 第二遍[：:]/m)
    if (/^### 第二遍[：:]/m.test(source)) assert.match(split.deep, /^### 第二遍[：:]/m)
  })
}

test('第 27 章主线不含矩阵推导', () => {
  const file = '27-EKF的六个矩阵.md'
  const source = readFileSync(path.join(repoRoot, 'bms-book', 'book', file), 'utf8')
  const split = splitBookReading(file, source)
  assert.doesNotMatch(split.main, /\\begin\{bmatrix\}|## 27\.2 |## 27\.5 |## 27\.6 /)
  assert.match(split.deep, /\\begin\{bmatrix\}/)
  assert.match(split.deep, /## 27\.2 /)
})

test('代码围栏里的标题不会触发拆分', () => {
  const source = '# 示例\n\n## 12.1 主线\n\n```text\n### 第二遍：只是示例\n```\n\n### 第二遍：真实选读\n\n推导\n'
  const split = splitBookReading('12-SOC三条路.md', source)
  assert.match(split.main, /```text\n### 第二遍：只是示例\n```/)
  assert.doesNotMatch(split.main, /### 第二遍：真实选读/)
  assert.match(split.deep, /### 第二遍：真实选读/)
})
