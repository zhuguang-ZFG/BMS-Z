/**
 * 跨卷引用（设计 §9）：解析两家书稿之间的普通相对 Markdown 链接。
 *
 * 引用源始终指向对方的书稿文件（GitHub 上可点开），这里按清单与标题算出
 * 唯一章/附录标签：站点版改写为带「卷一/卷二」前缀的站内链接，印刷版与
 * 单文件 HTML 降级为纯文本。标签只由清单生成，正文里不许手写卷次。
 */
import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const analogDocs = path.join(repoRoot, 'analog', 'docs')
const bmsBook = path.join(repoRoot, 'bms-book', 'book')
const analogManifest = JSON.parse(
  readFileSync(path.join(repoRoot, 'analog', 'analog-book', 'manifest.json'), 'utf8'))
const bmsManifest = JSON.parse(
  readFileSync(path.join(repoRoot, 'bms-book', 'manifest.json'), 'utf8'))

const volumeName = (volume) => (volume === 'I' ? '卷一' : '卷二')

function heading(file, pattern) {
  const match = readFileSync(file, 'utf8').match(pattern)
  if (!match) throw new Error(`章节缺少标题：${file}`)
  return match[1].replace(/<[^>]+>/g, '').trim()
}

function shortTitle(title) {
  return title
    .replace(/^第\s*\d+\s*章\s*/, '')
    .replace(/^附录\s*[A-Z]\s*/, '')
    .trim()
}

function label(volume, number, title) {
  const prefix = volumeName(volume)
  const clean = shortTitle(title)
  if (number.startsWith('附录')) return `${prefix}·${number}《${clean}》`
  return `${prefix}·第 ${number} 章《${clean}》`
}

function chapter(volume, number, title, file) {
  return {
    volume,
    number,
    label: label(volume, number, title),
    href: volume === 'I' ? `/volume-1/${file.replace(/\.md$/, '')}.html`
      : `/book/${file.replace(/\.md$/, '')}.html`,
  }
}

function buildChapters() {
  const chapters = new Map()
  const register = (file, entry) => {
    const key = path.resolve(file)
    if (chapters.has(key)) throw new Error(`跨卷索引重复：${key}`)
    chapters.set(key, entry)
  }
  for (const part of analogManifest.parts) {
    for (const unit of part.units) {
      for (const name of unit.chapters) {
        const file = path.join(analogDocs, name)
        const number = name.match(/ch(\d+)\.md$/)?.[1]
        if (!number) throw new Error(`卷一章号无法解析：${name}`)
        register(file, chapter('I', number, heading(file, /^##\s+(.+?)\s*$/m), name))
      }
    }
  }
  for (const appendix of analogManifest.appendices) {
    for (const name of appendix.files ?? []) {
      register(path.join(analogDocs, name),
        chapter('I', `附录 ${appendix.id}`, appendix.title, name))
    }
  }
  const numbered = bmsManifest.parts.flatMap((part) => part.files)
    .filter((name) => /^(?!00-)\d{2}-/.test(name))
  for (const name of numbered) {
    const file = path.join(bmsBook, name)
    const number = String(Number(name.slice(0, 2)))
    register(file, chapter('II', number, heading(file, /^#\s+(.+?)\s*$/m), name))
  }
  const appendices = readdirSync(bmsBook).filter((name) => /^附录.*\.md$/.test(name)).sort()
  appendices.forEach((name, index) => {
    const file = path.join(bmsBook, name)
    register(file, chapter('II', `附录 ${String.fromCharCode(65 + index)}`,
      heading(file, /^#\s+(.+?)\s*$/m), name))
  })
  return chapters
}

const chapters = buildChapters()

function volumeOf(file) {
  const resolved = path.resolve(file)
  if (resolved.startsWith(`${analogDocs}${path.sep}`)) return 'I'
  if (resolved.startsWith(`${bmsBook}${path.sep}`)) return 'II'
  return null
}

/** 解析一个源链接；卷内、站外、非 Markdown 目标都返回 null。 */
export function resolveCrossVolume(sourceFile, href) {
  if (!sourceFile || !href || /^(?:[a-z][a-z0-9+.-]*:|\/\/|\/|#)/i.test(href)) return null
  const sourceVolume = volumeOf(sourceFile)
  if (!sourceVolume) return null
  const hash = href.indexOf('#')
  const pathPart = (hash < 0 ? href : href.slice(0, hash)).split('?')[0]
  const anchor = hash < 0 ? '' : href.slice(hash)
  if (!pathPart.endsWith('.md')) return null
  const target = path.resolve(path.dirname(sourceFile), decodeURIComponent(pathPart))
  const targetVolume = volumeOf(target)
  if (!targetVolume || targetVolume === sourceVolume) return null
  const entry = chapters.get(target)
  if (!entry) throw new Error(`跨卷目标不在清单中：${sourceFile} -> ${href}`)
  return { label: entry.label, href: `${entry.href}${anchor}` }
}

const MARKDOWN_LINK = /(?<!!)\[([^\]]*)\]\(([^)\s]+)\)/g
const HTML_LINK = /<a\b([^>]*?)\bhref="([^"]+)"([^>]*)>(.*?)<\/a>/gs

function replaceMarkdown(source, sourceFile, mode) {
  return source.replace(MARKDOWN_LINK, (whole, text, href) => {
    const resolved = resolveCrossVolume(sourceFile, href)
    if (!resolved) return whole
    return mode === 'site' ? `[${resolved.label}](${resolved.href})` : resolved.label
  })
}

function replaceHtml(source, sourceFile, mode) {
  return source.replace(HTML_LINK, (whole, before, href, after, text) => {
    const resolved = resolveCrossVolume(sourceFile, href)
    if (!resolved) return whole
    return mode === 'site'
      ? `<a${before} href="${resolved.href}"${after}>${resolved.label}</a>`
      : resolved.label
  })
}

/** 站点版：链接保留，文本与目标均改成清单推导的标签与路由。 */
export function rewriteCrossLinksForSite(source, sourceFile) {
  return replaceHtml(replaceMarkdown(source, sourceFile, 'site'), sourceFile, 'site')
}

/** 印刷版与单文件 HTML：降级为纯文本「卷二·第 6 章《…》」。 */
export function degradeCrossLinks(source, sourceFile) {
  return replaceHtml(replaceMarkdown(source, sourceFile, 'print'), sourceFile, 'print')
}
