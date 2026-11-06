/**
 * 手绘逐帧动画：正文里照常写 `![]()`，渲染期补上「播放 / 停止」控件。
 *
 * 为什么不在正文里手写 `<figure class="book-motion">`：`visual-style-pack.md` §55 要求
 * 「导出动画须可暂停」，但可暂停标记每处约 390 字符。阶段 1 主线卡在 1.5 万字符预算上
 * （实测 13716，余量 1284；6 张图需约 1900），手写标记既超预算，又要把同一段属性在
 * 47 处复制一遍。渲染期生成只写一次，源文件仍是 `![]()`，字数与 `![]()` 计数门都不受影响。
 *
 * 产出与 bms-book 的既有形式一致：`<figure class="book-motion">` 里放静态首帧
 * （`-start.webp`，打印与首屏可读）、`data-motion-src` 指向动画、一个 `v-book-motion`
 * 按钮。主题早已注册该指令（theme/index.ts → reader.js 的 mountBookMotion），这里只负责
 * 拼出它认识的结构，不重复实现开关逻辑。
 *
 * 只处理「整段只有一张图」的手绘导出。其余写法（图与文字同段、两图连排、行内插图）
 * 会让控件静默消失——页面照常构建、图照常能看——所以这里直接让构建失败，报出文件与行号，
 * 判定与测试共用 `pausable-handraw-rules.mjs`，不靠相邻行启发式。
 *
 * 宽高与 `loading` 一并写死在标记里——`html_block` 不再是 image token，lazy-images 那条
 * 规则看不到它，漏写就会被 check_pages 判红。尺寸读不到时同样直接失败，不猜。
 */
import path from 'node:path'
import type MarkdownIt from 'markdown-it'
import { dimensionsOf } from './lazy-images'
import { planPausableImages } from './pausable-handraw-rules.mjs'

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
      const pageName = env?.relativePath ?? path.basename(pageAbs)

      const { blocks, skipped } = planPausableImages(state.tokens)
      if (skipped.length > 0) {
        const detail = skipped
          .map((s) => `  ${pageName}:${s.line} ${s.slug}（${s.why}）`)
          .join('\n')
        throw new Error(
          `pausable-handraw: 这些手绘动画会失去播放控件，请改成独占一段（前后留空行、段内只有这一张图）：\n${detail}`
        )
      }
      if (blocks.length === 0) return true

      const planned = new Map(blocks.map((b) => [b.index, b]))
      const out: typeof state.tokens = []
      for (let index = 0; index < state.tokens.length; index += 1) {
        const block = planned.get(index)
        if (!block) {
          out.push(state.tokens[index])
          continue
        }

        const startFile = path.resolve(pageDir, `${block.dir}${block.slug}-start.webp`)
        const size = dimensionsOf(startFile)
        if (!size) {
          throw new Error(
            `pausable-handraw: 读不出静态首帧尺寸：${startFile}（手绘动画必须带 -start.webp 打印帧）`
          )
        }

        const token = new state.Token('html_block', '', 0)
        token.map = state.tokens[index].map
        token.content =
          `<figure class="book-motion" data-animation="${block.slug}.webp" data-mode="static">\n` +
          `<img src="${block.dir}${block.slug}-start.webp" width="${size.width}" height="${size.height}"` +
          ` loading="lazy" alt="${escapeAttr(block.alt)}" data-motion-src="${block.dir}${block.slug}.webp">\n` +
          `<button type="button" data-book-motion v-book-motion aria-pressed="false" hidden>播放动画</button>\n` +
          `</figure>`
        out.push(token)
        index += 2 // 吃掉同段的 paragraph_open / inline / paragraph_close
      }
      state.tokens = out
      return true
    })
  }
}
