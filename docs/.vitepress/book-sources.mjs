import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { splitBookReading } from './book-reading-split.mjs'

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
export const bookRoot = path.join(repoRoot, 'bms-book')
export const bookManifest = JSON.parse(readFileSync(path.join(bookRoot, 'manifest.json'), 'utf8'))

const numberedChapterFiles = bookManifest.parts
  .flatMap((part) => part.files)
  .filter((file) => /^(?!00-)\d{2}-/.test(file))
const guideFiles = Object.keys(bookManifest.chapter_guides)
const missingGuides = numberedChapterFiles.filter((file) => !Object.hasOwn(bookManifest.chapter_guides, file))
const extraGuides = guideFiles.filter((file) => !numberedChapterFiles.includes(file))
if (missingGuides.length || extraGuides.length) {
  throw new Error(`章节罗盘清单不完整：missing=${missingGuides.join(',')}, extra=${extraGuides.join(',')}`)
}

const escapeHtml = (value) => value.replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[character])

function upsertImageDimension(attributes, name, value) {
  const pattern = new RegExp(`\\s${name}="[^"]*"`)
  if (pattern.test(attributes)) return attributes.replace(pattern, ` ${name}="${value}"`)
  return `${attributes} ${name}="${value}"`
}

function requireRasterDimensions(attributes, file) {
  const width = attributes.match(/\swidth="(\d+)"/)?.[1]
  const height = attributes.match(/\sheight="(\d+)"/)?.[1]
  if (!width || !height) throw new Error(`书内照片缺少 width/height：${file}`)
}

function chapterCompass(chapter) {
  const guide = bookManifest.chapter_guides[chapter.file]
  if (!guide) return ''
  const rows = [
    ['本章要回答', guide.question],
    ['读完应交出', guide.deliverable],
    ['这一章不证明', guide.boundary],
  ].map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('')
  return `<aside class="chapter-compass" aria-label="本章罗盘"><p class="chapter-compass__eyebrow">读完核对 · 问题、交付与边界</p><dl>${rows}</dl></aside>`
}

function renderRouteInline(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

function chapterRoute(title, content) {
  const rows = content.trim().split(/\r?\n/).filter(Boolean).map((line) => {
    const match = line.match(/^- \*\*(第一次主线|第二遍深挖|动手验证)\*\*[：:]\s*(.+)$/)
    if (!match) throw new Error(`阅读路径格式错误：${line}`)
    return `<li><strong>${match[1]}</strong><span>${renderRouteInline(match[2])}</span></li>`
  })
  if (rows.length !== 3) throw new Error(`阅读路径必须恰好三条：${content}`)
  return `<aside class="chapter-route" aria-label="阅读路径"><p class="chapter-route__eyebrow">${escapeHtml(title || '阅读路径')}</p><ol>${rows.join('')}</ol></aside>`
}

export const bookChapters = bookManifest.parts.flatMap((part) => part.files.map((file) => {
  const source = readFileSync(path.join(bookRoot, 'book', file), 'utf8')
  return {
    part,
    file,
    slug: file.replace(/\.md$/, ''),
    title: source.match(/^# (.+)$/m)?.[1] ?? file,
    source,
  }
}))

export function siteChapter(chapter, index, deep = false) {
  const split = splitBookReading(chapter.file, chapter.source)
  if (deep && !split.deep) throw new Error(`章节没有进阶篇：${chapter.file}`)
  const navigation = (other) => other
    ? { text: other.title, link: `/book/${other.slug}.html` }
    : { text: '书籍与阅读路线', link: '/reading.html' }
  const frontmatter = {
    pageClass: `book-reading book-part-${chapter.part.id}`,
    description: `${chapter.title}${deep ? '进阶与复算' : ''}：BMS 实战伴读书。`,
    prev: deep ? navigation(chapter) : navigation(bookChapters[index - 1]),
    next: navigation(bookChapters[index + 1]),
    editLink: false,
  }
  const compass = deep ? '' : chapterCompass(chapter)
  const kicker = `<p class="book-kicker">${escapeHtml(chapter.part.title)} · ${escapeHtml(chapter.part.description)}</p>`
  const manuscript = deep
    ? `# ${chapter.title}：进阶与复算\n\n${split.deep}`
    : split.main
  const source = manuscript.replace(/^# .+$/m, (heading) => `${kicker}\n\n${heading}`)
    .replace(/^::: chapter-route[ \t]*([^\n]*)\n([\s\S]*?)\n:::[ \t]*$/gm,
      (_, title, content) => chapterRoute(title, content))
    .replace(/data-motion-src="\.\.\/\.\.\/docs\/circuits\/(assets|handraw\/exports)\/([^"]+)"/g,
      (_, dir, file) => `data-motion-src="../circuits/${dir}/${file}"`)
    .replace(/\]\(docs\//g, '](../')
    // 书稿里按仓库相对写的回链 `../../docs/x.md`（check_docs 按书稿所在目录解析，
    // 必须这么写）进站点时降一层：书页在 docs/book/，`../x.md` 正好指回 docs/x.md。
    .replace(/\]\(\.\.\/\.\.\/docs\//g, '](../')
    .replace(/^::: (story|principle|trap|lab)\s*([^\n]*)/gm, (_, kind, title) =>
      `::: ${{ story: 'info', principle: 'tip', trap: 'warning', lab: 'tip' }[kind]} ${title || '实验'}`)
    .replace(/<img src="\.\.\/assets\/([^"]+)" alt="([^"]*)"([^>]*)>/g,
      (_, file, alt, attrs) => {
        // R2 起书内插图有 raster：SVG 走 viewBox，PNG 读 IHDR（宽高在字节 16..24），其余拒绝。
        const extension = path.extname(file).toLowerCase()
        let width, height
        if (extension === '.svg') {
          const svg = readFileSync(path.join(bookRoot, 'assets', file), 'utf8')
          const dimensions = svg.match(/viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"/)
          if (!dimensions) throw new Error(`缺少书内图尺寸：${file}`)
          width = dimensions[1]
          height = dimensions[2]
        } else if (extension === '.png') {
          const png = readFileSync(path.join(bookRoot, 'assets', file))
          if (png.length < 24 || png.readUInt32BE(12) !== 0x49484452) throw new Error(`PNG 缺 IHDR 头：${file}`)
          width = String(png.readUInt32BE(16))
          height = String(png.readUInt32BE(20))
        } else if (extension === '.webp') {
          // 逐帧手绘序列的打印帧：VP8X/VP8L/VP8 三种分块各有一套尺寸打包。
          const webp = readFileSync(path.join(bookRoot, 'assets', file))
          if (webp.length < 30 || webp.toString('ascii', 0, 4) !== 'RIFF'
              || webp.toString('ascii', 8, 12) !== 'WEBP') throw new Error(`WebP 缺 RIFF/WEBP 头：${file}`)
          const fourcc = webp.toString('ascii', 12, 16)
          if (fourcc === 'VP8X') {
            width = String(webp.readUIntLE(24, 3) + 1)
            height = String(webp.readUIntLE(27, 3) + 1)
          } else if (fourcc === 'VP8L') {
            const bits = webp.readUInt32LE(21)
            width = String((bits & 0x3fff) + 1)
            height = String(((bits >> 14) & 0x3fff) + 1)
          } else if (fourcc === 'VP8 ') {
            width = String(webp.readUInt16LE(26) & 0x3fff)
            height = String(webp.readUInt16LE(28) & 0x3fff)
          } else {
            throw new Error(`未知 WebP 分块 ${fourcc}：${file}`)
          }
        } else {
          throw new Error(`不支持的书内图格式：${file}`)
        }
        let attributes = attrs.replace(/\s*\/\s*$/, '')
        attributes = upsertImageDimension(attributes, 'width', width)
        attributes = upsertImageDimension(attributes, 'height', height)
        return `<img src="../../bms-book/assets/${file}" alt="${alt}"${attributes} loading="lazy">`
      })
    .replace(/<img src="\.\.\/\.\.\/docs\/circuits\/assets\/photos\/([^"]+)" alt="([^"]*)"([^>]*)>/g,
      (_, file, alt, attrs) => {
        readFileSync(path.join(repoRoot, 'docs', 'circuits', 'assets', 'photos', file))
        const attributes = attrs.replace(/\s*\/\s*$/, '')
        requireRasterDimensions(attributes, file)
        return `<img src="../circuits/assets/photos/${file}" alt="${alt}"${attributes} loading="lazy">`
      })
  const deepLink = split.deep && !deep
    ? `\n\n[读进阶与复算](./${chapter.slug}-进阶.md)`
    : ''
  const backLink = deep ? `\n\n[返回第 ${chapter.file.slice(0, 2).replace(/^0/, '')} 章主线](./${chapter.slug}.md)` : ''
  return `---\n${JSON.stringify(frontmatter, null, 2)}\n---\n\n${source}\n\n${compass}${deepLink}${backLink}\n\n[返回书籍与阅读路线](../reading.md) · [查看本章源码](../../bms-book/book/${chapter.file})\n`
}

export const readingListSource = readFileSync(path.join(repoRoot, 'BMS书籍清单.md'), 'utf8')
  .replace(/\]\(docs\//g, '](../')
  .replace(/\]\(bms-book\//g, '](../../bms-book/')

export function readingRoutes() {
  return [
    ...bookChapters.flatMap((chapter, index) => {
      const routes = [{ params: { chapter: chapter.slug }, content: siteChapter(chapter, index) }]
      if (splitBookReading(chapter.file, chapter.source).deep) {
        routes.push({ params: { chapter: `${chapter.slug}-进阶` }, content: siteChapter(chapter, index, true) })
      }
      return routes
    }),
    {
      params: { chapter: '书籍清单' },
      content: `---\nprev: false\nnext: false\neditLink: false\n---\n\n${readingListSource}\n\n[返回书籍与阅读路线](../reading.md)\n`,
    },
  ]
}
