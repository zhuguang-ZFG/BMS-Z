/**
 * 验收清单的唯一口径：从源文本数出条目、给条目生成稳定身份。
 *
 * 为什么要有这一份：渲染插件（checklist-render.ts）把 `- [ ]` 变成真控件，
 * 首页 loader（../index.data.ts）要把同一批条目算成电池组的格数。两边各数各的，
 * 读者勾了 12 格、首页说这页只有 11 格——最容易发生、也最难发现的错法。
 * 共用这一份，两边永远同数；渲染期还有一条断言把不一致直接判红。
 *
 * 为什么按「条目文本」而不是「第几条」生成身份：清单会增删、会重排。位置编号
 * 一漂移，勾在「能画出框图」上的对勾就跑到「能背出五大保护」上，进度静默错位、
 * 没人报错。文本本身才是这条 criteria 的身份；改写措辞等于换了条标准，那格该回
 * 到未勾。
 *
 * window 只出现在文件末尾那两个状态函数里，而且 typeof 守卫在前：本文件被构建链
 * 两头 import——渲染插件与首页 loader 在 VitePress 的 Node 进程里跑，电池组在浏览器
 * 里跑。数条目与读状态共用一份定义，进度才不可能算成两个数。
 */

/** `- [ ] xxx` / `- [x] xxx`，也认 `*`、`+` 项目符号；捕获组是条目正文。 */
const TASK_RE = /^\s*[-*+]\s+\[[ xX]\]\s*(.*)$/
/** 围栏：三个反引号或三个波浪号，允许最多三个前导空格（CommonMark）。 */
const FENCE_RE = /^ {0,3}(`{3,}|~{3,})/

/**
 * 逐行扫，按 CommonMark 的口径跳过围栏内的内容——正文里有用代码块示范清单写法的
 * 地方，那些不是真的 criteria。
 */
export function extractTaskItems(source: string): string[] {
  const items: string[] = []
  let fence: string | null = null
  for (const line of source.split(/\r?\n/)) {
    const marker = line.match(FENCE_RE)
    if (marker) {
      // 同种围栏才关闭；一直没关闭就一直跳过，避免把示例当标准。
      if (fence === null) fence = marker[1][0]
      else if (marker[1][0] === fence) fence = null
      continue
    }
    if (fence !== null) continue
    const task = line.match(TASK_RE)
    if (task && task[1].trim() !== '') items.push(task[1].trim())
  }
  return items
}

export function countTaskItems(source: string): number {
  return extractTaskItems(source).length
}

/** FNV-1a 32 位：无依赖，构建期与浏览器跑出的结果一致。 */
function fnv1a(text: string, seed: number): number {
  let hash = seed >>> 0
  for (let i = 0; i < text.length; i++) {
    hash ^= text.charCodeAt(i)
    hash = Math.imul(hash, 0x01000193) >>> 0
  }
  return hash >>> 0
}

function hex32(value: number): string {
  return value.toString(16).padStart(8, '0')
}

/**
 * 一格的身份 = 页 + 条目文本。带页前缀，是因为同一条措辞可能出现在两篇里
 * （阶段正文与「精通自检清单」有重复句），跨页串味就是进度算错。
 * 拼上文本长度，是为了切开只靠分隔符切不干净的组合；两次不同种子把 32 位扩到
 * 64 位，全站 75 条条目撞号的概率可以忽略。
 */
export function checklistKey(page: string, text: string): string {
  const salted = page + '#' + text.length + '#' + text
  return hex32(fnv1a(salted, 0x811c9dc5)) + hex32(fnv1a(salted, 0x01000193))
}

/** localStorage 的键：换形状就换键名，别让旧数据以半套字段的方式活下来。 */
export const STORE_KEY = 'bms.checklist.v1'

/** { 页相对路径: { 条目键: 1 } }。值只存 1，勾没勾就是键在不在。 */
export type ChecklistStore = Record<string, Record<string, 1>>

/**
 * 读这份状态，两头都用它：主题里的 v-bms-check 负责写，首页电池组负责算。
 *
 * 构建期（Node）没有 window，返回空态而不是抛——首页 loader 与渲染插件都 import
 * 这一份，只有浏览器里才有真数据。所以首页 SSR 出来的骨架必然是「未测量」。
 */
export function readChecklistStore(): ChecklistStore {
  if (typeof window === 'undefined') return {}
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORE_KEY) || 'null')
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {}
  } catch {
    return {}
  }
}

/** 写：隐私模式与配额满都静默失败——勾得动但记不住，比整页报错强。 */
export function writeChecklistStore(store: ChecklistStore): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(STORE_KEY, JSON.stringify(store))
  } catch {
    /* 记住这件事不影响读正文，不为此打断阅读。 */
  }
}
