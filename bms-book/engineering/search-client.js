/**
 * 工程深研册的离线全文搜索（浏览器侧实现）。
 *
 * 为什么索引在浏览器里建：单文件书要能整体拷走、断网打开，构建期生成的索引
 * 若分成 JSON 就得再 fetch 一次，file:// 下直接失效；所以第一次输入时才走一遍
 * DOM，之后复用同一份索引。加载时除了找一次搜索框，不碰正文。
 *
 * 为什么复用 tokenizeCjk：MiniSearch 默认只在空白和标点处切词，
 * 「母线电压已经起来了」会整句成为一个词条，搜「母线」命中不了句中的词。
 * docs/.vitepress/cjk-search.ts 已有二元组分词，索引端和查询端必须用同一个
 * 函数，否则两端词表分家。
 *
 * 结果一律用 textContent 写入：正文来自 Markdown，仍按不可信内容处理，
 * 不走 innerHTML；链接目标只能是书中真实存在的 id 片段。
 */

import MiniSearch from 'minisearch'
import { tokenizeCjk } from '../../docs/.vitepress/cjk-search.ts'

export const SEARCH_HINT =
  '输入中文词或句子片段；第一次搜索时才建立全书索引，句中的词也能搜到。'

const MAX_RESULTS = 20

// 不进索引的东西：脚本/样式/矢量图是噪声，MathJax 容器里同时有排版副本和
// 辅助 MathML，导航与搜索框本身也不是正文。层级过滤用 hidden 隐藏正文，
// 但这里不跳过 hidden：被过滤的段落仍须搜得到，选中结果时由层级脚本展开。
const SKIP_TAGS = new Set([
  'script',
  'style',
  'noscript',
  'template',
  'svg',
  'nav',
  'mjx-container',
  'mjx-assistive-mml',
])
const SKIP_CLASSES = ['book-search', 'level-bar', 'header-anchor']

const SEARCH_CSS = `
.book-search { margin: 1.2em 0 2em; padding: 1em 1.1em; border: 1px solid var(--line, #d8d2c4); border-radius: 6px; background: #fbf8f1; }
.book-search__title { margin: 0 0 .6em; padding: 0; border: 0; font-size: 1.05rem; }
.book-search__form { display: flex; flex-wrap: wrap; gap: .5em; align-items: center; }
.book-search__label { font-weight: 600; }
.book-search__input { flex: 1 1 16rem; min-width: 0; padding: .35em .55em; border: 1px solid var(--line, #d8d2c4); border-radius: 4px; font: inherit; background: #fff; color: inherit; }
.book-search__submit, .book-search__clear { padding: .3em .9em; border: 1px solid var(--line, #d8d2c4); border-radius: 4px; background: #fff; color: inherit; font: inherit; cursor: pointer; }
.book-search__submit { background: var(--accent, #1f4e79); border-color: var(--accent, #1f4e79); color: #fff; }
.book-search__status { margin: .6em 0 0; font-size: .85rem; color: #5a6a76; }
.book-search__results { margin: .8em 0 0; padding: 0; list-style: none; }
.book-search__item { padding: .65em 0; border-top: 1px dashed var(--line, #d8d2c4); }
.book-search__item:first-child { border-top: 0; padding-top: 0; }
.book-search__hit { color: var(--accent, #1f4e79); font-weight: 600; text-decoration: none; }
.book-search__hit:hover, .book-search__hit:focus-visible { text-decoration: underline; }
.book-search__meta { display: block; margin-top: .15em; font-size: .78rem; color: #5a6a76; }
.book-search__snippet { display: block; margin-top: .2em; font-size: .92rem; }
.book-search__noscript { margin: .5em 0 0; font-size: .85rem; color: #5a6a76; }
@media print { .book-search { display: none !important; } }
`

function tagName(element) {
  return element && element.tagName ? String(element.tagName).toLowerCase() : ''
}

function normalized(value) {
  return String(value == null ? '' : value)
    .replace(/\s+/g, ' ')
    .trim()
}

function skipElement(element) {
  if (SKIP_TAGS.has(tagName(element))) return true
  const classList = element.classList
  if (classList && typeof classList.contains === 'function') {
    for (let i = 0; i < SKIP_CLASSES.length; i += 1) {
      if (classList.contains(SKIP_CLASSES[i])) return true
    }
  }
  if (
    typeof element.getAttribute === 'function' &&
    element.getAttribute('aria-hidden') === 'true'
  ) {
    return true
  }
  return false
}

function collectText(node, out) {
  for (let child = node.firstChild; child; child = child.nextSibling) {
    if (child.nodeType === 3) {
      if (child.nodeValue) out.push(child.nodeValue)
    } else if (child.nodeType === 1 && !skipElement(child)) {
      collectText(child, out)
    }
  }
}

export function textOf(element) {
  if (!element || skipElement(element)) return ''
  const out = []
  collectText(element, out)
  return normalized(out.join(''))
}

function directHeading(chapter, tag) {
  const children = chapter && chapter.children ? chapter.children : []
  for (let i = 0; i < children.length; i += 1) {
    if (tagName(children[i]) === tag) return textOf(children[i])
  }
  return ''
}

/**
 * 把 main > section.book-chapter 切成以 h2 为界的小节。
 *
 * 每个小节带真实片段 URL：h2 的 id 优先，没有 id 就退回本章的 id（导语、
 * 章首 aside 都归到这里）。details 里的答案不展开也照样收进 text——
 * 「收进索引」和「在页面上展开」是两件事。
 */
export function collectSections(root) {
  const main =
    root ||
    (typeof document !== 'undefined' && document
      ? document.querySelector('main')
      : null)
  if (!main || !main.children) return []

  const sections = []

  for (let c = 0; c < main.children.length; c += 1) {
    const chapter = main.children[c]
    if (tagName(chapter) !== 'section') continue
    if (!chapter.classList || !chapter.classList.contains('book-chapter')) continue

    const chapterId = chapter.id || ''
    const chapterTitle = directHeading(chapter, 'h1') || chapterId
    const chapterUrl = chapterId ? '#' + chapterId : ''
    let current = {
      title: chapterTitle || '本章导读',
      chapter: chapterTitle,
      url: chapterUrl,
    }
    let parts = []

    const flush = () => {
      const text = normalized(parts.join(' '))
      if (current && (current.title || text)) {
        sections.push({
          title: current.title,
          chapter: current.chapter,
          url: current.url,
          text,
        })
      }
      parts = []
    }

    for (let i = 0; i < chapter.children.length; i += 1) {
      const child = chapter.children[i]
      const tag = tagName(child)
      // 章标题只作 title，不再混进正文；否则同一句话在索引里出现两遍。
      if (tag === 'h1') continue
      if (tag === 'h2') {
        flush()
        const heading = textOf(child)
        const id = child.id || ''
        current = {
          title: heading || chapterTitle || '未命名小节',
          chapter: chapterTitle,
          url: id ? '#' + id : chapterUrl,
        }
        continue
      }
      const text = textOf(child)
      if (text) parts.push(text)
    }
    flush()
  }

  return sections.filter((section) => section.title || section.text)
}

/**
 * 建索引。tokenize 交给共享的中文分词，查询时 MiniSearch 用同一函数切词；
 * 正文按二元组入索引，所以句中任意两字以上的中文串都能靠词条命中。
 */
export function buildSearchIndex(sections) {
  const index = new MiniSearch({
    fields: ['title', 'text'],
    storeFields: ['title', 'url', 'chapter'],
    tokenize: tokenizeCjk,
    searchOptions: { boost: { title: 2 }, prefix: true, combineWith: 'OR' },
  })
  index.addAll(
    sections.map((section, i) => ({
      id: i,
      title: section.title,
      text: section.text,
      url: section.url,
      chapter: section.chapter,
    })),
  )
  return index
}

/** 查询并还原成书内小节；id 是 sections 的下标，和索引文档一一对应。 */
export function searchSections(index, sections, rawQuery) {
  const query = normalized(rawQuery)
  if (!index || !sections || !query) return { query, hits: [], total: 0 }

  const results = index.search(query)
  const seen = new Set()
  const hits = []
  for (let i = 0; i < results.length; i += 1) {
    const id = results[i].id
    if (seen.has(id)) continue
    seen.add(id)
    const section = sections[id]
    if (!section) continue
    hits.push({ score: results[i].score, section })
  }
  return { query, hits, total: hits.length }
}

function findMatch(source, query) {
  if (!query) return null
  const haystack = source.toLowerCase()
  const direct = haystack.indexOf(query.toLowerCase())
  if (direct >= 0) return { at: direct, length: query.length }

  let best = null
  for (const token of tokenizeCjk(query)) {
    const needle = token.toLowerCase()
    if (!needle) continue
    const at = haystack.indexOf(needle)
    if (at < 0) continue
    if (!best || at < best.at || (at === best.at && token.length > best.length)) {
      best = { at, length: token.length }
    }
  }
  return best
}

/** 结果摘要窗口：优先围住命中词，命中不了就取开头。 */
export function snippetFor(text, query, radius = 48) {
  const source = normalized(text)
  if (!source) return ''
  const match = findMatch(source, normalized(query))
  if (!match) {
    return source.length <= radius * 2 ? source : source.slice(0, radius * 2) + '…'
  }
  const start = Math.max(0, match.at - radius)
  const end = Math.min(source.length, match.at + match.length + radius)
  return (
    (start > 0 ? '…' : '') +
    source.slice(start, end) +
    (end < source.length ? '…' : '')
  )
}

function installStyles(doc) {
  if (doc.getElementById('engineering-search-style')) return
  const style = doc.createElement('style')
  style.id = 'engineering-search-style'
  style.textContent = SEARCH_CSS
  const head = doc.head
  if (head) head.appendChild(style)
}

/** 挂载：只绑定事件，索引推迟到第一次查询。 */
export function mountSearch(win) {
  const doc = win && win.document
  if (!doc) return

  // 解析还没结束就等 DOMContentLoaded：这段脚本在 body 末尾，等一拍不会慢到
  // 用户发现，却能保证层级脚本、正文与搜索框都已经在树上。
  if (doc.readyState === 'loading') {
    doc.addEventListener('DOMContentLoaded', () => mountSearch(win), { once: true })
    return
  }

  const root = doc.querySelector('.book-search')
  if (!root) return
  if (root.getAttribute('data-engineering-search') === 'ready') return

  const form = root.querySelector('form')
  const input = root.querySelector('input[type="search"]')
  const status = root.querySelector('.book-search__status')
  const list = root.querySelector('.book-search__results')
  const clear = root.querySelector('.book-search__clear')
  if (!form || !input || !status || !list) return

  root.setAttribute('data-engineering-search', 'ready')
  installStyles(doc)

  let sections = null
  let index = null
  let sequence = 0

  function setStatus(message) {
    const text = String(message == null ? '' : message)
    if (status.textContent !== text) status.textContent = text
  }

  function ensureIndex() {
    if (index) return true
    const main = doc.querySelector('main')
    if (!main) return false
    const found = collectSections(main)
    if (!found.length) return false
    sections = found
    index = buildSearchIndex(found)
    return true
  }

  function reset() {
    sequence += 1
    input.value = ''
    list.replaceChildren()
    setStatus(SEARCH_HINT)
  }

  function render(query, hits) {
    const shown = hits.slice(0, MAX_RESULTS)
    const fragment = doc.createDocumentFragment()

    for (let i = 0; i < shown.length; i += 1) {
      const section = shown[i].section
      const item = doc.createElement('li')
      item.className = 'book-search__item'

      let hit
      if (section.url) {
        hit = doc.createElement('a')
        hit.setAttribute('href', section.url)
        hit.setAttribute('data-engineering-search-target', section.url.slice(1))
      } else {
        hit = doc.createElement('span')
      }
      hit.className = 'book-search__hit'
      hit.textContent = section.title || section.chapter || '未命名小节'
      item.appendChild(hit)

      if (section.chapter && section.chapter !== section.title) {
        const meta = doc.createElement('span')
        meta.className = 'book-search__meta'
        meta.textContent = section.chapter
        item.appendChild(meta)
      }

      const snippet = snippetFor(section.text, query)
      if (snippet) {
        const text = doc.createElement('span')
        text.className = 'book-search__snippet'
        text.textContent = snippet
        item.appendChild(text)
      }

      fragment.appendChild(item)
    }

    list.replaceChildren(fragment)

    if (!hits.length) {
      setStatus('没有找到「' + query + '」的匹配。试试更短的中文词，或换一个说法。')
    } else if (hits.length > shown.length) {
      setStatus(
        '找到 ' +
          hits.length +
          ' 条结果，先显示前 ' +
          shown.length +
          ' 条；加长关键词可以缩小范围。',
      )
    } else {
      setStatus('找到 ' + hits.length + ' 条结果。')
    }
  }

  function run() {
    // 同步执行也留序号：以后若把建索引挪进 rAF/worker，旧查询不会盖掉新结果。
    sequence += 1
    const seq = sequence
    const query = normalized(input.value)

    if (!query) {
      list.replaceChildren()
      setStatus(SEARCH_HINT)
      return
    }
    if (!ensureIndex()) {
      list.replaceChildren()
      setStatus('这本书里没有可搜索的章节（找不到 main > section.book-chapter）。')
      return
    }

    const found = searchSections(index, sections, query)
    if (seq !== sequence) return
    render(query, found.hits)
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault()
    run()
  })
  input.addEventListener('input', run)
  input.addEventListener('search', run)
  input.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return
    if (!input.value && !list.childNodes.length) return
    event.preventDefault()
    reset()
  })
  if (clear) {
    clear.addEventListener('click', () => {
      reset()
      input.focus()
    })
  }

  list.addEventListener('click', (event) => {
    const target = event.target
    const link =
      target && typeof target.closest === 'function'
        ? target.closest('a[data-engineering-search-target]')
        : null
    if (!link) return

    const id = link.getAttribute('data-engineering-search-target')
    if (!id) return

    // 事件契约：层级脚本在 document 上监听，同步展开目标段与 details；
    // 搜索这边不碰 hidden、不改层级，浏览器随后按真实 href 片段跳转。
    const custom = new win.CustomEvent('engineering-search-navigate', {
      detail: { id }, bubbles: true, cancelable: true,
    })
    if (!root.dispatchEvent(custom)) event.preventDefault()
  })
}
