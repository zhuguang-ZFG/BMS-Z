import { readFileSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { createMarkdownRenderer } from 'vitepress'
import { bookRoot, bookChapters } from '../docs/.vitepress/book-sources.mjs'
import { splitBookReading } from '../docs/.vitepress/book-reading-split.mjs'

const md = await createMarkdownRenderer(bookRoot, { math: true })
const kinds = { story: '现场', principle: '原理', trap: '坑', lab: '动手' }

function renderChapterRoute(title, content) {
  const entries = content.trim().split(/\r?\n/).filter(Boolean).map((line) => {
    const match = line.match(/^- \*\*(第一次主线|第二遍深挖|动手验证)\*\*[：:]\s*(.+)$/)
    if (!match) throw new Error(`阅读路径格式错误：${line}`)
    return `<li><strong>${md.utils.escapeHtml(match[1])}</strong><span>${md.renderInline(match[2])}</span></li>`
  })
  if (entries.length !== 3) throw new Error(`阅读路径必须恰好三条：${content}`)
  return `<aside class="chapter-route" aria-label="阅读路径"><p class="chapter-route__eyebrow">${md.utils.escapeHtml(title || '阅读路径')}</p><ol>${entries.join('')}</ol></aside>`
}

const chapters = bookChapters.map((chapter, index) => {
  const prefix = `ch-${String(index + 1).padStart(2, '0')}`
  const callouts = []
  const split = splitBookReading(chapter.file, chapter.source)
  const manuscript = split.deep
    ? `${split.main}\n<!--BOOK-DEEP-START-->\n\n## 进阶与复算\n\n${split.deep}\n<!--BOOK-DEEP-END-->\n`
    : chapter.source
  const routed = manuscript.replace(
    /^::: chapter-route[ \t]*([^\n]*)\n([\s\S]*?)\n:::[ \t]*$/gm,
    (_, title, content) => {
      callouts.push(renderChapterRoute(title, content))
      return `\n\n<!--CALLOUT:${callouts.length - 1}-->\n\n`
    },
  )
  const source = routed.replace(
    /^::: (story|principle|trap|lab)[ \t]*([^\n]*)\n([\s\S]*?)\n:::[ \t]*$/gm,
    (_, kind, title, content) => {
      callouts.push(`<aside class="callout ${kind}"><div class="callout-title">${md.utils.escapeHtml(title || kinds[kind])}</div>${md.render(content)}</aside>`)
      return `\n\n<!--CALLOUT:${callouts.length - 1}-->\n\n`
    },
  )
  let body = md.render(source)
  callouts.forEach((block, i) => { body = body.replace(`<!--CALLOUT:${i}-->`, block) })
  let heading = 0
  const headingIds = new Map()
  body = body.replace(/<h([1-5])([^>]*)>/g, (_, level, attrs) => {
    heading += 1
    const id = heading === 1 ? prefix : `${prefix}-s${heading}`
    const oldId = attrs.match(/\bid="([^"]+)"/)?.[1]
    if (oldId) headingIds.set(oldId, id)
    return `<h${Number(level) + 1}${attrs.replace(/\s+id="[^"]*"/g, '')} id="${id}">`
  }).replace(/<\/h([1-5])>/g, (_, level) => `</h${Number(level) + 1}>`)
  body = body.replace(/((?:href|xlink:href)="#)([^"]+)/g,
    (_, start, id) => `${start}${headingIds.get(decodeURIComponent(id)) ?? id}`)

  // 包含 MathJax 内部 id：跨章避免重复，SVG 引用与 ARIA IDREF 必须同向改写。
  const ids = new Map()
  body.replace(/\bid="([^"]+)"/g, (_, id) => {
    ids.set(id, id.startsWith(prefix) ? id : `${prefix}-${id}`)
    return ''
  })
  body = body.replace(/\bid="([^"]+)"/g, (_, id) => `id="${ids.get(id)}"`)
    .replace(/\baria-labelledby="([^"]+)"/g, (_, value) =>
      `aria-labelledby="${value.split(/\s+/).map(id => ids.get(id) ?? id).join(' ')}"`)
    .replace(/((?:href|xlink:href)="#)([^"]+)/g, (_, start, id) => `${start}${ids.get(id) ?? id}`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${ids.get(id) ?? id})`)
  body = body.replace(/<img src="\.\.\/assets\/([^"]+)"([^>]*)>/g, (_, file, attrs) => {
    const asset = readFileSync(path.join(bookRoot, 'assets', file))
    const text = asset.toString('utf8')
    const [, width, height] = text.match(/viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"/) ?? []
    if (!width || !height) throw new Error(`缺少插图尺寸：${file}`)
    attrs = attrs.replace(/data-motion-src="\.\.\/\.\.\/docs\/circuits\/assets\/([^"]+)"/g, (_, animation) => {
      const motion = readFileSync(path.join(bookRoot, '../docs/circuits/assets', animation))
      return `data-motion-src="data:image/svg+xml;base64,${motion.toString('base64')}"`
    })
    return `<img src="data:image/svg+xml;base64,${asset.toString('base64')}"${attrs} width="${width}" height="${height}" loading="lazy">`
  })
  body = body.replace(/<img src="\.\.\/\.\.\/docs\/circuits\/assets\/photos\/([^"]+)"([^>]*)>/g,
    (_, file, attrs) => {
      const width = attrs.match(/\swidth="(\d+)"/)?.[1]
      const height = attrs.match(/\sheight="(\d+)"/)?.[1]
      if (!width || !height) throw new Error(`书内照片缺少 width/height：${file}`)
      const extension = path.extname(file).toLowerCase()
      const mime = extension === '.png' ? 'image/png' : 'image/jpeg'
      if (!['.jpg', '.jpeg', '.png'].includes(extension)) throw new Error(`不支持的书内照片格式：${file}`)
      const asset = readFileSync(path.join(bookRoot, '../docs/circuits/assets/photos', file))
      return `<img src="data:${mime};base64,${asset.toString('base64')}"${attrs} loading="lazy">`
    })
  body = body.replace(/\s+v-book-(?:motion|lab)(?=[\s>])/g, '')
  body = body.replace('<!--BOOK-DEEP-START-->',
    '<details class="chapter-deep"><summary>展开本章进阶推导与练习</summary>')
    .replace('<!--BOOK-DEEP-END-->', '</details>')
  return { title: chapter.title, prefix, body, part: chapter.part.id }
})
process.stdout.write(JSON.stringify(chapters))
