/**
 * 手绘逐帧动画：正文里照常写 `![]()`，渲染期补上「播放 / 停止」控件。
 *
 * 为什么不在正文里手写 `<figure class="book-motion">`：`visual-style-pack.md` §55 要求
 * 「导出动画须可暂停」，但可暂停标记每处约 390 字符。阶段 1 主线卡在 1.5 万字符预算上
 * （实测 13716，余量 1284；6 张图需约 1900），手写标记既超预算，又要把同一段属性在
 * 45 处复制一遍。渲染期生成只写一次，源文件仍是 `![]()`，字数与 `![]()` 计数门都不受影响。
 *
 * 产出与 bms-book 的既有形式一致：`<figure class="book-motion">` 里放静态首帧
 * （`-start.webp`，打印与首屏可读）、`data-motion-src` 指向动画、一个 `v-book-motion`
 * 按钮。主题早已注册该指令（theme/index.ts → reader.js 的 mountBookMotion），这里只负责
 * 拼出它认识的结构，不重复实现开关逻辑。
 *
 * 只处理「整段只有一张图」的手绘导出；句子中间的插图保持原样。宽高与 `loading` 一并写死
 * 在标记里——`html_block` 不再是 image token，lazy-images 那条规则看不到它，漏写就会被
 * check_pages 判红。尺寸读不到时直接让构建失败，不猜：写错宽高比不写更糟。
 */
import path from 'node:path'
import type MarkdownIt from 'markdown-it'
import { dimensionsOf } from './lazy-images'

/** 只认手绘导出的动画本体；`-start`／`-end` 是打印帧，不做二次包装。 */
const HANDRAW_EXPORT = /^(.*\/handraw\/exports\/)([a-z0-9-]+)\.webp$/

function escapeAttr(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function pausableHandrawImages(): (md: MarkdownIt) => void {
  return (md: MarkdownIt) => {
    md.core.ruler.push('bms-pausable-handraw', (state) => {
      const env = state.env as { path?: string; relativePath?: string } | undefined
      const pageAbs = env?.path ?? env?.relativePath
      if (!pageAbs) return true
      const pageDir = path.dirname(path.resolve(pageAbs))

      const tokens = state.tokens
      const out: typeof tokens = []
      for (let index = 0; index < tokens.length; index += 1) {
        const open = tokens[index]
        const inline = tokens[index + 1]
        const close = tokens[index + 2]
        const standalone =
          open.type === 'paragraph_open' &&
          inline?.type === 'inline' &&
          close?.type === 'paragraph_close'

        const kids = standalone ? (inline.children ?? []).filter((t) => t.type !== 'text' || t.content.trim()) : []
        const image = kids.length === 1 && kids[0].type === 'image' ? kids[0] : null
        const src = image ? String(image.attrGet('src') ?? '') : ''
        const match = src.match(HANDRAW_EXPORT)

        if (!image || !match) {
          out.push(open)
          continue
        }

        const [, dir, slug] = match
        const startFile = path.resolve(pageDir, `${dir}${slug}-start.webp`)
        const size = dimensionsOf(startFile)
        if (!size) {
          throw new Error(
            `pausable-handraw: 读不出静态首帧尺寸：${startFile}（手绘动画必须带 -start.webp 打印帧）`
          )
        }

        const block = new state.Token('html_block', '', 0)
        block.map = open.map
        block.content =
          `<figure class="book-motion" data-animation="${slug}.webp" data-mode="static">\n` +
          `<img src="${dir}${slug}-start.webp" width="${size.width}" height="${size.height}"` +
          ` loading="lazy" alt="${escapeAttr(image.content)}" data-motion-src="${dir}${slug}.webp">\n` +
          `<button type="button" data-book-motion v-book-motion aria-pressed="false" hidden>播放动画</button>\n` +
          `</figure>`
        out.push(block)
        index += 2
      }
      state.tokens = out
      return true
    })
  }
}
