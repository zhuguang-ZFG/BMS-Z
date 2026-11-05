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
