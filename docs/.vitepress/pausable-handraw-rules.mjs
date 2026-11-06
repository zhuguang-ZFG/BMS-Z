/**
 * 手绘动画的「能不能挂控件」判定：纯函数，插件与测试共用同一份。
 *
 * 为什么要抽出来：渲染规则只换「整段只有一张图」的段落。图片一旦和文字同段、
 * 或两张图连着写，段落里就不止一个子项，规则会**静默跳过**——页面照常构建、
 * 图照常能看，只是没有播放控件。这种失败模式靠人眼发现不了，所以判定必须
 * 由真实的 Markdown token 得出，而不是靠相邻行的字符串启发式。
 *
 * 判定是**全覆盖**的：先把 token 流里所有手绘图片收齐，再减去被接管的那些，
 * 剩下的就是会失去控件的图。这样游离在段落之外的写法也跑不掉。
 *
 * 插件拿到 `skipped` 直接让构建失败；测试拿同一份结果断言各种写法。
 */

/** 只认手绘导出的动画本体；`-start`／`-end` 是打印帧，不做二次包装。 */
export const HANDRAW_EXPORT = /^(.*\/handraw\/exports\/)([a-z0-9-]+)\.webp$/

const isBlankText = (token) => token.type === 'text' && !token.content.trim()

/** 递归收集 token 流里的全部 image token（行内子项可能再嵌 children）。 */
function collectImages(tokens, out = []) {
  for (const token of tokens) {
    if (token.type === 'image') out.push(token)
    if (token.children) collectImages(token.children, out)
  }
  return out
}

function lineOf(...candidates) {
  for (const token of candidates) {
    if (token?.map) return token.map[0] + 1
  }
  return 1
}

/**
 * @param {Array} tokens markdown-it 的块级 token 流（core state 或 `md.parse` 结果）
 * @returns {{ blocks: Array<{index:number, dir:string, slug:string, alt:string, line:number}>,
 *             skipped: Array<{slug:string, line:number, why:string}> }}
 */
export function planPausableImages(tokens) {
  const blocks = []
  const converted = new Set()
  const images = collectImages(tokens)

  for (let index = 0; index < tokens.length; index += 1) {
    const open = tokens[index]
    const inline = tokens[index + 1]
    const close = tokens[index + 2]
    const isParagraph =
      open?.type === 'paragraph_open' &&
      inline?.type === 'inline' &&
      close?.type === 'paragraph_close'
    if (!isParagraph) continue

    const kids = inline.children ?? []
    const found = kids.filter((token) => token.type === 'image')
    if (found.length !== 1) continue

    const image = found[0]
    const match = String(image.attrGet('src') ?? '').match(HANDRAW_EXPORT)
    if (!match) continue
    // 段内还有除空白以外的子项（文字、链接、第二张图…）=> 不接管
    if (kids.some((token) => token !== image && !isBlankText(token))) continue

    converted.add(image)
    blocks.push({
      index,
      dir: match[1],
      slug: match[2],
      alt: image.content,
      line: lineOf(inline, open)
    })
  }

  const skipped = images
    .filter((image) => !converted.has(image))
    .map((image) => {
      const match = String(image.attrGet('src') ?? '').match(HANDRAW_EXPORT)
      if (!match) return null
      const holder = tokens.find((token) => token.children?.includes(image))
      const siblings = holder ? holder.children.filter((t) => t !== image && !isBlankText(t)).length : 0
      return {
        slug: match[2],
        line: lineOf(holder, image),
        why: holder ? `同一段里还有 ${siblings} 个其它子项` : '图片不在独立段落里'
      }
    })
    .filter(Boolean)

  return { blocks, skipped }
}
