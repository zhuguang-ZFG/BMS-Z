#!/usr/bin/env node
/**
 * 检索门禁：正文里写了某个中文词，搜索框敲这个词就必须能翻到那一页。
 *
 * 为什么要单独一道闸：VitePress 本地搜索用 MiniSearch，默认只在空白和标点处切词。
 * 中文两字之间既没空格也没标点，整句会变成一个词条，于是「油箱」「体二极管」这类句中词
 * 一律搜不到。页面照旧能点开、内链照旧能对上，check_docs.py 与 check_pages.py 都看不出
 * 毛病——只有真人拿关键词去搜才发现搜索是半残的。
 *
 * 查四件事，全是构建期取证：
 * 1. 浏览器确实拿到了分词函数。VitePress 把 themeConfig 里函数的**源码**塞进每页站点数据
 *    （`_vp-fn_` 标记），客户端 new Function 还原；源码引用的模块级变量不会跟着过去，
 *    所以 cjk-search.ts 必须自包含。
 * 2. 还原出来的函数与模块实现逐条一致——不一致就是查询端和索引端切法分家。
 * 3. 每一页都进了索引（有正文没进索引，等于这一页在搜索里不存在）。
 * 4. 逐词对账。真值不是写死的期望条数，而是从 docs/ 正文现算：内容增减不会让门禁变红，
 *    只有搜索真的漏了才红。
 *
 * 用法：node .github/scripts/check_search.mjs [dist目录] [--base /BMS-Z/]
 */
import { readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { gzipSync } from 'node:zlib'

import MiniSearch from 'minisearch'

import { BASE as baseFromConfig } from '../../docs/.vitepress/base.ts'
import { tokenizeCjk } from '../../docs/.vitepress/cjk-search.ts'

const ROOT = path.resolve(import.meta.dirname, '..', '..')
const DOCS = path.join(ROOT, 'docs')

// 每个词都必须是正文里的**句中词**：只在标题开头出现的词，连默认切法都能靠前缀匹配侥幸
// 命中，那种用例证明不了分词有没有生效。加词就从页面正文里挑。
const TERMS = ['油箱', '体二极管', '均衡', '老化', '卡尔曼', '预充', '采样', '短路']

// 与 VitePress 客户端 VPLocalSearchBox.vue 的检索参数一致，那边改了这里要跟着改。
const SEARCH_OPTIONS = { fuzzy: 0.2, prefix: true, boost: { title: 4, text: 2, titles: 1 } }

const SAMPLES = [
  '零漂会把油箱慢慢加歪',
  'SOC += I * dt / Q 代码就一行',
  '背靠背 MOS 的体二极管还通着',
  '阶段 4 教程：SOC / SOH / SOP 估算算法',
  '箱',
]

const argv = process.argv.slice(2)
const baseIdx = argv.indexOf('--base')
const positional = argv.filter((a, i) => !a.startsWith('--') && i !== baseIdx && i !== baseIdx + 1)
const DIST = path.resolve(positional[0] || path.join(ROOT, 'docs/.vitepress/dist'))
// base 从 base.ts 取，不在这里再抄一份 /BMS-Z/：那一句漂了，站点数据和索引里的
// 段落 id 会一起漂，只有拿同一个源才对得上。--base 只为本机对着别的产物跑。
const BASE = baseIdx >= 0 ? argv[baseIdx + 1] : baseFromConfig

const failures = []
const fail = (message) => failures.push(message)

function walk(dir, match, out = []) {
  for (const name of readdirSync(dir)) {
    if (name === '.vitepress' || name === 'public') continue
    const full = path.join(dir, name)
    if (statSync(full).isDirectory()) walk(full, match, out)
    else if (match(name)) out.push(full)
  }
  return out
}

/** 索引产物：一个只导出 JSON 字符串的 chunk，文件名带构建哈希。 */
function readIndexChunk() {
  const chunks = path.join(DIST, 'assets', 'chunks')
  const file = readdirSync(chunks).find((f) => f.startsWith('@localSearchIndexroot'))
  if (!file) {
    fail('产物里没有本地搜索索引 chunk（themeConfig.search.provider 还是 local 吗？）')
    return null
  }
  const src = readFileSync(path.join(chunks, file), 'utf8')
  const m = src.match(/const t='([\s\S]*?)';export/)
  if (!m) fail(`看不懂索引 chunk 的格式：${file}`)
  // loadJSON 吃的是 JSON 文本本身，不要先 parse 成对象。
  return m ? { file, src, json: m[1] } : null
}

/**
 * 还原浏览器实际会用的分词函数，与 VitePress 的 deserializeFunctions 同一个动作：
 * 把 `_vp-fn_` 后面的源码取出来求值。
 */
function readClientTokenizers() {
  const html = readFileSync(path.join(DIST, 'index.html'), 'utf8')
  // 站点数据里带函数时，VitePress 写的是 deserializeFunctions(JSON.parse("…"))，
  // 不带函数时直接 JSON.parse("…")。两种都要认，并且字符串里有大量转义引号，
  // 正则啃不动——按 JS 字符串字面量的转义规则扫出这一段。
  const start = html.indexOf('window.__VP_SITE_DATA__=')
  if (start < 0) {
    fail('页面里找不到站点数据，无法验证查询端分词')
    return []
  }
  const open = html.indexOf('JSON.parse("', start)
  if (open < 0) {
    fail('站点数据里找不到 JSON.parse 段，无法验证查询端分词')
    return []
  }
  let i = open + 'JSON.parse('.length + 1
  let literal = ''
  while (i < html.length) {
    const ch = html[i]
    if (ch === '\\') { literal += ch + html[i + 1]; i += 2; continue }
    if (ch === '"') break
    literal += ch
    i++
  }

  // literal 还带着 JS 转义（\" \\ \uXXXX），先按 JSON 字符串解码一层得到站点数据原文，
  // 再解析成对象。
  const miniSearch = JSON.parse(JSON.parse(`"${literal}"`)).themeConfig?.search?.options?.miniSearch
  if (!miniSearch) {
    fail('站点数据里没有 themeConfig.search.options.miniSearch：分词函数根本没配到搜索上')
    return []
  }
  const found = []
  for (const [where, value] of [
    ['options.tokenize', miniSearch.options?.tokenize],
    ['searchOptions.tokenize', miniSearch.searchOptions?.tokenize],
  ]) {
    if (typeof value !== 'string' || !value.startsWith('_vp-fn_')) {
      fail(`search.options.miniSearch.${where} 不是函数：浏览器会用默认切法，和索引端的二元组对不上`)
      continue
    }
    try {
      found.push([where, new Function(`return ${value.slice('_vp-fn_'.length)}`)()])
    } catch (error) {
      fail(`${where} 在浏览器里还原失败：${error.message}（函数体必须自包含，不能引用模块级变量）`)
    }
  }
  return found
}

/**
 * markdown 里能被索引到的文字，按 VitePress 建索引的口径算：只算标题之后的段落（首个
 * 标题之前的「本篇你会学到」根本不进索引）；图片替代文字、链接地址、frontmatter、HTML
 * 注释都不算；公式渲染成 SVG，剥完标签不剩中文，所以也不算；标题下没内容的段落会被跳过。
 */
function searchableText(mdSource) {
  const body = mdSource
    .replace(/^---[\s\S]*?^---[ \t]*\r?\n/m, '')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/^\s*\$\$[\s\S]*?\$\$\s*$/gm, ' ')
    .replace(/\$[^$\n]+\$/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')

  const sections = []
  let current = null
  for (const line of body.split(/\r?\n/)) {
    if (/^#{1,6}\s/.test(line)) {
      if (current) sections.push(current)
      current = { lines: [] }
      continue
    }
    current?.lines.push(line)
  }
  if (current) sections.push(current)

  return sections
    .filter((s) => s.lines.join('').trim())
    .map((s) => s.lines.join(' '))
    .join(' ')
    .replace(/\s+/g, ' ')
}

/** 源文件到站点 URL：与 VitePress 的 getDocId 同规则（index.md 退成目录，其余换 .html）。 */
function pageUrlOf(mdFile) {
  const rel = path.relative(DOCS, mdFile).split(path.sep).join('/')
  return BASE + rel.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '.html')
}

const chunk = readIndexChunk()
if (!chunk) {
  console.error('FAIL: 检索门禁起不来——')
  for (const line of failures) console.error('  ' + line)
  process.exit(1)
}

const index = MiniSearch.loadJSON(chunk.json, {
  fields: ['title', 'titles', 'text'],
  storeFields: ['title', 'titles'],
  tokenize: tokenizeCjk,
})

// —— 1 + 2：浏览器那份副本必须和模块实现同切法 ——
const clients = readClientTokenizers()
for (const [where, fn] of clients) {
  for (const sample of SAMPLES) {
    const ours = tokenizeCjk(sample).join(' ')
    const browser = Array.isArray(fn(sample)) ? fn(sample).join(' ') : `<返回 ${fn(sample)}>`
    if (ours !== browser) fail(`${where} 与 cjk-search.ts 切法不一致：\n  模块: ${ours}\n  浏览器: ${browser}`)
  }
}

// —— 3：每页都进索引 ——
// 段落 id 形如 /BMS-Z/stages/stage-0-前置知识.html#锚点，取 # 前面当页面。
// 直接读序列化结果里的 documentIds，不去依赖 MiniSearch 的内部访问器。
const indexedPages = new Set(
  Object.values(JSON.parse(chunk.json).documentIds).map((id) => String(id).split('#')[0])
)
const markdowns = walk(DOCS, (n) => n.endsWith('.md'))
const searchableDocs = markdowns.filter((f) => !/^search:\s*false\s*$/m.test(readFileSync(f, 'utf8').slice(0, 2000)))
for (const md of searchableDocs) {
  const url = pageUrlOf(md)
  if (!indexedPages.has(url)) fail(`${path.relative(ROOT, md)} 没进搜索索引（URL ${url} 在索引里查不到）`)
}

// —— 4：逐词对账 ——
const rows = []
for (const term of TERMS) {
  const truth = new Set()
  for (const md of searchableDocs) {
    if (searchableText(readFileSync(md, 'utf8')).includes(term)) truth.add(pageUrlOf(md))
  }
  if (!truth.size) {
    fail(`真值表里的「${term}」在正文里一次都没出现：这条用例证明不了任何事，换一个句中词`)
    continue
  }
  const hits = new Set()
  for (const result of index.search(term, { ...SEARCH_OPTIONS, tokenize: tokenizeCjk })) {
    hits.add(String(result.id).split('#')[0])
  }
  const missing = [...truth].filter((page) => !hits.has(page))
  if (missing.length) {
    fail(`「${term}」正文里 ${truth.size} 页有，搜索只翻到 ${hits.size} 页，漏了：${missing.slice(0, 3).join('、')}`)
  }
  rows.push([term, truth.size, hits.size])
}

function report() {
  if (failures.length) {
    console.error(`FAIL: 检索门禁 ${failures.length} 处不过：`)
    for (const line of failures) console.error('  ' + line)
    process.exit(1)
  }
  const kb = (n) => `${(n / 1024).toFixed(0)}KB`
  console.log(`ok: 索引 ${chunk.file}，${index.documentCount} 个段落，${kb(Buffer.byteLength(chunk.src, 'utf8'))}（gzip ${kb(gzipSync(chunk.src, { level: 6 }).length)}）`)
  for (const [term, truth, hits] of rows) console.log(`  「${term}」正文 ${truth} 页 → 搜索命中 ${hits} 页`)
  console.log(`ok: 分词函数已随站点数据进浏览器，且与索引端一致；${searchableDocs.length} 篇全部在索引里`)
  process.exit(0)
}

report()
