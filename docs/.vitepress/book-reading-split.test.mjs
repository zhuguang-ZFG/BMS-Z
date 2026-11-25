import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { splitBookReading, splitChapterFiles } from './book-reading-split.mjs'
import { readingRoutes } from './book-sources.mjs'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')

test('全部书稿图片在生成页面中使用站点可解析的路径', () => {
  for (const route of readingRoutes()) {
    for (const image of route.content.matchAll(/<img\b[^>]*>/g)) {
      const relative = image[0].match(/src="(\.\.?\/[^\"]+)"/)?.[1]
      if (relative) assert.ok(existsSync(path.resolve(repoRoot, 'docs/book', relative)),
        `${route.params.chapter} 图片相对路径不存在：${relative}`)
    }
  }
})

test('正文手绘进入站点后全部改写为可打包的资源路径', () => {
  const routes = readingRoutes()
  const figures = routes.flatMap((route) => [...route.content.matchAll(/<figure class="reading-sketch">([\s\S]*?)<\/figure>/g)])
  const manifest = JSON.parse(readFileSync(path.join(repoRoot, 'book', 'reading-sketches.json'), 'utf8'))
  assert.equal(figures.length, manifest.entries.filter((entry) => entry.chapter.startsWith('bms-book/')).length)
  for (const figure of figures) {
    assert.match(figure[1], /src="\.\.\/\.\.\/bms-book\/assets\/reading-sketches\//)
    assert.match(figure[1], /width="960" height="720"/)
    assert.doesNotMatch(figure[1], /src="\.\.\/assets\//)
  }
})

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
