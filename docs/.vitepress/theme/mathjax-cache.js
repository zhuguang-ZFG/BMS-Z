/**
 * 把构建期编码的 MathJax 字形缓存插回页面。
 *
 * 缓存 SVG 直接写进正文时，Vue 会把它编译成 VNode 并在水合时丢掉 <defs>，
 * 公式里的 <use> 就指向不存在的字形。构建器把 SVG 编码进 data 属性，并且
 * 用运行期绑定保住这个节点（静态节点会被 lean bundle 清空）；这里在挂载后
 * 用 XML 解析器把 SVG 插回，按外来内容规则解析。
 *
 * SVG 挂到 #app 之外的宿主节点：留在 .vp-doc 里会被下一次路由渲染连带清掉。
 * 同页重复调用按载荷前缀判重，不重复解析。
 */
const HOST_ID = 'mjx-global-cache-host'

function payloadKey(encoded) {
  return `${encoded.length}:${encoded.slice(0, 48)}`
}

export function mountMathJaxCache(root = document) {
  const holders = root.querySelectorAll('.mjx-global-cache[data-mjx-cache]')
  const encoded = holders[holders.length - 1]?.dataset.mjxCache || ''
  let host = document.getElementById(HOST_ID)
  if (!encoded) {
    host?.remove()
    return
  }
  const key = payloadKey(encoded)
  if (host && host.dataset.mjxKey === key) return
  const binary = atob(encoded)
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0))
  const parsed = new DOMParser().parseFromString(new TextDecoder().decode(bytes), 'image/svg+xml')
  if (parsed.documentElement.nodeName !== 'svg') return
  if (!host) {
    host = document.createElement('div')
    host.id = HOST_ID
    host.hidden = true
    document.body.appendChild(host)
  }
  host.replaceChildren(document.importNode(parsed.documentElement, true))
  host.dataset.mjxKey = key
}
