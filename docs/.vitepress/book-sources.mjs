import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

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

function chapterCompass(chapter) {
  const guide = bookManifest.chapter_guides[chapter.file]
  if (!guide) return ''
  const rows = [
    ['本章要回答', guide.question],
    ['读完应交出', guide.deliverable],
    ['这一章不证明', guide.boundary],
  ].map(([label, value]) => `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('')
  return `<aside class="chapter-compass" aria-label="本章罗盘"><p class="chapter-compass__eyebrow">本章导读 · 先定问题，再读证据</p><dl>${rows}</dl></aside>`
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

export function siteChapter(chapter, index) {
  const navigation = (other) => other
    ? { text: other.title, link: `/book/${other.slug}.html` }
    : { text: '书籍与阅读路线', link: '/reading.html' }
  const frontmatter = {
    pageClass: `book-reading book-part-${chapter.part.id}`,
    description: `${chapter.title}：BMS 实战伴读书，配原理、实验与练习。`,
    prev: navigation(bookChapters[index - 1]),
    next: navigation(bookChapters[index + 1]),
    editLink: false,
  }
  const compass = chapterCompass(chapter)
  const kicker = `<p class="book-kicker">${escapeHtml(chapter.part.title)} · ${escapeHtml(chapter.part.description)}</p>`
  const source = (compass
    ? chapter.source.replace(/^# .+$/m, (heading) => `${kicker}\n\n${heading}\n\n${compass}`)
    : chapter.source.replace(/^# .+$/m, (heading) => `${kicker}\n\n${heading}`))
    .replace(/data-motion-src="\.\.\/\.\.\/docs\/circuits\/assets\/([^"]+)"/g,
      (_, file) => `data-motion-src="../circuits/assets/${file}"`)
    .replace(/\]\(docs\//g, '](../')
    .replace(/^::: (story|principle|trap|lab)\s*([^\n]*)/gm, (_, kind, title) =>
      `::: ${{ story: 'info', principle: 'tip', trap: 'warning', lab: 'tip' }[kind]} ${title || '实验'}`)
    .replace(/<img src="\.\.\/assets\/([^"]+)" alt="([^"]*)"([^>]*)>/g,
      (_, file, alt, attrs) => {
        const svg = readFileSync(path.join(bookRoot, 'assets', file), 'utf8')
        const dimensions = svg.match(/viewBox="[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)"/)
        if (!dimensions) throw new Error(`缺少书内图尺寸：${file}`)
        const attributes = attrs.replace(/\s*\/\s*$/, '')
        return `<img src="../../bms-book/assets/${file}" alt="${alt}"${attributes} width="${dimensions[1]}" height="${dimensions[2]}" loading="lazy">`
      })
  return `---\n${JSON.stringify(frontmatter, null, 2)}\n---\n\n${source}\n\n[返回书籍与阅读路线](../reading.md) · [查看本章源码](../../bms-book/book/${chapter.file})\n`
}

export const readingListSource = readFileSync(path.join(repoRoot, 'BMS书籍清单.md'), 'utf8')
  .replace(/\]\(docs\//g, '](../')
  .replace(/\]\(bms-book\//g, '](../../bms-book/')

export function readingRoutes() {
  return [
    ...bookChapters.map((chapter, index) => ({
      params: { chapter: chapter.slug }, content: siteChapter(chapter, index),
    })),
    {
      params: { chapter: '书籍清单' },
      content: `---\nprev: false\nnext: false\neditLink: false\n---\n\n${readingListSource}\n\n[返回书籍与阅读路线](../reading.md)\n`,
    },
  ]
}
