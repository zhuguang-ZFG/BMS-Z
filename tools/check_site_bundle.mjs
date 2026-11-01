/**
 * Keep the deferred local-search index from hiding accidental page-bundle growth.
 *
 * Vite has one chunk-size threshold for everything. BMS-Z deliberately ships a
 * larger Chinese bigram search index, while ordinary route chunks should stay
 * much smaller. This post-build check gives the two asset classes separate
 * budgets and also catches MathJax SVGs that reference a missing glyph cache.
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'

const assetsDir = path.resolve(process.argv[2] || 'docs/.vitepress/dist/assets')
const PAGE_BUDGET = 850 * 1024
const SEARCH_BUDGET = 4800 * 1024

if (!existsSync(assetsDir)) {
  console.error(`站点资源目录不存在：${assetsDir}——先运行 npm run docs:build`)
  process.exit(1)
}

function walk(dir) {
  const files = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) files.push(...walk(full))
    else if (entry.isFile() && entry.name.endsWith('.js')) files.push(full)
  }
  return files
}

function formatKiB(bytes) {
  return `${(bytes / 1024).toFixed(1)} KiB`
}

const chunks = walk(assetsDir).map((file) => ({
  file,
  name: path.relative(assetsDir, file).replaceAll('\\', '/'),
  size: statSync(file).size,
}))

if (chunks.length === 0) {
  console.error(`站点资源目录里没有 JavaScript chunk：${assetsDir}`)
  process.exit(1)
}

const searchChunks = chunks.filter(({ name }) => path.basename(name).startsWith('@localSearchIndex'))
const pageChunks = chunks.filter(({ name }) => !path.basename(name).startsWith('@localSearchIndex'))
const failures = []

if (searchChunks.length === 0) failures.push('没有生成本地搜索索引 chunk')

for (const chunk of pageChunks) {
  if (chunk.size > PAGE_BUDGET) {
    failures.push(`${chunk.name} = ${formatKiB(chunk.size)}，超过普通 chunk 预算 ${formatKiB(PAGE_BUDGET)}`)
  }

  const source = readFileSync(chunk.file, 'utf8')
  if (source.includes('xlink:href:"#MJX-') && !source.includes('id:"MJX-')) {
    failures.push(`${chunk.name} 引用了 MathJax 字形，却没有随 chunk 携带字形定义`)
  }
}

for (const chunk of searchChunks) {
  if (chunk.size > SEARCH_BUDGET) {
    failures.push(`${chunk.name} = ${formatKiB(chunk.size)}，超过搜索索引预算 ${formatKiB(SEARCH_BUDGET)}`)
  }
}

const largestPage = pageChunks.toSorted((a, b) => b.size - a.size)[0]
const largestSearch = searchChunks.toSorted((a, b) => b.size - a.size)[0]

if (failures.length) {
  console.error('站点 bundle 预算失败：')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log(
  `bundle 预算通过：普通最大 ${largestPage?.name || '无'} ${formatKiB(largestPage?.size || 0)}` +
    `；搜索索引 ${largestSearch ? `${largestSearch.name} ${formatKiB(largestSearch.size)}` : '无'}`
)
