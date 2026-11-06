/**
 * 手绘动画的挂载前置条件。
 *
 * 正文里照常写 `![]()`，播放 / 停止控件由 `pausable-handraw.ts` 在渲染期补上。
 * 那条规则只认「整段只有一张图」的段落：图片一旦和文字挤在同一行，规则会静默跳过，
 * 页面照样能构建、图照样能看，只是没有控件——没有门就发现不了。
 *
 * 这里守两件事：
 *   1. 阶段页里的每张手绘导出的 Markdown 图必须独占一行（否则挂不上控件）；
 *   2. 每个被引用的 slug 必须有 `-start.webp` 静态首帧（渲染期缺它会直接抛错，
 *      但等到构建才炸，报错离改动人太远）。
 */
import assert from 'node:assert/strict'
import { readdirSync, readFileSync, existsSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const stagesDir = path.resolve(here, '../stages')
const exportsDir = path.resolve(here, '../circuits/handraw/exports')

const EMBED = /!\[[^\]]*\]\(\.\.\/circuits\/handraw\/exports\/([a-z0-9-]+)\.webp\)/
const EMBED_ALL = new RegExp(EMBED.source, 'g')

function stagePages() {
  return readdirSync(stagesDir)
    .filter((name) => name.endsWith('.md'))
    .map((name) => path.join(stagesDir, name))
}

test('阶段页的手绘动画都独占一行，渲染期才挂得上播放控件', () => {
  const offenders = []
  for (const file of stagePages()) {
    const lines = readFileSync(file, 'utf8').split('\n')
    lines.forEach((line, index) => {
      const match = line.match(EMBED)
      if (match && line.trim() !== match[0]) {
        offenders.push(`${path.basename(file)}:${index + 1} 图与文字同段`)
      }
    })
  }
  assert.deepEqual(offenders, [], `这些图会静默失去播放控件：\n${offenders.join('\n')}`)
})

test('阶段页引用的每张手绘动画都有 -start 静态首帧', () => {
  const missing = new Set()
  for (const file of stagePages()) {
    for (const match of readFileSync(file, 'utf8').matchAll(EMBED_ALL)) {
      const start = path.join(exportsDir, `${match[1]}-start.webp`)
      if (!existsSync(start)) missing.add(`${match[1]}-start.webp`)
    }
  }
  assert.deepEqual([...missing], [], `缺静态首帧：${[...missing].join('、')}`)
})

test('阶段页至少有一处手绘动画（防止这条规则被整体绕过）', () => {
  const count = stagePages().reduce(
    (sum, file) => sum + [...readFileSync(file, 'utf8').matchAll(EMBED_ALL)].length,
    0
  )
  assert.ok(count >= 40, `阶段页手绘动画只剩 ${count} 处，规则是不是失效了？`)
})
