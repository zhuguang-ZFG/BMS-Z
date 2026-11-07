import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import type { Loader } from 'vitepress'
import { BASE } from './.vitepress/base'
import { loadLearningChecklists } from './.vitepress/learning-progress.mjs'
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

type GoalRoute = {
  id: string
  title: string
  forWho: string
  duration: string
  hardware: string
  start: string
  output: string
  link: string
}

function pageLink(relPath: string, fragment?: string): string {
  const page = relPath.replace(/\.md$/, '')
  return `${BASE}${page}.html${fragment ? `#${fragment}` : ''}`
}

const learningLayers: LearningLayer[] = [
  {
    number: '01',
    name: '记忆',
    verb: '认出器件与保护项',
    summary: '认出电芯红线、五大保护和器件角色。',
    proof: '闭卷说出满充电压与断口方向。',
    link: pageLink('stages/bloom-map.md', '记忆'),
  },
  {
    number: '02',
    name: '理解',
    verb: '解释保护为什么动作',
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
    verb: '找到误差从哪里来',
    summary: '从误差预算、模型、噪声和时间轴定位根因。',
    proof: '解释零漂、参数错配或坏帧如何留下证据。',
    link: pageLink('stages/bloom-map.md', '分析'),
  },
  {
    number: '05',
    name: '评价',
    verb: '比较方案与适用条件',
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
    title: '选择适合当前基础的章节',
    details: '按能力地图选择章节，做完自检再继续。',
    linkText: '打开能力地图',
    link: pageLink('stages/bloom-map.md'),
  },
  {
    tag: '做实验',
    title: '用五天完成一个实验',
    details: '十一期共学都只用电脑：读讲解、看图、运行命令，保存实际结果。',
    linkText: '选择一期共学',
    link: pageLink('共学/README.md'),
  },
  {
    tag: '交作品',
    title: '整理并检查项目结果',
    details: '写下需求、适用条件和复现步骤，再用毕业项目量规检查。',
    linkText: '看毕业项目指南',
    link: pageLink('stages/stage-6-精通与毕业项目.md', '66-毕业项目指南-创造'),
  },
]

const goalRoutes: GoalRoute[] = [
  {
    id: 'beginner',
    title: '第一次学 BMS',
    forWho: '从电池常识开始，逐步了解整套系统',
    duration: '24 课，按作品推进',
    hardware: '纸笔与电脑，默认不用电池',
    start: '先分清 V、A、Ah 和 Wh，再跟踪同一个 4S 包。',
    output: '计算单、采样日志、保护与通信回放、工程任务书。',
    link: pageLink('stages/getting-started.md'),
  },
  {
    id: 'hardware',
    title: '动手做一块板',
    forWho: '测保护板，再学 AFE 采样与 MCU 控制',
    duration: '2 周–4 个月',
    hardware: '需要测量器材',
    start: '从路线 A 开始，先用分压链模拟电芯。',
    output: '一份含保护阈值、延时与恢复过程的实测记录。',
    link: pageLink('stages/按目标选路线.md', 'a-做一块-34-串保护板并实测保护动作'),
  },
  {
    id: 'algorithm',
    title: '做状态估算算法',
    forWho: '会编程，想研究 SOC、SOH 与 SOP',
    duration: '1–3 个月',
    hardware: '一台电脑即可',
    start: '从安时积分的漂移开始，再接 OCV、模型和 EKF。',
    output: '一份注明参考真值、误差曲线和失败原因的报告。',
    link: pageLink('stages/按目标选路线.md', 'c-只做算法socsoh全程零器材'),
  },
  {
    id: 'product',
    title: '把原型做成产品',
    forWho: '已有板级基础，继续补安全、量产与交付',
    duration: '持续推进',
    hardware: '按项目准备器材',
    start: '写清需求与风险，再选高压架构、固件和测试。',
    output: '需求、测试、责任与复现步骤完整的项目记录。',
    link: pageLink('stages/按目标选路线.md', 'f-往产品级--车规靠功能安全与量产'),
  },
]

const course = JSON.parse(readFileSync(path.resolve('docs/course/manifest.json'), 'utf8')) as {
  modules: { id: string; title: string; artifact: string }[]
  lessons: { module: string; id: string; file: string }[]
}
const syllabus = course.modules.map((module, index) => {
  const lessons = course.lessons.filter((lesson) => lesson.module === module.id)
  return {
    number: String(index + 1).padStart(2, '0'),
    title: module.title.replace(/^.* · /, ''),
    description: module.artifact,
    duration: `第 ${lessons[0].id}–${lessons[lessons.length - 1].id} 课`,
    link: pageLink(`course/${lessons[0].file}`),
  }
})

const experiments = [
  { number: '01', title: '把整套信号链跑一遍', description: '从采样、SOC 到保护与通信，跟着运行记录追踪一次关断。', output: '哪一拍越限，哪一拍真正断开', page: 'PC综合实验专题' },
  { number: '02', title: '拿真实数据检验估算', description: '用 NASA 实测记录标定模型，再换一段独立负载查看误差。', output: '换工况后，模型还准不准', page: 'SOC真实数据专题' },
  { number: '03', title: '看一阶模型漏掉了什么', description: '模拟活性颗粒中的扩散，对比一阶 RC 与扩散响应。', output: '拟合不上前段的差异有多大', page: '扩散与常相位专题' },
].map(experiment => ({ ...experiment, link: pageLink(`${experiment.page}.md`) }))

export default {
  load() {
    const cells = loadLearningChecklists(path.resolve('docs'), BASE)
    return {
      stages: stageLinks(path.resolve('docs')).map((s) => ({
        ...s,
        // 首页用普通 <a> 渲染（markdown 里 RouterLink 客户端解析不稳），
        // 所以这里直接烤出带 base 和 .html 的最终地址。
        link: `${BASE.slice(0, -1)}${s.link}.html`,
      })),
      learningLayers,
      practiceRoutes,
      goalRoutes,
      syllabus,
      experiments,
      animationCount: readdirSync(path.resolve('docs/circuits/assets')).filter(file => file.endsWith('.svg')).length,
      pack: {
        cells,
        total: cells.reduce((sum, cell) => sum + cell.total, 0),
      },
    }
  },
} satisfies Loader
