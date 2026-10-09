// 站点皮肤的唯一入口：继承 VitePress 默认主题，再挂一份 custom.css。
// 为什么单独开这个文件：默认主题只保证「干净」，本站 67 个页面里 211 张图、
// 150 张是 SMIL 动画，正文又塞满公式与表格，默认皮在三件事上吃亏——
// 没有中文族字体（各系统兜底，字面忽大忽小）、强调色与动画色板不同源、
// 表格与公式没有排印处理。这三件都在 CSS 层解决，不需要动正文。
//
// 加页面内 style 或第二份 CSS 会先撞墙：docs/维护说明.md 与本文件的注释
// 是皮肤口径的两处出处，改皮肤请连它们一起改。
import DefaultTheme from 'vitepress/theme'
import './custom.css'

export default DefaultTheme
