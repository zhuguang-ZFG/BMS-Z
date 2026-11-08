// 工程深研样章渲染器（P2.6）：只读登记过的正文源，用站点的 createMarkdownRenderer
// （含 mathjax3 离线数学）把样章 Markdown 渲染成 HTML 片段。自定义语义块
// （story/chapter-route，三到五冒号）在渲染前改成 <aside> 占位，与 bms-book/render.mjs
// 同一模式；格式不对直接抛错，不静默吞。输出 JSON 到 stdout，由 tools/build_engineering.py 装配。
import { readFileSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'

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

const manifest = readJson('bms-book/engineering-manifest.json')

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

// 库内回链统一改写：bridges/code 指 GitHub 源，docs/旧书章节指发布站点，工程约定指本册页面。
// 样章在 bms-book/engineering/ 下（两层 ../），约定在 bms-book/ 下（一层）：都按 (?:\.\./)+ 认。
// 离线单文件不携带第二套真源；内容链接（<a href>）允许外链，资源（img/script/link）不许。
function rewriteInternalLinks(html) {
  return html
    .replace(/(<a\b[^>]*\bhref=")(?:\.\/)?(?:\.\.\/)+bridges\/([^"/]+)\.(?:md|html)([^"]*)(")/g,
      (_w, start, name, _frag, end) => `${start}https://github.com/zhuguang-ZFG/BMS-Z/blob/main/bms-book/bridges/${encodeURIComponent(name)}.md${end}`)
    .replace(/(<a\b[^>]*\bhref=")(?:\.\/)?(?:\.\.\/)+docs\//g, `$1${SITE_ORIGIN}${BASE}`)
    .replace(/(<a\b[^>]*\bhref=")(?:\.\/)?(?:\.\.\/)+engineering-conventions\.html/g, '$1conventions.html')
    .replace(/(<a\b[^>]*\bhref=")(?:\.\/)?(?:\.\.\/)+code\/(.*?)\.html/g,
      '$1https://github.com/zhuguang-ZFG/BMS-Z/blob/main/code/$2')
    .replace(/(<a\b[^>]*\bhref=")(?:\.\/)?(?:\.\.\/)+book\/(.*?)\.html/g,
      `$1${SITE_ORIGIN}${BASE}book/$2.html`)
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
  html = rewriteInternalLinks(html)
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

const units = manifest.units.filter((u) => u.kind === 'sample' && u.status === 'locally_verified')
const rendered = units.map(renderUnit)

// 工程约定（符号/时钟/数据口径合同）随册交付；样章里的相对回链在装配侧改指本页。
const conventionsPath = path.join(ROOT, 'bms-book/engineering-conventions.md')
try {
  const conventionsText = readFileSync(conventionsPath, 'utf8')
  const conventions = rewriteInternalLinks(md.render(conventionsText))
  rendered.push({
    id: 'conventions',
    title: '工程深研约定（符号、时钟与数据口径）',
    html: conventions,
    headings: [],
  })
} catch (error) {
  throw new Error(`工程装配：读不到工程约定 ${conventionsPath}：${error.message}`)
}

process.stdout.write(JSON.stringify({ units: rendered }))
