/**
 * 正文图片：首屏之外的都懒加载，并且每张都带上真实像素尺寸。
 *
 * 为什么要管：一页最多 36 张图（阶段 6），合计 1.4MB；实拍照片单张最大 457KB。
 * 浏览器一解析到 `<img>` 就开始下载，手机上翻开一篇文章的首屏要为 30 多张永远
 * 看不到的图买单。`loading="lazy"` 让首屏只取第一张。
 *
 * 为什么两件事必须一起做：懒加载会把塌陷推到滚动那一刻——没有宽高的图一到就
 * 把下面的文字顶开，正看着动画会跳一下。主题的默认样式是 `img{max-width:100%;
 * height:auto}`，只要把真实像素尺寸写进 `width`/`height`，浏览器就按宽高比先把位置
 * 留出来（现代浏览器都支持），滚动加载时版面纹丝不动。
 *
 * 尺寸从源文件读，不靠约定：SVG 读 viewBox，JPEG 读 SOF 段，PNG 读 IHDR 头。
 * 读不出的（外链、data:、异形文件）就只加懒加载，绝不写错的尺寸——写错宽高比
 * 比不写更糟。
 */
import { readFileSync } from 'node:fs'
import path from 'node:path'
import type MarkdownIt from 'markdown-it'
import type { StateCore, Token } from 'markdown-it/index.js'

/** 尺寸缓存：同一张图在多页复用（动画会被导读页重复引用）。 */
const dimCache = new Map<string, { width: number; height: number } | null>()

function dimensionsOf(file: string): { width: number; height: number } | null {
  if (dimCache.has(file)) return dimCache.get(file)!
  let result: { width: number; height: number } | null = null
  try {
    if (file.endsWith('.svg')) {
      const text = readFileSync(file, 'utf8').slice(0, 4000)
      const viewBox = text.match(/viewBox="\s*[-\d.]+\s+[-\d.]+\s+([\d.]+)\s+([\d.]+)\s*"/)
      if (viewBox) {
        result = { width: Number(viewBox[1]), height: Number(viewBox[2]) }
      } else {
        const w = text.match(/\swidth="([\d.]+)(?:px)?"/)
        const h = text.match(/\sheight="([\d.]+)(?:px)?"/)
        if (w && h) result = { width: Number(w[1]), height: Number(h[1]) }
      }
    } else {
      const buffer = readFileSync(file)
      if (buffer.subarray(0, 8).toString('hex') === '89504e470d0a1a0a') {
        result = { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) }
      } else if (buffer[0] === 0xff && buffer[1] === 0xd8) {
        // JPEG：扫到 SOF0..SOF15（跳过 DHT/JPEG 扩展等 0xC4/0xC8/0xCC）拿宽高。
        for (let i = 2; i + 9 < buffer.length; ) {
          if (buffer[i] !== 0xff) {
            i += 1
            continue
          }
          const marker = buffer[i + 1]
          if (marker >= 0xc0 && marker <= 0xcf && marker !== 0xc4 && marker !== 0xc8 && marker !== 0xcc) {
            result = { width: buffer.readUInt16BE(i + 7), height: buffer.readUInt16BE(i + 5) }
            break
          }
          i += 2 + buffer.readUInt16BE(i + 2)
        }
      }
    }
  } catch {
    result = null
  }
  dimCache.set(file, result)
  return result
}

/** 递归收集 image token，保持文档顺序（图片可能嵌在链接的 children 里）。 */
function collectImages(tokens: Token[], out: Token[] = []): Token[] {
  for (const token of tokens) {
    if (token.type === 'image') out.push(token)
    if (token.children) collectImages(token.children, out)
  }
  return out
}

/** 只处理站内相对路径；外链、data:、根绝对路径一律不猜本地文件。 */
function resolveLocalSrc(src: string, pageDir: string): string | null {
  if (!src || /^(?:[a-z][a-z0-9+.-]*:)?\/\//i.test(src) || src.startsWith('data:')) return null
  if (src.startsWith('/')) return null
  const clean = decodeURIComponent(src.split('#')[0].split('?')[0])
  return path.resolve(pageDir, clean)
}

export function lazyImagesWithDimensions(): (md: MarkdownIt) => void {
  return (md: MarkdownIt) => {
    md.core.ruler.push('bms-lazy-images', (state: StateCore) => {
      const env = state.env as { path?: string; relativePath?: string } | undefined
      const pageAbs = env?.path ?? env?.relativePath
      if (!pageAbs) return true
      const pageDir = path.dirname(path.resolve(pageAbs))

      const images = collectImages(state.tokens)
      // 每页第一张留在首屏，照常立即加载；其余等靠近视口再下载。
      images.forEach((image, index) => {
        if (index > 0) image.attrSet('loading', 'lazy')
        const file = resolveLocalSrc(String(image.attrGet('src') ?? ''), pageDir)
        const dimensions = file ? dimensionsOf(file) : null
        if (dimensions) {
          image.attrSet('width', String(dimensions.width))
          image.attrSet('height', String(dimensions.height))
        }
      })
      return true
    })
  }
}
