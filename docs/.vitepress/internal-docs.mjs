/**
 * 不进站点的内部文档（agent 与维护者的工作文档，不是读者页）。
 *
 * 为什么必须一处定义、两处使用：`config.mts` 的 `srcExclude` 决定它们不构建成页面，
 * `sidebar.ts` 的目录扫描决定导航里有没有它们的链接。只改前者，侧栏照样生成指向未构建
 * 页面的 href——`check_pages.py` 报一批死链；只改后者，页面照样构建——报一批孤儿。
 *
 * 名单里的三类：handraw 真源树（提示词 / 帧 / runbook）、`superpowers/`（计划与设计）、
 * 根上的画风包。读者面的画风规范是 `circuits/动画画风规范.md`，那份照旧发布。
 *
 * 这些文件还必须各自带 `search: false`：`check_search.mjs` 是逐篇扫源码树判「进没进索引」
 * 的，不认 `srcExclude`；少了这个键，构建通过但检索门红。`internal-docs.test.mjs` 守着这三条。
 */
export const INTERNAL_DOC_GLOBS = ['superpowers/**', 'circuits/handraw/**', 'visual-style-pack.md', 'yuyu-overhaul/**']

/** 目录 glob（`…/**`）退成前缀，其余按整文件比对；两张表从同一份 glob 推出，不会各写一遍。 */
const INTERNAL_DOC_DIRS = INTERNAL_DOC_GLOBS.filter((glob) => glob.endsWith('/**')).map((glob) =>
  glob.slice(0, -2)
)
const INTERNAL_DOC_FILES = INTERNAL_DOC_GLOBS.filter((glob) => !glob.endsWith('/**'))

/**
 * @param {string} relPath 相对 `docs/` 的 POSIX 路径
 * @returns {boolean}
 */
export function isInternalDoc(relPath) {
  return INTERNAL_DOC_DIRS.some((dir) => relPath.startsWith(dir)) || INTERNAL_DOC_FILES.includes(relPath)
}
