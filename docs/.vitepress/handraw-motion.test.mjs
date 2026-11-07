/**
 * 手绘动画的挂载前置条件。
 *
 * 正文里照常写 `![]()`，播放 / 停止控件由 `pausable-handraw.ts` 在渲染期补上。
 * 那条规则只认「整段只有一张图」的段落：图片一旦和文字挤在同一段、或两张图连排，
 * 规则会**静默跳过**——页面照样构建、图照样能看，只是没有控件。
 *
 * 判定用 Markdown token 的**形状**（`pausable-handraw-rules.mjs`，与插件同一份），
 * 测试直接构造 token 覆盖各种写法，不依赖「相邻行长什么样」的启发式——那种写法
 * 漏掉了「图后紧跟文字」。真实阶段页由插件在构建期把关：遇到跳过的写法直接抛错
 * （`npm run docs:build` 会红），这里再用正则核一遍静态首帧与总数。
 */
import assert from 'node:assert/strict'
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import { planPausableImages } from './pausable-handraw-rules.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const stagesDir = path.resolve(here, '../stages')
const exportsDir = path.resolve(here, '../circuits/handraw/exports')
const EMBED = /!\[[^\]]*\]\(\.\.\/circuits\/handraw\/exports\/([a-z0-9-]+)\.webp\)/g

function stagePages() {
  return readdirSync(stagesDir)
    .filter((name) => name.endsWith('.md'))
    .map((name) => path.join(stagesDir, name))
}

/** 构造一个 image token；只实现判定函数用到的接口。 */
function image(src, alt = '示意') {
  return { type: 'image', content: alt, map: [0, 0], attrGet: (key) => (key === 'src' ? src : null) }
}

function text(content) {
  return { type: 'text', content, map: [0, 0], attrGet: () => null }
}

/** 把「段落里的子项」拼成 markdown-it 的块级形状。 */
function paragraph(...children) {
  return [
    { type: 'paragraph_open', map: [0, 1] },
    { type: 'inline', map: [0, 1], children, content: '{inline}' },
    { type: 'paragraph_close', map: [0, 1] }
  ]
}

const ANIM = '../circuits/handraw/exports/thermal-runaway.webp'

test('静态首末帧保持原图，不被误认成需要二次播放的动画', () => {
  for (const suffix of ['start', 'end']) {
    const frame = ANIM.replace('.webp', `-${suffix}.webp`)
    assert.deepEqual(planPausableImages(paragraph(image(frame))), { blocks: [], skipped: [] })
    assert.deepEqual(planPausableImages(paragraph(text('静态说明'), image(frame))), { blocks: [], skipped: [] })
  }
})

test('独占一段的图会被接管', () => {
  const { blocks, skipped } = planPausableImages(paragraph(image(ANIM)))
  assert.deepEqual(skipped, [])
  assert.equal(blocks.length, 1)
  assert.equal(blocks[0].slug, 'thermal-runaway')
  assert.equal(blocks[0].line, 1)
})

test('图后紧跟文字会被判定为跳过（相邻行启发式漏掉的写法）', () => {
  const { blocks, skipped } = planPausableImages(paragraph(image(ANIM), text('普通文字')))
  assert.equal(blocks.length, 0)
  assert.equal(skipped.length, 1)
  assert.match(skipped[0].why, /同一段里还有/)
})

test('两张图连排会被判定为跳过', () => {
  const { blocks, skipped } = planPausableImages(paragraph(image(ANIM), image(ANIM)))
  assert.equal(blocks.length, 0)
  assert.equal(skipped.length, 2)
})

test('行内插图（前后都有文字）会被判定为跳过', () => {
  const { blocks, skipped } = planPausableImages(
    paragraph(text('前面说话'), image(ANIM), text('后面说话'))
  )
  assert.equal(blocks.length, 0)
  assert.equal(skipped.length, 1)
  assert.match(skipped[0].why, /同一段里还有 2 个其它子项/)
})

test('不在段落里的图（例如混进别的块）会被判定为跳过', () => {
  const { blocks, skipped } = planPausableImages([image(ANIM)])
  assert.equal(blocks.length, 0)
  assert.equal(skipped.length, 1)
  assert.match(skipped[0].why, /不在独立段落/)
})

test('带 title 的写法仍按 src 识别，不因此漏判', () => {
  const withTitle = image(ANIM)
  withTitle.attrGet = (key) => (key === 'src' ? ANIM : key === 'title' ? '标题' : null)
  const { blocks, skipped } = planPausableImages(paragraph(withTitle))
  assert.deepEqual(skipped, [])
  assert.equal(blocks.length, 1)
})

test('阶段页引用的每张手绘动画都有 -start 静态首帧', () => {
  const missing = new Set()
  for (const file of stagePages()) {
    for (const match of readFileSync(file, 'utf8').matchAll(EMBED)) {
      if (!existsSync(path.join(exportsDir, `${match[1]}-start.webp`))) {
        missing.add(`${match[1]}-start.webp`)
      }
    }
  }
  assert.deepEqual([...missing], [], `缺静态首帧：${[...missing].join('、')}`)
})

test('阶段页至少有一批手绘动画（防止规则被整体绕过）', () => {
  const count = stagePages().reduce(
    (sum, file) => sum + [...readFileSync(file, 'utf8').matchAll(EMBED)].length,
    0
  )
  assert.ok(count >= 40, `阶段页手绘动画只剩 ${count} 处，规则是不是失效了？`)
})
