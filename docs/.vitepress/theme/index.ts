// 站点皮肤的唯一入口：继承 VitePress 默认主题，挂一份 custom.css，再注册一个指令
// 让验收清单的勾选记住，并挂载伴读书的动画、参数交互与静读设置。
// 为什么单独开这个文件：默认主题只保证「干净」，本站 67 个页面里 211 张图、
// 大半是 SMIL 动画，正文又塞满公式与表格，默认皮在三件事上吃亏——
// 没有中文族字体（各系统兜底，字面忽大忽小）、强调色与动画色板不同源、
// 表格与公式没有排印处理。这三件都在 CSS 层解决，不需要动正文。
//
// 2026-10 起这里多了一件事：清单勾选要活过刷新，于是有了 v-bms-check——本站第一处
// 运行时 JS。口径跟着改：皮肤 = 1 份 custom.css + 1 个主题钩子，仍是唯一出处；
// 页面内 <style> 与第二份 CSS 依旧不许有。
//
// 加页面内 style 或第二份 CSS 会先撞墙：docs/维护说明.md 与本文件的注释
// 是皮肤口径的两处出处，改皮肤请连它们一起改。
import DefaultTheme from 'vitepress/theme'
import type { EnhanceAppContext } from 'vitepress'

import { readChecklistStore, writeChecklistStore } from '../checklist'
import './custom.css'
import { mountBookMotion, mountBookLab, mountCalmReader } from '../../../bms-book/reader.js'

/**
 * 挂载时把这台浏览器记住的状态写回控件。
 *
 * 用 property 而不是 attribute：`checked` 属性只决定初始值，写它会让服务端渲染的
 * HTML 与客户端状态打架（hydration 告警），写 property 不参与对比。
 * 监听器挂在控件自己身上，SPA 换页时随旧 DOM 节点一起销毁，不会越积越多。
 */
function restore(el: HTMLElement): void {
  const box = el as HTMLInputElement
  const page = box.dataset.bmsPage
  const key = box.dataset.bmsKey
  if (!page || !key) return
  box.checked = !!readChecklistStore()[page]?.[key]
  box.addEventListener('change', () => {
    const store = readChecklistStore()
    const ticks = store[page] || (store[page] = {})
    if (box.checked) ticks[key] = 1
    else {
      delete ticks[key]
      // 全勾空就删掉整页：至少勾过一格才算「这一节采到了」，取消到最后一条即回到未采样。
      if (Object.keys(ticks).length === 0) delete store[page]
    }
    writeChecklistStore(store)
  })
}

export default {
  extends: DefaultTheme,
  // extends 而不是覆盖：DefaultTheme 自己的 enhanceApp 注册了 Badge 等全局组件，
  // 直接写 enhanceApp 会把它们一起丢掉，正文里所有 <Badge> 当场变成未知组件。
  enhanceApp({ app, router }: EnhanceAppContext) {
    // 两头都注册：SSR 解析到 v-bms-check 却找不到定义会当场抛（读 getSSRProps），
    // 客户端找不到指令则整页挂载失败。构建期这段也跑，所以只注册、不碰 DOM。
    app.directive('bms-check', {
      getSSRProps: () => ({}),
      mounted: restore
    })
    const cleanups = new WeakMap<HTMLElement, () => void>()
    for (const [name, mount] of [['book-motion', mountBookMotion], ['book-lab', mountBookLab]] as const) {
      app.directive(name, {
        getSSRProps: () => ({}),
        mounted(el: HTMLElement) {
          const cleanup = mount(el)
          if (cleanup) cleanups.set(el, cleanup)
        },
        unmounted(el: HTMLElement) { cleanups.get(el)?.(); cleanups.delete(el) }
      })
    }
    if (typeof window !== 'undefined') {
      // 等两帧再挂：路由切换后 VitePress 还要换掉 .vp-doc 的内容，挂早了会对着
      // 上一章的 DOM 量滚动位置。但「等两帧」本身要防重入——切页比两帧更快时
      // （点目录连点几下就会），旧写法先把 cleanupReader 置空、再排 rAF，于是
      // 第二次调用时它已经是 undefined、拆不掉第一次挂的监听，第一次那对
      // scroll/resize 就永久留在 window 上，对着已经摘掉的进度条节点做无用功
      // （实测连挂 3 次漏 4 个监听）。所以：取消未兑现的那一帧，并且只在真正
      // 调用过 cleanup 之后才清句柄。
      let cleanupReader: (() => void) | undefined
      let pendingFrame = 0
      const mountReader = () => {
        if (pendingFrame) window.cancelAnimationFrame(pendingFrame)
        cleanupReader?.()
        cleanupReader = undefined
        pendingFrame = window.requestAnimationFrame(() => {
          pendingFrame = window.requestAnimationFrame(() => {
            pendingFrame = 0
            cleanupReader = mountCalmReader(document)
          })
        })
      }
      const previousAfterRouteChange = router.onAfterRouteChange
      router.onAfterRouteChange = async (to: string) => {
        await previousAfterRouteChange?.(to)
        mountReader()
      }
      mountReader()
    }
  }
}
