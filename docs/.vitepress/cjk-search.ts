/**
 * 本地搜索的中文分词：汉字串切二元组，其余保持 MiniSearch 的默认切法。
 *
 * 为什么站点必须自己写：MiniSearch 默认只在空白和标点处切词（它的分隔符是
 * /[\n\r\p{Z}\p{P}]+/u），而中文两字之间既没空格也没标点，于是
 * 「零漂会把油箱慢慢加歪」整串成为一个词条——搜「油箱」只能靠前缀匹配碰运气，
 * 命中不了句中。正文里能查的东西几乎都是中文词，等于搜索半残。
 *
 * 为什么用二元组而不是 Intl.Segmenter 分词：词条在 CI 的 Node 里建，查询串在访客
 * 浏览器里切，两端必须切出同一批词。Segmenter 的中文词库依赖浏览器 ICU 数据，
 * 数据不全时会整串返回，那样查询和索引直接对不上；二元组是纯字符串运算，
 * 两端必然一致，也不给站点加运行时依赖。
 * 代价是词表里混进「箱慢」这种跨词二元组：它只会让个别结果排序靠前一点，
 * 不会让该出现的段落消失，所以值得。
 */

/**
 * 这个函数必须完全自包含：正则写在函数体里，一个模块级常量都不许引用。
 *
 * VitePress 把 themeConfig 交给浏览器的方式是「把函数源码塞进每页的站点数据」，
 * 客户端再用 new Function 还原（构建产物里能看到 `_vp-fn_` 标记）。源码里引用的
 * 模块级变量不会跟着过去，浏览器里就是 undefined——分词会在每次敲键时抛错，
 * 而索引是构建期用真函数建的，两边词表立刻对不上。
 * .github/scripts/check_search.mjs 会把 HTML 里那段源码取出来跑，跟这里的实现逐条比对。
 */
export function tokenizeCjk(text: string): string[] {
  const han = /\p{Script=Han}/u
  // 与 MiniSearch 默认分词同款分隔符，保证英文、数字、全角标点的切法不变。
  const separators = /[\n\r\p{Z}\p{P}]+/u

  const terms: string[] = []

  for (const chunk of text.split(separators)) {
    if (!chunk) continue

    let cursor = 0
    while (cursor < chunk.length) {
      const isHan = han.test(chunk[cursor])
      let end = cursor
      while (end < chunk.length && han.test(chunk[end]) === isHan) end++

      const run = chunk.slice(cursor, end)
      if (isHan && run.length > 1) {
        for (let i = 0; i + 2 <= run.length; i++) terms.push(run.slice(i, i + 2))
      } else {
        terms.push(run)
      }
      cursor = end
    }
  }

  return terms
}
