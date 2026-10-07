import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { defineConfig } from 'vitepress'

import { BASE } from './base'
import { escapingLinksToGitHub } from './escaping-links'
import { multiSidebar } from './sidebar'

// 站点根 = 仓库的 docs/。构建命令固定为 `vitepress build docs`（本地脚本与 CI 同一条），
// 所以按 cwd 定位；一旦不在仓库根调用就当场报错，而不是静默生成一个缺页面的站点。
const DOCS_DIR = path.resolve('docs')
if (!existsSync(path.join(DOCS_DIR, 'stages'))) {
  throw new Error(`找不到站点根：${DOCS_DIR}（请在仓库根目录运行 vitepress build docs）`)
}

// 标题锚点必须和 GitHub 渲染出来的 slug 一模一样：仓库里有数百处 `xxx.md#中文锚点`
// 的内链，而 GitHub 与 VitePress 默认是两套 slug 规则（VitePress 把 `.` 换成 `-`，
// 并给数字开头的标题加 `_` 前缀），不覆盖就会全线失配。
//
// 这份实现是 .github/scripts/check_docs.py 里 slugify() 的 JS 孪生体：那里的 `\w` 认
// 中文、也认 ①⑳ 这类带圈数字，所以这里用 Unicode 属性类别而不是只认 ASCII 的 JS `\w`。
// 两边必须同步改——deploy workflow 里的 Pages 锚点对账会拦住漂移。
const KEEP = /[^\p{L}\p{N}\p{M}\s_-]/gu

function githubSlugify(heading: string): string {
  return heading
    .normalize('NFC')
    .trim()
    .toLowerCase()
    .replace(KEEP, '')
    .replace(/ /g, '-')
}

// 仓库根上由站点自己托管的文件：正文照旧写 `../BMS学习路径.html`（GitHub 与 Obsidian
// 都靠这个相对路径），构建后拷进 dist，Pages 上指向站点内的绝对 URL。
// 清单只有 site-assets.json 这一份，config 与 copy-site-assets.mjs 共用，不会各说各话。
const SITE_ASSETS: Record<string, string> = JSON.parse(
  readFileSync(path.join(DOCS_DIR, '.vitepress', 'site-assets.json'), 'utf8')
).assets

export default defineConfig({
  base: BASE,
  lang: 'zh-CN',
  title: 'BMS-Z',
  description:
    '从入门到产品级的电池管理系统（BMS）中文自学路线——七篇阶段教程、148 张动画电路图、PC 可跑的配套代码。',

  // 跨出 docs/ 的相对链接（README、code/、.github 模板…）在 Pages 上没有对应页面，
  // VitePress 会判死链。源码不能改：Obsidian 和 GitHub 都依赖这些相对路径。
  // 渲染期由下面的 markdown.config 钩子改写成 GitHub blob URL，所以这里放开内置检查；
  // 链接指向的文件是否真存在，由 .github/scripts/check_docs.py 把关。
  ignoreDeadLinks: true,

  // PDF 与本地产物不进站点。
  srcExclude: ['**/*.pdf'],

  markdown: {
    anchor: { slugify: githubSlugify },
    toc: { slugify: githubSlugify },
    config(md) {
      md.use(escapingLinksToGitHub(SITE_ASSETS))
    },
  },

  vite: {
    build: {
      // 默认 4KB 以下的 SVG 会被内联成 base64 data URL。关掉内联，让 148 张动画
      // 始终以真实 .svg 文件出站点，SMIL 行为与在 GitHub 上打开时一致。
      assetsInlineLimit: 0,
    },
  },

  lastUpdated: true,

  themeConfig: {
    siteTitle: 'BMS-Z',
    nav: [
      { text: '从这里开始', link: '/stages/getting-started' },
      { text: '阶段教程', link: '/stages/stage-0-前置知识' },
      { text: '电路详解', link: '/circuits/README' },
      { text: '查资料', link: '/bms-resources' },
      { text: '一起学', link: '/擂台' },
    ],
    sidebar: multiSidebar(DOCS_DIR),
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有匹配的段落',
            resetButtonTitle: '清空关键词',
            displayDetails: '展开命中位置',
          },
        },
      },
    },
    outline: { level: [2, 3], label: '本页目录' },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '回到顶部',
    docFooter: { prev: '上一篇', next: '下一篇' },
    lastUpdatedText: '最后更新',
    editLink: {
      pattern: 'https://github.com/zhuguang-ZFG/BMS-Z/edit/main/docs/:path',
      text: '在 GitHub 上改这一页',
    },
    footer: {
      message: '文档 CC BY-SA 4.0 · 代码 MIT',
      copyright: 'BMS-Z 中文 BMS 自学路线',
    },
  },
})
