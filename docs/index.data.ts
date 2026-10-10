import { readFileSync } from 'node:fs'
import path from 'node:path'
import type { Loader } from 'vitepress'
import { BASE } from './.vitepress/base'
import { checklistKey, extractTaskItems } from './.vitepress/checklist'
import { stageLinks } from './.vitepress/sidebar'

type LearningLayer = {
  number: string
  name: string
  verb: string
  summary: string
  proof: string
  link: string
}

type PracticeRoute = {
  tag: string
  title: string
  details: string
  linkText: string
  link: string
}

function pageLink(relPath: string, fragment?: string): string {
  const page = relPath.replace(/\.md$/, '')
  return `${BASE}${page}.html${fragment ? `#${fragment}` : ''}`
}

type PackCell = {
  /** 电芯上印的阶段号，跟着文件名走，不跟数组下标走。 */
  index: string
  /** 电芯下面那行短名。 */
  name: string
  /** 这一格的可勾条目实际在哪一页：与控件上的 data-bms-page 同一个字符串。 */
  page: string
  link: string
  total: number
  /** 这一格全部条目键。首页拿它数「勾了几个」，所以必须与渲染插件同一套生成。 */
  keys: string[]
}

/**
 * 毕业那一格不在阶段正文里：stage-6 结尾把人送回总纲的「精通自检清单」，正文自己
 * 一条 `- [ ]` 都没有。照正文算就是一格永远 0/0 的电芯，包容量被它钉死在零。
 */
const PACK_SOURCES: Readonly<Record<string, { page: string; link: string; name: string }>> = {
  'stages/stage-6-精通与毕业项目.md': {
    page: 'bms-resources.md',
    link: pageLink('bms-resources.md', '精通自检清单'),
    name: '精通',
  },
}

/** `阶段 4 教程：SOC / SOH / SOP 估算算法` → `SOC / SOH / SOP 估算算法`。 */
function shortName(title: string): string {
  const afterColon = title.slice(title.indexOf('：') + 1).trim()
  return (afterColon || title).split('——')[0].trim()
}

/**
 * 一格电芯 = 一个阶段的验收清单。条目和键都从源文件现算，不写死数字：
 * 数条目用的是 checklist.ts 里渲染插件那一份口径，两边不可能数出两个数。
 */
function packCell(stage: { text: string; link: string }): PackCell {
  const source = `${stage.link.slice(1)}.md`
  const override = PACK_SOURCES[source]
  const page = override?.page ?? source
  const items = extractTaskItems(readFileSync(path.resolve('docs', page), 'utf8'))
  const number = /stage-(\d+)/.exec(stage.link)?.[1] ?? '?'
  return {
    index: number.padStart(2, '0'),
    name: override?.name ?? shortName(stage.text),
    page,
    link: override?.link ?? `${BASE.slice(0, -1)}${stage.link}.html`,
    total: items.length,
    keys: items.map((item) => checklistKey(page, item)),
  }
}

const learningLayers: LearningLayer[] = [
  {
    number: '01',
    name: '记忆',
    verb: '先叫对名字',
    summary: '认出电芯红线、五大保护和器件角色。',
    proof: '闭卷说出满充电压与断口方向。',
    link: pageLink('stages/bloom-map.md', '记忆'),
  },
  {
    number: '02',
    name: '理解',
    verb: '再讲清机制',
    summary: '解释过充、过放、温度与最弱单体为什么重要。',
    proof: '用自己的话讲清延时保护的理由。',
    link: pageLink('stages/bloom-map.md', '理解'),
  },
  {
    number: '03',
    name: '应用',
    verb: '亲手跑一次',
    summary: '把保护、SOC、协议或状态机放进可重复的 PC 实验。',
    proof: '跑出结果，并指出曲线或帧从哪一拍变化。',
    link: pageLink('stages/bloom-map.md', '应用'),
  },
  {
    number: '04',
    name: '分析',
    verb: '拆开它为何漂',
    summary: '从误差预算、模型、噪声和时间轴定位根因。',
    proof: '解释零漂、参数错配或坏帧如何留下证据。',
    link: pageLink('stages/bloom-map.md', '分析'),
  },
  {
    number: '05',
    name: '评价',
    verb: '做出有边界的取舍',
    summary: '比较架构与算法，不把通信或云端当安全闭环。',
    proof: '给出方案选择，并写明不能交给谁的决策。',
    link: pageLink('stages/bloom-map.md', '评价'),
  },
  {
    number: '06',
    name: '创造',
    verb: '交付可复现作品',
    summary: '按需求、证据和验收量规把知识收束成作品。',
    proof: '别人按你的记录能重跑并判断是否达标。',
    link: pageLink('stages/bloom-map.md', '创造'),
  },
]

const practiceRoutes: PracticeRoute[] = [
  {
    tag: '找位置',
    title: '先定位自己在哪一层',
    details: '不必从头刷七阶段；按能力地图选一个第一入口，做完自检再向上走。',
    linkText: '打开能力地图',
    link: pageLink('stages/bloom-map.md'),
  },
  {
    tag: '做证据',
    title: '用五天把一个闭环跑通',
    details: '十一期共学都只用电脑：读一节、看一张图、跑一条命令，再交出原文结果。',
    linkText: '挑一期开跑',
    link: pageLink('共学/README.md'),
  },
  {
    tag: '交作品',
    title: '把结果送进工程验收',
    details: '从仿真结果继续写需求、边界和复现步骤，最后用毕业量规检查证据链。',
    linkText: '看毕业项目指南',
    link: pageLink('stages/stage-6-精通与毕业项目.md', '66-毕业项目指南-创造'),
  },
]

export default {
  load() {
    const cells = stageLinks(path.resolve('docs')).map(packCell)
    return {
      stages: stageLinks(path.resolve('docs')).map((s) => ({
        ...s,
        // 首页用普通 <a> 渲染（markdown 里 RouterLink 客户端解析不稳），
        // 所以这里直接烤出带 base 和 .html 的最终地址。
        link: `${BASE.slice(0, -1)}${s.link}.html`,
      })),
      learningLayers,
      practiceRoutes,
      pack: {
        cells,
        total: cells.reduce((sum, cell) => sum + cell.total, 0),
      },
    }
  },
} satisfies Loader
