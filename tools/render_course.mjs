/** Render the sequential course from its only manuscript source. */
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createMarkdownRenderer } from 'vitepress'
import { BASE, SITE_ORIGIN } from '../docs/.vitepress/base.ts'
import { bookChapters } from '../docs/.vitepress/book-sources.mjs'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const course = path.join(root, 'docs', 'course')
const manifest = JSON.parse(readFileSync(path.join(course, 'manifest.json'), 'utf8'))
const md = await createMarkdownRenderer(course, { math: true })
const sources = [
  { file: 'index.md', prefix: 'course-guide', title: '怎么使用这门课程' },
  { file: 'project.md', prefix: 'course-project', title: '贯穿项目使用说明' },
  ...manifest.lessons.map(lesson => ({ ...lesson, prefix: `lesson-${lesson.id}` })),
]
const byFile = new Map(sources.map(item => [item.file, item]))

// Render first so links to headings in other lessons can resolve against actual IDs.
for (const item of sources) {
  let body = md.render(readFileSync(path.join(course, item.file), 'utf8'))
  body = body.replace(/<a\b[^>]*class="[^"]*header-anchor[^"]*"[^>]*>[\s\S]*?<\/a>/g, '')
    .replace(/<button\b[^>]*>[\s\S]*?<\/button>/g, '')
    .replace(/<span class="lang">[\s\S]*?<\/span>/g, '')
  const ids = new Map()
  let count = 0
  body = body.replace(/<h([1-6])([^>]*)>/g, (_, level, attrs) => {
    const old = attrs.match(/\bid="([^"]+)"/)?.[1]
    const id = count++ === 0 ? item.prefix : `${item.prefix}-${old ?? `s${count}`}`
    if (old) ids.set(old, id)
    return `<h${Math.min(Number(level) + 1, 6)}${attrs.replace(/\s+id="[^"]*"/g, '')} id="${id}">`
  }).replace(/<\/h([1-6])>/g, (_, level) => `</h${Math.min(Number(level) + 1, 6)}>`)
  // Include MathJax and explicit HTML IDs in the same namespace, preserving IDREFs.
  body.replace(/\bid="([^"]+)"/g, (_, id) => {
    if (![...ids.values()].includes(id)) ids.set(id, `${item.prefix}-${id}`)
    return ''
  })
  const mappedIds = new Set(ids.values())
  body = body.replace(/\bid="([^"]+)"/g, (_, id) => `id="${mappedIds.has(id) ? id : ids.get(id)}"`)
    .replace(/\b(aria-labelledby|aria-describedby)="([^"]+)"/g, (_, attr, value) =>
      `${attr}="${value.split(/\s+/).map(id => ids.get(id) ?? id).join(' ')}"`)
    .replace(/(xlink:href=")#([^"]+)/g, (_, start, id) => `${start}#${ids.get(id) ?? id}`)
    .replace(/url\(#([^)]+)\)/g, (_, id) => `url(#${ids.get(id) ?? id})`)
  item.body = body
  item.ids = ids
}

for (const item of sources) {
  item.assets = []
  item.body = item.body.replace(/(<a\b[^>]*\bhref=")([^"]+)(")/g, (_, before, href, after) => {
    if (/^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(href)) return before + href + after
    const [rawPath, rawHash = ''] = href.split('#')
    // VitePress normalizes Markdown links to .html while rendering.
    const localPath = decodeURIComponent(rawPath).replace(/^\.\//, '').replace(/\.html$/, '.md')
    const hash = decodeURIComponent(rawHash)
    const target = byFile.get(localPath || item.file)
    if (target) {
      const id = hash ? target.ids.get(hash) : target.prefix
      if (!id) throw new Error(`${item.file}: unknown course heading ${href}`)
      return `${before}#${id}${after}`
    }
    const resolved = path.resolve(course, localPath)
    const docs = path.join(root, 'docs')
    if (resolved.startsWith(path.join(root, 'bms-book', 'book') + path.sep)) {
      const chapter = bookChapters.find(chapter => chapter.file === path.basename(resolved))
      if (!chapter) throw new Error(`${item.file}: unknown deep-reading chapter ${href}`)
      return `${before}${SITE_ORIGIN}${BASE}book/${chapter.slug}.html${rawHash ? `#${rawHash}` : ''}${after}`
    }
    if (!resolved.startsWith(docs + path.sep)) throw new Error(`${item.file}: unsupported local link ${href}`)
    const sitePath = path.relative(docs, resolved).replaceAll(path.sep, '/').replace(/\.md$/, '.html')
    return `${before}${SITE_ORIGIN}${BASE}${sitePath}${rawHash ? `#${rawHash}` : ''}${after}`
  })
  item.body = item.body.replace(/(<img\b[^>]*\bsrc=")([^"]+)(")/g, (_, before, src, after) => {
    if (src.startsWith('data:')) return before + src + after
    if (/^[a-z]+:/i.test(src)) throw new Error(`${item.file}: remote image is not offline: ${src}`)
    const asset = path.resolve(course, decodeURIComponent(src))
    if (!asset.startsWith(root + path.sep)) throw new Error(`Image outside repository: ${src}`)
    const mime = { '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg' }[path.extname(asset).toLowerCase()]
    if (!mime) throw new Error(`Unsupported image: ${src}`)
    item.assets.push(path.relative(root, asset).replaceAll(path.sep, '/'))
    return `${before}data:${mime};base64,${readFileSync(asset).toString('base64')}${after}`
  })
  // Keep answers closed in HTML; EPUB keeps their contents and PDF expands a print copy.
}
process.stdout.write(JSON.stringify(sources.map(({ ids: _ids, ...item }) => item)))
