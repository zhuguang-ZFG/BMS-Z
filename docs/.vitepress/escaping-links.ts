/**
 * 把站点上点不开的相对链接改写成 GitHub URL。三类：跨出 docs/ 的文件、
 * 目录链接（站点没有目录列表）、docs/ 内部但不在产物里的源文件（.vitepress/ 等）。
 *
 * 为什么要改：docs/ 里有近百处合法相对链接指向仓库根——README.md、CHANGELOG.md、
 * CONTRIBUTING.md、code/**、challenges/**、.github/ISSUE_TEMPLATE/**。它们在 GitHub
 * 网页端和 Obsidian 里都能点开，所以源码不能动。但 VitePress 的站点根就是 docs/，
 * 它会把这类链接规范化成 `./../README.html`，在 Pages 上直接 404。
 *
 * 怎么办：渲染期按「当前页 → 仓库根」的相对位置还原出真实文件路径，指回 GitHub
 * （文件走 blob、目录走 tree）。锚点片段原样保留——标题 id 已与 GitHub slug
 * 对齐（见 config.mts 的 githubSlugify），同一个片段在两边都命中。
 */
import { existsSync, statSync } from 'node:fs'
import path from 'node:path'
import type MarkdownIt from 'markdown-it'
import type { StateCore } from 'markdown-it/index.js'

/** 仓库在 GitHub 上的位置；站点外的文件一律链到这里。 */
const BLOB_BASE = 'https://github.com/zhuguang-ZFG/BMS-Z/blob/main'

/** 目录链接的去处：GitHub 的目录页在站点上没有对应物，站点不提供目录列表。 */
const TREE_BASE = 'https://github.com/zhuguang-ZFG/BMS-Z/tree/main'

/**
 * 允许指向仓库根的顶层入口。白名单而不是「本地文件存在」：books/ 下的 PDF 只在某些
 * 机器上存在，按存在性改写会造出只在本地能点开的链接。
 */
const SITE_OUTSIDE_ROOTS = new Set([
  '.github',
  '.gitignore',
  'challenges',
  'code',
  'tools',
  'README.md',
  'CHANGELOG.md',
  'CONTRIBUTING.md',
  'CODE_OF_CONDUCT.md',
  'SECURITY.md',
  'LICENSE',
  'ruff.toml',
  '.lychee.toml',
  'BMS书籍清单.md',
])

/** VitePress 会把 .md 规范化成 .html，还原时按顺序试这几个后缀。 */
const EXT_CANDIDATES = ['', '.md', '.html']

/**
 * 仓库根上由站点自己托管的文件：正文照旧写 `../BMS学习路径.html`（GitHub 与 Obsidian
 * 都靠这个相对路径），构建时拷进 dist，Pages 上指向站点内的绝对 URL。
 * 键是仓库根相对路径，值是带 base 的站点 URL。
 */
export type SiteAssets = Readonly<Record<string, string>>

function isExternal(href: string): boolean {
  return /^(?:[a-z][a-z\d+\-.]*:|#|\/\/)/i.test(href)
}

/**
 * `../README.html`（当前页 `/repo/docs/共建任务板.md`）→ `README.md` 的 blob URL。
 * 还原不出白名单内的真实文件时返回 null，链接原样留给 VitePress。
 *
 * 站点根不取 cwd、也不取 import.meta.url：VitePress 编译 config 时这两处都可能变，
 * 而它一定会在 env.path 里给出当前页的绝对路径，仓库位置由它反推。
 */
export function resolveEscapingLink(
  href: string,
  pageAbsPath: string,
  siteAssets: SiteAssets
): string | null {
  if (isExternal(href)) return null

  const docsDir = docsRootOf(pageAbsPath)
  if (!docsDir) return null

  const [pathPart, frag] = href.split('#')
  const abs = path.resolve(
    docsDir,
    path.dirname(path.relative(docsDir, pageAbsPath)),
    decodeURIComponent(pathPart)
  )

  const repoRoot = path.dirname(docsDir)
  const normalized = path
    .relative(repoRoot, abs)
    .split(path.sep)
    .join('/')

  // 目录链接（如 circuits/README 里的 ../stages/、./assets/photos/）：GitHub 网页端
  // 打开的是目录列表，站点上没有对应页面（VitePress 只产出 .html 文件页），
  // 不指回 GitHub 就只能在 Pages 上 404。片段对目录页没有意义，丢掉。
  if (existsSync(abs) && statSync(abs).isDirectory()) {
    return `${TREE_BASE}/${normalized.split('/').map(encodeURIComponent).join('/')}`
  }

  // 仍在 docs/ 内部的链接默认是站点自己的页面，VitePress 会正确解析。
  // 但站点只产出 .md 对应的页面和 assets/ 下的拷贝——指向 docs 里其他源文件
  // （.vitepress/ 的配置与插件、以后可能出现的 .ts/.json）的链接在产物里没有
  // 对应物，也改指回 GitHub blob，保持「源码写法不动」的纪律。
  const toDocs = path.relative(docsDir, abs)
  if (!toDocs.startsWith('..') && !path.isAbsolute(toDocs)) {
    if (
      existsSync(abs) &&
      path.extname(abs) !== '.md' &&
      !abs.split(path.sep).includes('assets')
    ) {
      // normalized 相对仓库根，docs/ 内的文件自带 docs/ 前缀，别再补一次。
      return `${BLOB_BASE}/${normalized
        .split('/')
        .map(encodeURIComponent)
        .join('/')}${frag ? `#${frag}` : ''}`
    }
    return null
  }

  const siteUrl = siteAssets[normalized]
  if (siteUrl) return frag ? `${siteUrl}#${frag}` : siteUrl

  const [top] = normalized.split('/')
  if (!SITE_OUTSIDE_ROOTS.has(top)) return null

  const segments = normalized.split('/')
  const base = segments[segments.length - 1]
  const stem = base.replace(/\.html?$/, '')
  const dirSegments = segments.slice(0, -1)
  for (const ext of EXT_CANDIDATES) {
    const candidate = [...dirSegments, stem + ext].join('/')
    if (existsSync(path.join(repoRoot, ...candidate.split('/')))) {
      return `${BLOB_BASE}/${candidate.split('/').map(encodeURIComponent).join('/')}${
        frag ? `#${frag}` : ''
      }`
    }
  }
  return null
}

/** 往上找到 docs/ 那一层；页面不在 docs/ 下时返回 null。 */
function docsRootOf(pageAbsPath: string): string | null {
  let current = path.dirname(pageAbsPath)
  while (current !== path.dirname(current)) {
    if (path.basename(current) === 'docs') return current
    current = path.dirname(current)
  }
  return null
}

export function escapingLinksToGitHub(siteAssets: SiteAssets): (md: MarkdownIt) => void {
  return (md: MarkdownIt) => {
    md.core.ruler.push('bms-escaping-links', (state: StateCore) => {
      const env = state.env as { path?: string; relativePath?: string } | undefined
      const pageAbs = env?.path ?? env?.relativePath
      if (!pageAbs) return true
      for (const token of state.tokens) {
        if (token.type !== 'inline' || !token.children) continue
        for (const child of token.children) {
          if (child.type !== 'link_open') continue
          const idx = child.attrIndex('href')
          if (idx < 0) continue
          const rewritten = resolveEscapingLink(child.attrs![idx][1], pageAbs, siteAssets)
          if (rewritten) child.attrs![idx][1] = rewritten
        }
      }
      return true
    })
  }
}
