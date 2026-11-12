/**
 * 卷一（模拟电路书）的站点视图：从书稿清单推导页面顺序、标题与资源清单。
 *
 * 书稿的根清单 `book/manifest.json` 指向卷一的 schema 2 清单；那份清单只收
 * 54 个印刷页，站点还多出 9 个「清单不收、但读者需要」的篇首页与目录页。
 * 这里把它们按篇位插回去，得到稳定的 63 页阅读顺序——侧栏、镜像脚本与
 * parity 测试共用这一份顺序，谁也不再各写一张表。
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
export const volumeOneDocs = path.join(repoRoot, 'analog', 'docs')
export const volumeOneAssets = path.join(repoRoot, 'analog', 'assets')
export const volumeOneManifestPath = path.join(repoRoot, 'analog', 'analog-book', 'manifest.json')

const volumeOneManifest = JSON.parse(readFileSync(volumeOneManifestPath, 'utf8'))

/** 篇首页：印刷清单把它们折进篇扉页，站点保留为可读的一页。 */
const PART_OPENERS = {
  I: 'p1-00-part1.md',
  III: 'p2-00-part2.md',
  IV: 'p3-00-part3.md',
  V: 'p4-00-part4.md',
}

/** 附录分节页：清单只收节内正文，站点把「第 N 篇」入口页放在对应附录开头。 */
const APPENDIX_OPENERS = {
  A: ['p5-00-part5.md'],
  C: ['p6-00-part6.md'],
  D: ['p7-00-part7.md'],
  E: ['p8-00-part8.md'],
}

export const galleryPage = {
  file: 'gallery.md',
  slug: 'gallery',
  title: '动画画廊',
  href: '/volume-1/gallery',
}

export const landingPage = {
  file: 'index.md',
  slug: '',
  title: '卷一：模拟电路之路',
  href: '/volume-1/',
}

/** 首页标题：跳过代码围栏，取第一个 `#`，没有就取第一个 `##`。 */
export function pageTitle(source) {
  let fence = ''
  for (const line of source.split(/\r?\n/)) {
    const delimiter = line.match(/^\s*(`{3,}|~{3,})/)
    if (delimiter) {
      if (!fence) fence = delimiter[1][0]
      else if (delimiter[1][0] === fence) fence = ''
      continue
    }
    if (fence) continue
    const heading = line.match(/^#{1,2} (.+)$/)
    if (heading) return heading[1].replace(/\s+#+\s*$/, '').trim()
  }
  return ''
}

function readPage(file) {
  const absolute = path.join(volumeOneDocs, file)
  if (!existsSync(absolute)) throw new Error(`卷一页面不存在：${file}`)
  const source = readFileSync(absolute, 'utf8')
  return { file, source, title: pageTitle(source) || file.replace(/\.md$/, '') }
}

function unique(files, seen) {
  const out = []
  for (const file of files) {
    if (seen.has(file)) throw new Error(`卷一页面重复：${file}`)
    seen.add(file)
    out.push(file)
  }
  return out
}

/**
 * 顺序 = 前置页 → 五篇（含篇首页）→ 附录 A–H（含分节页与画廊）→ 书末。
 * 清单外的 9 页全部在这里显式落位；最后再做一次「源目录 ↔ 顺序表」对账，
 * 新增页面忘了登记会当场报错，而不是从站点上静默消失。
 */
function buildPages() {
  const seen = new Set()
  const groups = []

  const front = volumeOneManifest.front_matter
    .filter((entry) => entry.file)
    .map((entry) => entry.file)
  front.push('p0-07-toc.md')
  groups.push({
    key: 'front',
    text: '开始之前',
    files: unique(front, seen),
  })

  for (const part of volumeOneManifest.parts) {
    const files = []
    const opener = PART_OPENERS[part.id]
    if (opener) files.push(opener)
    for (const unit of part.units) files.push(...unit.chapters)
    groups.push({
      key: `part-${part.id}`,
      text: `${part.title} · ${part.subtitle}`,
      files: unique(files, seen),
    })
  }

  for (const appendix of volumeOneManifest.appendices) {
    const files = [...(APPENDIX_OPENERS[appendix.id] || []), ...(appendix.files || [])]
    // 附录 A 是动画索引，站点上的画廊页接在它的入口页后面。
    if (appendix.id === 'A') files.push(galleryPage.file)
    groups.push({
      key: `appendix-${appendix.id}`,
      text: `附录 ${appendix.id} · ${appendix.title}`,
      files: unique(files, seen),
    })
  }

  const back = volumeOneManifest.back_matter
    .filter((entry) => entry.file)
    .map((entry) => entry.file)
  groups.push({
    key: 'back',
    text: '书末',
    files: unique(back, seen),
  })

  const sourceFiles = readdirSync(volumeOneDocs)
    .filter((name) => name.endsWith('.md') && name !== 'index.md')
    .sort()
  const generated = new Set([galleryPage.file])
  const missing = sourceFiles.filter((file) => !seen.has(file))
  const extra = [...seen].filter((file) => !sourceFiles.includes(file) && !generated.has(file))
  if (missing.length || extra.length) {
    throw new Error(`卷一顺序表与 docs/ 不一致：missing=${missing.join(',')} extra=${extra.join(',')}`)
  }

  const pages = []
  for (const group of groups) {
    for (const file of group.files) {
      if (file === galleryPage.file) {
        pages.push({ ...galleryPage, group: group.key })
        continue
      }
      pages.push({ ...readPage(file), group: group.key })
    }
  }
  return { groups, pages }
}

export const volumeOne = buildPages()

export function volumeOneSlug(file) {
  return file.replace(/\.md$/, '')
}

export function pageHref(page) {
  return page.href ?? `/volume-1/${volumeOneSlug(page.file)}`
}

/** VitePress 侧栏：篇为组，页为项；书末与附录折叠，正文篇常开。 */
export function volumeOneGroups() {
  return [
    {
      text: '卷一 · 模拟电路之路',
      items: [
        { text: '卷一导读', link: landingPage.href },
        { text: '书籍与阅读路线', link: '/reading' },
      ],
    },
    ...volumeOne.groups.map((group) => ({
      text: group.key.startsWith('appendix-') || group.key === 'back' ? `卷一 · ${group.text}` : group.text,
      collapsed: group.key.startsWith('appendix-') || group.key === 'back',
      items: group.files.map((file) => {
        const page = volumeOne.pages.find((item) => item.file === file)
        return { text: page.title, link: pageHref(page) }
      }),
    })),
  ]
}

/** 动画索引：只认仓库里那份 YAML，字段格式由 generate 脚本固定为「- id」+ 两空格键。 */
export function animationIndex() {
  const file = path.join(repoRoot, 'analog', 'analog-book', 'data', 'animations.yml')
  const items = []
  let current = null
  let lastKey = ''
  for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
    if (line.startsWith('- id:')) {
      if (current) items.push(current)
      current = { id: line.slice(5).trim() }
      lastKey = ''
      continue
    }
    if (!current) continue
    const match = line.match(/^  ([a-z_]+):\s?(.*)$/)
    if (match) {
      current[match[1]] = match[2]
      lastKey = match[1]
    } else if (line.startsWith('    ') && lastKey) {
      current[lastKey] += ` ${line.trim()}`
    }
  }
  if (current) items.push(current)
  for (const item of items) {
    if (!item.anchor || !item.static_svg || !item.title) {
      throw new Error(`动画索引条目不完整：${item.id}`)
    }
  }
  return items
}
