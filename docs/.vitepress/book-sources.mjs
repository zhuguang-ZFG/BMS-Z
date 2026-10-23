import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
export const bookRoot = path.join(repoRoot, 'bms-book')
export const bookManifest = JSON.parse(readFileSync(path.join(bookRoot, 'manifest.json'), 'utf8'))

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
    description: `${chapter.title}：BMS 实战伴读书，配原理、实验与练习。`,
    prev: navigation(bookChapters[index - 1]),
    next: navigation(bookChapters[index + 1]),
    editLink: false,
  }
  const source = chapter.source
    .replace(/\]\(docs\//g, '](../')
    .replace(/^::: (story|principle|trap|lab)\s*([^\n]*)/gm, (_, kind, title) =>
      `::: ${{ story: 'info', principle: 'tip', trap: 'warning', lab: 'tip' }[kind]} ${title || '实验'}`)
    .replace(/<img src="\.\.\/assets\/([^"]+)" alt="([^"]*)"\s*\/?\s*>/g,
      (_, file, alt) => `\n\n![${alt}](../../bms-book/assets/${file})\n\n`)
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
