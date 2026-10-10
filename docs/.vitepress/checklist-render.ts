/**
 * 把验收清单的 `- [ ]` 变成真能勾选的复选框。
 *
 * 为什么要这一份：首页写着「每篇都有可勾选的过关标准」，而 VitePress 1.6 不带任务
 * 列表渲染，全站 75 条标准在浏览器里是一行行死文本 `<li>[ ] 能画出框图</li>`——那条
 * 声明是假的。这份规则把它变成 `<input type="checkbox">`，配合主题里的 `v-bms-check`
 * 指令（theme/index.ts）把勾选存进这台浏览器的 localStorage。
 *
 * 为什么不注入 `<p>`：tight list 里 `list_item_open` 之后直接就是 `inline`，没有
 * paragraph token；主题给 `.vp-doc p` 加 16px 上下边距，多包一层每条标准白涨约
 * 32px，七篇正文的清单会胖成一堵空墙。
 *
 * 为什么身份取条目文本而不是「第几条」：见 checklist.ts 的头注释。这里把那份口径用到
 * 渲染上，并在构建期当场对账——转换出的框数必须等于源文本数出的条目数，不等就 throw。
 * 宁可不发版，也不给读者一个算错的进度。
 */
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import type MarkdownIt from 'markdown-it'
import type { StateCore, Token } from 'markdown-it/index.js'
import { checklistKey, countTaskItems } from './checklist'

/** 条目正文开头就是清单标记；捕获组用于按长度剥掉它。 */
const TASK_PREFIX = /^(\[[ xX]\])\s+/

/** 清单的说明句：说清数据去哪了，读者才敢勾。 */
const NOTE_TEXT = '勾了会记住，只存在这台浏览器里。'

/** close 类型 → 配对的 open 类型。只跟踪可能包住清单条目的容器。 */
const OPEN_OF_CLOSE: Readonly<Record<string, string>> = {
  paragraph_close: 'paragraph_open',
  blockquote_close: 'blockquote_open',
  list_item_close: 'list_item_open',
  bullet_list_close: 'bullet_list_open',
  ordered_list_close: 'ordered_list_open'
}
const TRACKED = new Set(Object.values(OPEN_OF_CLOSE))

/** 打开的容器：token 本身 + 它在 state.tokens 里的下标（插入提示语要用）。 */
type Frame = { token: Token; index: number }
/** 待插入：下标 + 要插进去的 token。下标是插入前的位置。 */
type Insertion = { at: number; tokens: Token[] }

/** 页键是中文路径，属性值里的引号与和号必须转，否则破标签。 */
function escapeAttr(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/"/g, '&quot;')
}

/**
 * 当前页在 docs/ 下的相对路径，直接当 localStorage 的页键。
 *
 * 不用 location.pathname 反推：中文文件名的 pathname 是百分号编码的，而首页 loader
 * 烤出来的链接是原文中文，两边对不上。构建期把这一个值戳进每个控件的 data-bms-page，
 * 读写两头同源，不存在编码差异。
 */
function pageKeyOf(env: { path?: string; relativePath?: string } | undefined): string | null {
  if (!env) return null
  // 两条来源必须落到同一个形状：正斜杠、相对 docs/。首页 loader 用的就是这个形状，
  // 差一个反斜杠或一段前缀，读者勾的对勾就找不回来了。
  const raw = env.relativePath ?? (env.path ? path.relative(path.resolve('docs'), path.resolve(env.path)) : null)
  if (!raw || raw.startsWith('..')) return null
  return raw.split(path.sep).join('/')
}

/**
 * 一个控件。不带 checked 属性：勾选状态由指令写 DOM property，产物永远是未勾的中性
 * 起点，服务端渲染与客户端恢复不可能对不上，也就不会有 hydration 告警。
 */
function checkboxHtml(page: string, key: string): string {
  const open = '<label class="checklist-label">'
  const box = '<input class="checklist-box" type="checkbox" v-bms-check'
  const pageAttr = ' data-bms-page="' + escapeAttr(page) + '"'
  const keyAttr = ' data-bms-key="' + escapeAttr(key) + '">'
  return open + box + pageAttr + keyAttr
}

/** 从栈顶往下找包着这条 inline 的 list_item；tight 直接命中，loose 隔一个段落。 */
function enclosingItem(stack: Frame[]): { item: Token; list: Token; listIndex: number } | null {
  for (let depth = stack.length - 1; depth >= 0; depth--) {
    const entry = stack[depth]
    if (entry.token.type === 'list_item_open') {
      const parent = stack[depth - 1]
      if (!parent) return null
      const kind = parent.token.type
      const isList = kind === 'bullet_list_open' || kind === 'ordered_list_open'
      if (!isList) return null
      return { item: entry.token, list: parent.token, listIndex: parent.index }
    }
    // 再往上就出清单了：段落之外的容器一律不算。
    if (entry.token.type !== 'paragraph_open') return null
  }
  return null
}

/**
 * 每页只在第一个清单前发一句提示语。bms-resources.md 的 24 条分在四个独立清单里，
 * 按清单发就会发四遍。
 */
function noteTokens(state: StateCore): Token[] {
  const open = new state.Token('paragraph_open', 'p', 1)
  open.attrSet('class', 'checklist-note')
  const inline = new state.Token('inline', '', 0)
  inline.content = NOTE_TEXT
  const text = new state.Token('text', '', 0)
  text.content = NOTE_TEXT
  inline.children = [text]
  return [open, inline, new state.Token('paragraph_close', 'p', -1)]
}

export function checklistTaskItems(): (md: MarkdownIt) => void {
  return (md: MarkdownIt) => {
    // 挂在链尾：config(md) 在 VitePress 自带的插件之后跑，此时 inline token 已经
    // 切好，文本、链接、加粗都是现成的 children，只需要在它前面挂一个 <label>。
    md.core.ruler.push('bms-checklist', (state: StateCore) => {
      const env = state.env as { path?: string; relativePath?: string } | undefined
      const page = pageKeyOf(env)
      if (!page) return true

      const stack: Frame[] = []
      const pending: Insertion[] = []
      let boxes = 0
      let noteAt = -1

      for (let index = 0; index < state.tokens.length; index++) {
        const token = state.tokens[index]
        if (token.nesting === 1) {
          if (TRACKED.has(token.type)) stack.push({ token, index })
          continue
        }
        if (token.nesting === -1) {
          const top = stack[stack.length - 1]
          if (top && top.token.type === OPEN_OF_CLOSE[token.type]) stack.pop()
          continue
        }
        if (token.type !== 'inline') continue

        const placed = enclosingItem(stack)
        if (!placed) continue
        const marker = TASK_PREFIX.exec(token.content)
        if (!marker) continue
        const first = token.children?.[0]
        // 剥不掉就不动：宁可这一格留成死文本，也不产出半个复选框加一行残句。
        // 真出现这种条目，文末的对账会报框数不符、当场发不出去。
        if (!first || first.type !== 'text') continue
        if (!first.content.startsWith(marker[1])) continue

        // 身份取「剥掉标记后的第一行」，与 checklist.ts 逐行数条目的口径一致。
        const cut = marker[0].length
        const text = token.content.slice(cut).split('\n')[0].trim()
        first.content = first.content.slice(cut)
        token.content = token.content.slice(cut)
        // attrSet 而不是 attrJoin：同一份 ul 会被它每条 criteria 命中一次，
        // join 会把类名重复堆到属性里。markdown-it 不给列表加 class，覆盖无风险。
        placed.item.attrSet('class', 'checklist-item')
        placed.list.attrSet('class', 'contains-task-list')
        const before = new state.Token('html_inline', '', 0)
        before.content = checkboxHtml(page, checklistKey(page, text))
        const after = new state.Token('html_inline', '', 0)
        after.content = '</label>'
        pending.push({ at: index, tokens: [before] })
        pending.push({ at: index + 1, tokens: [after] })
        boxes += 1
        if (noteAt < 0) noteAt = placed.listIndex
      }

      // 倒序 splice：正序改会让后面所有下标整体右移，第二条起就插到别处去了。
      pending.sort((a, b) => b.at - a.at)
      for (const insert of pending) state.tokens.splice(insert.at, 0, ...insert.tokens)
      if (noteAt >= 0) state.tokens.splice(noteAt, 0, ...noteTokens(state))

      // 对账：转换出的框数必须等于源文本里数出的条目数，差一条就当场停。
      const abs = env?.path ? path.resolve(env.path) : path.join(path.resolve('docs'), page)
      if (existsSync(abs)) {
        const expected = countTaskItems(readFileSync(abs, 'utf8'))
        if (expected !== boxes) {
          throw new Error(`验收清单对账不上：${page} 源文本 ${expected} 条、渲染出 ${boxes} 个框`)
        }
      }
      return true
    })
  }
}