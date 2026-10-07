import path from 'node:path'
import type { Loader } from 'vitepress'
import { BASE } from './.vitepress/base'
import { stageLinks } from './.vitepress/sidebar'

export default {
  load() {
    return {
      stages: stageLinks(path.resolve('docs')).map((s) => ({
        ...s,
        // 首页用普通 <a> 渲染（markdown 里 RouterLink 客户端解析不稳），
        // 所以这里直接烤出带 base 和 .html 的最终地址。
        link: `${BASE.slice(0, -1)}${s.link}.html`,
      })),
    }
  },
} satisfies Loader
