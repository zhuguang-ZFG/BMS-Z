import { readFileSync } from 'node:fs'
import path from 'node:path'
import process from 'node:process'
import { createMarkdownRenderer } from 'vitepress'
import { bookRoot, bookChapters } from '../docs/.vitepress/book-sources.mjs'

const md = await createMarkdownRenderer(bookRoot, { math: true })
const kinds = { story: '现场', principle: '原理', trap: '坑', lab: '动手' }

const chapters = bookChapters.map((chapter, index) => {
  const prefix = `ch-${String(index + 1).padStart(2, '0')}`
  const callouts = []
  const source = chapter.source.replace(
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

  // 包含 MathJax 内部 id：跨章避免重复，SVG 的 href/url 也要同向改写。
  const ids = new Map()
  body.replace(/\bid="([^"]+)"/g, (_, id) => {
    ids.set(id, id.startsWith(prefix) ? id : `${prefix}-${id}`)
    return ''
  })
  body = body.replace(/\bid="([^"]+)"/g, (_, id) => `id="${ids.get(id)}"`)
    .replace(/((?:href|xlink:href)="#)([^"]+)/g, (_, start, id) => `${start}${ids.get(id) ?? id}`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${ids.get(id) ?? id})`)
  body = body.replace(/<img src="\.\.\/assets\/([^"]+)"([^>]*)>/g, (_, file, attrs) => {
    const asset = readFileSync(path.join(bookRoot, 'assets', file))
    const text = asset.toString('utf8')
    const [, width, height] = text.match(/viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"/) ?? []
    if (!width || !height) throw new Error(`缺少插图尺寸：${file}`)
    return `<img src="data:image/svg+xml;base64,${asset.toString('base64')}"${attrs} width="${width}" height="${height}" loading="lazy">`
  })
  return { title: chapter.title, prefix, body, part: chapter.part.id }
})
process.stdout.write(JSON.stringify(chapters))
