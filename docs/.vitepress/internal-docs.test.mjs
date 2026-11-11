import assert from 'node:assert/strict'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { INTERNAL_DOC_GLOBS, isInternalDoc } from './internal-docs.mjs'

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

function markdownFiles(dir) {
  if (!existsSync(dir)) return []
  let entries
  try {
    entries = readdirSync(dir, { withFileTypes: true })
  } catch {
    return [] // .vitepress/dist 这类本机构建产物可能不可读，不在口径内
  }
  return entries.flatMap((entry) => {
    if (entry.name === '.vitepress') return []
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) return markdownFiles(full)
    return entry.name.endsWith('.md') ? [full] : []
  })
}

test('内部文档名单同时覆盖目录与整文件两类', () => {
  for (const rel of ['circuits/handraw/README.md', 'superpowers/plans/x.md', 'visual-style-pack.md']) {
    assert.ok(isInternalDoc(rel), `${rel} 应被排除`)
  }
  for (const rel of ['circuits/动画画风规范.md', 'stages/stage-1-认识BMS.md', '维护说明.md']) {
    assert.ok(!isInternalDoc(rel), `${rel} 是读者页，不该被排除`)
  }
})

test('内部文档都带 search: false（检索门按源码树逐篇核对）', () => {
  const inside = markdownFiles(docsDir)
    .map((file) => path.relative(docsDir, file).split(path.sep).join('/'))
    .filter((rel) => isInternalDoc(rel))
  assert.ok(inside.length >= INTERNAL_DOC_GLOBS.length, '内部文档一篇都没扫到，路径口径写错了')
  for (const rel of inside) {
    const head = readFileSync(path.join(docsDir, rel), 'utf8').slice(0, 2000)
    assert.match(head, /^search:\s*false\s*$/m, `${rel} 缺 search: false，检索门会判它没进索引`)
  }
})

test('维护说明仍发布但不进搜索索引（索引预算）', () => {
  const rel = '维护说明.md'
  assert.ok(!isInternalDoc(rel), `${rel} 是读者页，不该被排除`)
  const head = readFileSync(path.join(docsDir, rel), 'utf8').slice(0, 2000)
  assert.match(head, /^search:\s*false\s*$/m, `${rel} 缺 search: false，会挤占本地搜索索引预算`)
})

// P2.4 索引构成审计（2026-11-08）：检索服务学习正文。治理/工具/社区机制页仍发布、
// 可导航，但不再进本地索引——它们是导航或流程页，不是可被检索的教学正文。
// 深研学习页禁止通过这条路过门：装配后必须进自己的分片索引（见 P2.5/P2.6 验收）。
//
// 2026-11-10 教学/治理边界复审：练习剧本、仿真题、工具与器材目录、有独立正文的
// 读者工具页属于学习面，不能只因为体积大就留在治理页一侧。判据是读者能不能从这
// 一页学或练到正文里别处没有的东西；纯历史、规范、推广、贡献机制与试读工具仍退出。
const LEARNING_PAGES = [
  'AI陪练卡.md',
  'budget.md',
  '工具箱.md',
  '擂台.md',
  't13-包级手册缺口.md',
  'obsidian.md',
]

const NON_TEACHING_PAGES = [
  '更新动态.md',
  'AI陪练速查卡.md',
  '项目改造计划.md',
  '教学设计规范.md',
  '传播材料.md',
  '作品墙.md',
  '共建任务板.md',
  '陌生读者试读记录.md',
  '陌生读者试读任务.md',
]

test('学习与练习页必须进搜索索引（P2.4 教学/治理边界复审）', () => {
  for (const rel of LEARNING_PAGES) {
    assert.ok(!isInternalDoc(rel), `${rel} 仍应发布，不该被排除出构建`)
    const head = readFileSync(path.join(docsDir, rel), 'utf8').slice(0, 2000)
    assert.doesNotMatch(head, /^search:\s*false\s*$/m, `${rel} 是学习/练习页，不能靠 search: false 退出索引`)
  }
})

test('非教学页仍发布但不进搜索索引（P2.4 索引构成审计）', () => {
  for (const rel of NON_TEACHING_PAGES) {
    assert.ok(!isInternalDoc(rel), `${rel} 仍应发布，不该被排除出构建`)
    const head = readFileSync(path.join(docsDir, rel), 'utf8').slice(0, 2000)
    assert.match(head, /^search:\s*false\s*$/m, `${rel} 缺 search: false，会挤占本地搜索索引预算`)
  }
})
