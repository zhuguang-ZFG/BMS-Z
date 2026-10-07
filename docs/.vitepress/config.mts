import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

import { defineConfig } from 'vitepress'

import { BASE, SITE_ORIGIN } from './base'
import { tokenizeCjk } from './cjk-search'
import { escapingLinksToGitHub } from './escaping-links'
import { lazyImagesWithDimensions } from './lazy-images'
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

/**
 * 篇首那句「本篇你会学到」。59 篇里 27 篇有，是正文作者自己写的摘要。
 * 分享卡片没有 frontmatter description 时拿它兜底——比整站复读站点简介实在，
 * 也不新编文案：只认正文那一行，链接剥成文字，超长截断。
 */
function leadSummary(relPath: string): string | null {
  const file = path.join(DOCS_DIR, relPath)
  if (!existsSync(file)) return null
  const line = readFileSync(file, 'utf8').match(/^> \*\*本篇你会学到\*\*　?(.+)$/m)?.[1]
  if (!line) return null
  const text = line
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[*`]/g, '')
    .trim()
  if (!text) return null
  return text.length > 140 ? `${text.slice(0, 140)}…` : text
}

export default defineConfig({
  base: BASE,
  lang: 'zh-CN',
  title: 'BMS-Z',
  description:
    '从入门到产品级的电池管理系统（BMS）中文自学路线——七篇阶段教程、150 张动画电路图、PC 可跑的配套代码。',

  // 站点级 <head>，全站一份。每篇自己的 og:title / og:url / 摘要由下面的
  // transformHead 补，两边不重复推同一个键。
  head: [
    // docs/public/ 下的文件由 VitePress 原样拷到 dist 根，favicon 走 base 前缀。
    ['link', { rel: 'icon', type: 'image/svg+xml', href: `${BASE}favicon.svg` }],
    ['meta', { property: 'og:site_name', content: 'BMS-Z 电池管理系统自学路线' }],
    // 预览图借 GitHub 仓库社交预览图：对任何公开仓库稳定出图，不需要构建产物。
    // 站点自己的 1200×630 封面还没有——有了就换这两行，别拿 AI 生成图凑数。
    [
      'meta',
      {
        property: 'og:image',
        content: 'https://opengraph.githubassets.com/1/zhuguang-ZFG/BMS-Z',
      },
    ],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    [
      'meta',
      {
        name: 'twitter:image',
        content: 'https://opengraph.githubassets.com/1/zhuguang-ZFG/BMS-Z',
      },
    ],
  ],

  // dist/sitemap.xml。VitePress 把每条 url 用 `new URL(item, hostname)` 解析，
  // 而 hostname 少了尾斜杠就会连路径一起被丢掉（实测：hostname 写成 …/BMS-Z 时
  // 产出 https://host/AI陪练卡.html，base 整段没了）。BASE 自带尾斜杠，直接拼。
  sitemap: { hostname: `${SITE_ORIGIN}${BASE}` },

  // 每篇自己的分享卡片。VitePress 默认只发 title 和 description，没有 og:*，
  // 链接发到聊天里就是一行裸文字。站点级的 og:site_name / og:image 在上面 head 里
  // 全站一份，这里补每篇四件：标题带站点名后缀、绝对地址、摘要、类型。
  // 绝对地址自己拼：pageData.url 在这个钩子里还没填，而 page 是源文件相对路径。
  transformHead({ page, pageData, siteData, description }) {
    const rel = page === 'index.md' ? '' : page.replace(/\.md$/, '.html')
    const encoded = rel.split('/').map(encodeURIComponent).join('/')
    const title = pageData.title || siteData.title
    // 首页没有 H1，标题就是站点名本身——再拼一次「· BMS-Z」会自我重复。
    const ogTitle = title === siteData.title ? title : `${title} · BMS-Z`
    // 摘要优先级：frontmatter 写的 > 正文那句「本篇你会学到」> 站点级简介。
    // ctx.description 已经掺了站点级默认值，分不出来源，所以按同一个顺序自己走一遍。
    const explicit = !!description && description !== siteData.description
    const summary = explicit ? description : leadSummary(page) || siteData.description
    return [
      ['meta', { property: 'og:title', content: ogTitle }],
      ['meta', { property: 'og:description', content: summary }],
      ['meta', { property: 'og:url', content: `${SITE_ORIGIN}${BASE}${encoded}` }],
      ['meta', { property: 'og:type', content: 'article' }],
    ]
  },

  // 跨出 docs/ 的相对链接（README、code/、.github 模板…）在 Pages 上没有对应页面，
  // VitePress 会判死链。源码不能改：Obsidian 和 GitHub 都依赖这些相对路径。
  // 渲染期由下面的 markdown.config 钩子改写成 GitHub blob URL，所以这里放开内置检查；
  // 链接指向的文件是否真存在，由 .github/scripts/check_docs.py 把关。
  ignoreDeadLinks: true,

  // PDF 与本地产物不进站点。
  srcExclude: ['**/*.pdf'],

  markdown: {
    math: true,
    anchor: { slugify: githubSlugify },
    toc: { slugify: githubSlugify },
    config(md) {
      md.use(escapingLinksToGitHub(SITE_ASSETS))
      md.use(lazyImagesWithDimensions())
    },
  },

  vite: {
    build: {
      // 默认 4KB 以下的 SVG 会被内联成 base64 data URL。关掉内联，让 150 张动画
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
        miniSearch: {
          // 索引端（CI 的 Node）与查询端（访客浏览器）必须用同一个分词函数，
          // 否则词条和查询词对不上，搜索会整体失灵。VitePress 会把 themeConfig
          // 里的函数序列化进站点数据带到客户端（构建产物里能看到这段函数体），
          // 两端各传一次是为了不依赖那个默认继承关系。
          options: { tokenize: tokenizeCjk },
          searchOptions: { tokenize: tokenizeCjk },
        },
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
    // 404 页的文案在组件默认值里是英文，不覆盖就是整站唯一的英文页面。
    notFound: {
      title: '这一页不在站点上',
      quote: '可能文件改名了，也可能链接写错了。回首页从侧栏重新找。',
      linkText: '回首页',
      linkLabel: '回首页',
    },
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
