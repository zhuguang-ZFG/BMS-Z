/**
 * 每页共享一份 MathJax 字形缓存。
 *
 * markdown-it-mathjax3 为每条公式新建一个 MathJax 文档；SVG 输出在 local 模式下
 * 会把整份 <defs> 塞进每条公式，公式一多，页面 chunk 就被同一批字形路径撑到
 * 兆字节级。这里保留它的 $ / $$ 分词器，只替换渲染：同一页的所有公式走同一个
 * 文档与 global 缓存，字形定义在页尾输出一次，公式里只留 <use>。
 *
 * 缓存按页重建，不跨页复用——直接打开或 SPA 跳到任何一页都自带定义。
 * 样式表每页内容相同（实测 2867 字符逐字节一致），由 config 作为全站 <head>
 * 注入一份；样式节点不能留在正文：Vue 客户端模板会丢弃 <style>，SSR 却输出，
 * 首节点就此错位，整页 hydration 全部对不上。
 */
import { mathjax } from 'mathjax-full/js/mathjax.js'
import { TeX } from 'mathjax-full/js/input/tex.js'
import { SVG } from 'mathjax-full/js/output/svg.js'
import { liteAdaptor } from 'mathjax-full/js/adaptors/liteAdaptor.js'
import { RegisterHTMLHandler } from 'mathjax-full/js/handlers/html.js'
import { AssistiveMmlHandler } from 'mathjax-full/js/a11y/assistive-mml.js'
import { AllPackages } from 'mathjax-full/js/input/tex/AllPackages.js'

let sheet = ''

export function mathJaxSvgStyle() {
  if (!sheet) {
    const adaptor = liteAdaptor()
    const handler = RegisterHTMLHandler(adaptor)
    AssistiveMmlHandler(handler)
    const output = new SVG({ fontCache: 'global' })
    const document = mathjax.document('', {
      InputJax: new TeX({ packages: AllPackages }),
      OutputJax: output,
    })
    document.convert('0', { display: false })
    sheet = adaptor.innerHTML(output.styleSheet(document)).trim()
  }
  return sheet
}

export function installMathJaxPageCache(md) {
  const adaptor = liteAdaptor()
  const handler = RegisterHTMLHandler(adaptor)
  AssistiveMmlHandler(handler)
  const input = new TeX({ packages: AllPackages })
  let page = null

  function createPage() {
    const output = new SVG({ fontCache: 'global' })
    return {
      output,
      document: mathjax.document('', { InputJax: input, OutputJax: output }),
      used: false,
    }
  }

  function render(token, display) {
    const current = page || (page = createPage())
    current.used = true
    const node = current.document.convert(token.content, { display })
    const html = adaptor.outerHTML(node)
    return display ? html.replace(/^<mjx-container /, '<mjx-container tabindex="0" ') : html
  }

  md.renderer.rules.math_inline = (tokens, index) => render(tokens[index], false)
  md.renderer.rules.math_block = (tokens, index) => render(tokens[index], true)

  const originalRender = md.render.bind(md)
  md.render = (source, env) => {
    page = createPage()
    try {
      const html = originalRender(source, env)
      if (!page.used) return html
      const cache = page.output.pageElements(page.document)
      // 缓存 SVG 编码进 data 属性。这里必须是运行期绑定（String(...)），不能是
      // 静态值：全静态的节点会被 Vue 压成 createStaticVNode 字符串，VitePress
      // 的 lean bundle 再把字符串换成 ""，水合时就当多余节点删掉，<defs> 一丢，
      // 公式里的 <use> 全部悬空。绑定值 SSR 与客户端算出同一个结果，水合两边一致。
      //
      // MathJax 的 outerHTML 不带 xmlns，而客户端用 image/svg+xml 解析这份载荷。
      // XML 解析器不补默认命名空间：不带 xmlns 时整棵缓存都是 null 命名空间的
      // 元素，importNode 后 <use> 克隆不出任何图形——公式只剩分数线（正文 SVG
      // 由 HTML 解析器按外来内容规则建，命名空间正常），深浅色下字形都是空白。
      let serialized = cache ? adaptor.outerHTML(cache) : ''
      if (serialized && !serialized.includes('xmlns="http://www.w3.org/2000/svg"')) {
        serialized = serialized.replace(/^<svg\b/, '<svg xmlns="http://www.w3.org/2000/svg"')
      }
      const encoded = serialized ? Buffer.from(serialized, 'utf8').toString('base64') : ''
      const cacheHtml = cache
        ? `<div class="mjx-global-cache" hidden :data-mjx-cache="String('${encoded}')"></div>`
        : ''
      return `${html}${cacheHtml}`
    } finally {
      page = null
    }
  }
}
