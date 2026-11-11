/**
 * 工程深研册的搜索装配：产出一段可内联的 HTML 和一段自包含的浏览器脚本。
 *
 * 为什么由 Node 现打包：全书必须是单文件、断网可用，搜索既不能运行时 fetch
 * 索引，也不能引 CDN。这里用仓库里已装的 esbuild 把 MiniSearch 与站点的
 * docs/.vitepress/cjk-search.ts 一起打进 IIFE，装配侧只拿到两个字符串，
 * 直接写进 <main> 与 </body> 前即可。
 *
 * 约定：
 * - html 只含语义结构（form/状态区/结果列表），样式由脚本挂载时注入；
 * - script 不含任何 <script> 标签，Main 直接把它放进内联脚本；
 * - script 不加载网络资源，也不出现会截断内联脚本的 `</script`；第三方许可保留。
 *
 * 直接运行（node bms-book/engineering/search.mjs）会打印 JSON：{html, script}，
 * 与 bms-book/engineering/render.mjs 的 stdout 约定一致，便于 Python 装配复用。
 */

import path from 'node:path'
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import process from 'node:process'
import { fileURLToPath, pathToFileURL } from 'node:url'

import { build as esbuild } from 'esbuild'

import { SEARCH_HINT } from './search-client.js'

const HERE = path.dirname(fileURLToPath(import.meta.url))

// 入口只做一件事：挂载。所有逻辑在 search-client.js 里，Node 测试与浏览器
// 打包共用同一份实现，测试断言的就不是另一套复制品。
const ENTRY = `import { mountSearch } from './search-client.js'
mountSearch(window)
`

export const SEARCH_HTML = `<section class="book-search" aria-labelledby="book-search-title">
  <h2 class="book-search__title" id="book-search-title">搜索全书</h2>
  <form class="book-search__form" role="search" autocomplete="off">
    <label class="book-search__label" for="book-search-input">关键词</label>
    <input class="book-search__input" id="book-search-input" type="search" name="q" autocomplete="off" spellcheck="false" enterkeyhint="search" aria-describedby="book-search-status" placeholder="例如：预充时序、采样窗口、0.5 mV">
    <button class="book-search__submit" type="submit">搜索</button>
    <button class="book-search__clear" type="button">清除</button>
  </form>
  <p class="book-search__status" id="book-search-status" role="status" aria-live="polite" aria-atomic="true">${SEARCH_HINT}</p>
  <ol class="book-search__results" id="book-search-results" aria-label="搜索结果"></ol>
  <noscript><p class="book-search__noscript">搜索需要浏览器启用脚本；目录与正文不依赖脚本也能读。</p></noscript>
</section>`

let scriptPromise

async function bundleScript() {
  const result = await esbuild({
    stdin: {
      contents: ENTRY,
      resolveDir: HERE,
      sourcefile: 'engineering-search-entry.js',
      loader: 'js',
    },
    bundle: true,
    write: false,
    format: 'iife',
    platform: 'browser',
    // 仓库支持的浏览器都在这个范围以上；不把现代 API 降级成 helper 体积。
    target: ['chrome100', 'firefox100', 'safari15'],
    minify: true,
    legalComments: 'eof',
    // 产物最终按 UTF-8 写进单文件书：保留中文字符比转成 \uXXXX 小得多。
    charset: 'utf8',
    logLevel: 'silent',
  })

  const output = result.outputFiles && result.outputFiles[0]
  if (!output) throw new Error('搜索脚本打包失败：esbuild 没有产出文件')

  const require = createRequire(import.meta.url)
  const licensePath = path.resolve(path.dirname(require.resolve('minisearch')), '../../LICENSE.txt')
  let script = `/*! MiniSearch\n${readFileSync(licensePath, 'utf8')}\n*/\n${output.text}`
  // 防御性转义：内联进 HTML 时字面 `</script` 会提前结束脚本。
  // 当前实现没有这种字面量，但依赖升级后仍不允许它悄悄出现。
  script = script.replace(/<\/script/gi, '<\\/script')
  if (/<script[\s>]/i.test(script)) {
    throw new Error('搜索脚本里出现了 <script 字面量，内联进 HTML 会被解析成标签')
  }
  return script
}

export async function engineeringSearch() {
  if (!scriptPromise) {
    scriptPromise = bundleScript().catch((error) => {
      scriptPromise = undefined
      throw error
    })
  }
  return { html: SEARCH_HTML, script: await scriptPromise }
}

function isDirectRun() {
  if (!process.argv[1]) return false
  try {
    return pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url
  } catch (error) {
    return false
  }
}

if (isDirectRun()) {
  const result = await engineeringSearch()
  process.stdout.write(JSON.stringify(result) + '\n')
}
