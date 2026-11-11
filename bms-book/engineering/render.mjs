// 工程深研渲染器（P2.6）：只读登记过的正文源，用站点的 createMarkdownRenderer
// （含 mathjax3 离线数学）把 Markdown 渲染成 HTML 片段。自定义语义块
// （story/chapter-route，三到五冒号）在渲染前改成 <aside> 占位，与 bms-book/render.mjs
// 同一模式；格式不对直接抛错，不静默吞。输出 JSON 到 stdout，由 tools/build_engineering.py 装配。
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import path from 'node:path'
import process from 'node:process'
import { engineeringSearch } from './search.mjs'

import { createMarkdownRenderer } from 'vitepress'
import { BASE, SITE_ORIGIN } from '../../docs/.vitepress/base.ts'

function repoRoot() {
  try {
    const here = new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
    return path.resolve(path.dirname(here), '..', '..')
  } catch (error) {
    throw new Error(`工程装配：定位仓库根失败：${error.message}`)
  }
}

const ROOT = repoRoot()
const ENGINEERING = path.join(ROOT, 'bms-book/engineering')

function readJson(rel) {
  try {
    return JSON.parse(readFileSync(path.join(ROOT, rel), 'utf8'))
  } catch (error) {
    throw new Error(`工程装配：读不到或解析不了 ${rel}：${error.message}`)
  }
}

const manifest = readJson('bms-book/engineering/manifest.json')

const md = await createMarkdownRenderer(ENGINEERING, { math: true })
const routeKinds = { story: '现场', chapterRoute: '阅读路径' }

function renderChapterRoute(title, content) {
  const entries = content.trim().split(/\r?\n/).filter(Boolean).map((line) => {
    const match = line.match(/^- \*\*([^*]+)\*\*[：:]\s*(.+)$/)
    if (!match) throw new Error(`阅读路径格式错误：${line}`)
    return `<li><strong>${md.utils.escapeHtml(match[1])}</strong><span>${md.renderInline(match[2])}</span></li>`
  })
  if (entries.length !== 3) throw new Error(`阅读路径必须恰好三条：${content}`)
  return `<aside class="chapter-route" aria-label="阅读路径"><p class="chapter-route__eyebrow">${md.utils.escapeHtml(title || '阅读路径')}</p><ol>${entries.join('')}</ol></aside>`
}

function renderCallout(kind, title, content) {
  return `<aside class="callout ${kind}"><div class="callout-title">${md.utils.escapeHtml(title || routeKinds[kind])}</div>${md.render(content)}</aside>`
}

// 注册正文之间保留离线导航；代码和未装配内容明确回链到仓库真源。
const units = manifest.units.filter((u) => u.status === 'locally_verified' && u.source)
const sourceIds = new Map(units.map((u) => [path.resolve(ROOT, u.source), u.id.toLowerCase()]))
sourceIds.set(path.join(ROOT, 'bms-book/engineering-conventions.md'), 'conventions')
sourceIds.set(path.join(ENGINEERING, 'P1-先修最小包.md'), 'prerequisites')

function rewriteInternalLinks(html, sourcePath) {
  return html.replace(/(<a\b[^>]*\bhref=")([^"]+)(")/g, (_whole, start, href, end) => {
    if (/^(?:[a-z][a-z0-9+.-]*:|#|\/\/)/i.test(href)) return `${start}${href}${end}`
    const [file, fragment] = href.split('#', 2)
    let target = path.resolve(path.dirname(sourcePath), decodeURIComponent(file))
    if (target.endsWith('.html')) target = target.slice(0, -5) + '.md'
    const id = sourceIds.get(target)
    if (id) return `${start}${id}.html${fragment ? `#${fragment}` : ''}${end}`
    const relative = path.relative(ROOT, target).split(path.sep).join('/')
    if (relative.startsWith('../')) throw new Error(`工程装配：链接逃出仓库 ${href}`)
    const encoded = relative.split('/').map(encodeURIComponent).join('/')
    const url = relative.startsWith('docs/') && !relative.startsWith('docs/superpowers/')
      ? `${SITE_ORIGIN}${BASE}${encoded.slice(5).replace(/\.md$/, '.html')}`
      : `https://github.com/zhuguang-ZFG/BMS-Z/blob/main/${encoded}`
    return `${start}${url}${fragment ? `#${fragment}` : ''}${end}`
  })
}

function renderUnit(unit) {
  const sourcePath = path.join(ROOT, unit.source)
  const text = readFileSync(sourcePath, 'utf8')
  const callouts = []
  // 章节导读/现场容器：三到五冒号都认；内容里允许出现 ::: 代码围栏样文本。
  const routed = text.replace(
    /^:{3,5} (story)[ \t]*([^\n]*)\n([\s\S]*?)\n:{3,5}[ \t]*$/gm,
    (_whole, kind, title, content) => {
      callouts.push(renderCallout(kind, title, content))
      return `\n\n<!--CALLOUT:${callouts.length - 1}-->\n\n`
    },
  ).replace(
    /^:{3,5} chapter-route[ \t]*([^\n]*)\n([\s\S]*?)\n:{3,5}[ \t]*$/gm,
    (_whole, title, content) => {
      callouts.push(renderChapterRoute(title, content))
      return `\n\n<!--CALLOUT:${callouts.length - 1}-->\n\n`
    },
  )
  if (/^:{3,5}/m.test(routed)) {
    const line = routed.split(/\r?\n/).find((l) => /^:{3,5}/.test(l))
    throw new Error(`${unit.id}: 未识别的语义块容器：${line}`)
  }
  let html = md.render(routed)
  for (const [index, aside] of callouts.entries()) {
    html = html.replace(`<!--CALLOUT:${index}-->`, aside)
  }
  if (html.includes('<!--CALLOUT:')) throw new Error(`${unit.id}: 语义块占位没有全部还原`)
  html = rewriteInternalLinks(html, sourcePath)
  const headings = []
  const headingRe = /<h([1-6])[^>]*>(?:<a[^>]*>)?([\s\S]*?)(?:<\/a>)?<\/h\1>/g
  let match = headingRe.exec(html)
  while (match) {
    const text = match[2].replace(/<[^>]+>/g, '').trim()
    headings.push({ level: Number(match[1]), text })
    match = headingRe.exec(html)
  }
  const title = unit.title || (headings[0]?.text ?? unit.id)
  return { id: unit.id, title, html, headings }
}

const rendered = units.map(renderUnit)
rendered.push(renderUnit({ id: 'prerequisites', title: '先修最小包', source: 'bms-book/engineering/P1-先修最小包.md' }))

// 来源身份随三格式交付；静态审读不改成上游复现或器件许可。
const escape = (text) => md.utils.escapeHtml(String(text ?? ''))
const snapshot = readJson('docs/superpowers/plans/2026-11-08-bms-open-source-snapshot.json')
const sourceRows = snapshot.resources.map((source) => {
  const license = source.license.spdx || source.license.conclusion || source.license.software || source.license.license
  return `<tr><td>${escape(source.id)}</td><td>${escape(source.repository)}</td><td><code>${escape(source.full_commit_sha)}</code></td><td>${escape(license)}；${escape(source.execution_status)}</td></tr>`
}).join('')
const experiments = readJson('bms-book/engineering/experiments.json').experiments
const experimentRows = experiments.map((experiment) => {
  const script = readFileSync(path.join(ROOT, experiment.script))
  return `<h2 id="${experiment.id.toLowerCase()}">${escape(experiment.id)} · ${escape(experiment.unit)}</h2><p>入口：<code>${escape(experiment.script)}</code>；源指纹：<code>${createHash('sha256').update(script).digest('hex').slice(0, 16)}</code>。来源：${escape(experiment.source_ids.join(' / '))}。</p><p>${escape(experiment.acceptance)}</p>`
}).join('')
const adoptionPath = path.join(ROOT, 'docs/superpowers/plans/bms-depth/source-adoption.md')
const gaps = readFileSync(adoptionPath, 'utf8').split('## 专项缺口与阻塞范围')[1]
rendered.push({ id: 'sources', title: '来源、实验与未闭合证据', headings: [], html: `<h1>来源、实验与未闭合证据</h1><p>版本取自 ${escape(snapshot.sampled_date_local)} 的固定取样；read/source_review_only 不表示已运行上游或通过硬件验收。在线原文与代码链接需要联网，当前正文、图、参数和下面的来源身份随册离线保留。</p><h2 id="versions">已读取开源版本</h2><table><thead><tr><th>ID</th><th>仓库</th><th>提交</th><th>许可与状态</th></tr></thead><tbody>${sourceRows}</tbody></table><h2 id="data-education">数据与讲义</h2><p>DATA01：NASA RW3，DOI ${escape(snapshot.data_sources[0].doi)}，${escape(snapshot.data_sources[0].license)}；reference_soc 不是独立真值。EDU01：UCCS/Plett，原讲义开放再利用许可未建立，正文未重发讲义。CASE01：PyBaMM #5072 / #5205，仅已读历史修复，未复现原MWE。</p>${experimentRows}${md.render('## 专项缺口与阻塞范围' + gaps)}` })

// 工程约定（符号/时钟/数据口径合同）随册交付；样章里的相对回链在装配侧改指本页。
const conventionsPath = path.join(ROOT, 'bms-book/engineering-conventions.md')
try {
  const conventionsText = readFileSync(conventionsPath, 'utf8')
  const conventions = rewriteInternalLinks(md.render(conventionsText), conventionsPath)
  rendered.push({
    id: 'conventions',
    title: '工程深研约定（符号、时钟与数据口径）',
    html: conventions,
    headings: [],
  })
} catch (error) {
  throw new Error(`工程装配：读不到工程约定 ${conventionsPath}：${error.message}`)
}

process.stdout.write(JSON.stringify({ units: rendered, search: await engineeringSearch() }))
