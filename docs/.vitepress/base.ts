/**
 * GitHub Pages 项目页的站点前缀。config.mts 和 index.data.ts 都要用：
 * 前者管整站资源路径，后者给首页数据烤最终 URL。只此一份，两边不会漂。
 */
export const BASE = '/BMS-Z/'

/**
 * 站点绝对地址。sitemap 的 hostname 和分享卡片用的 og:url 都拼这一个，
 * 不含末尾斜杠；页面 URL 由 VitePress 给出（自带 BASE 前缀），直接续在后面。
 */
export const SITE_ORIGIN = 'https://zhuguang-zfg.github.io'
