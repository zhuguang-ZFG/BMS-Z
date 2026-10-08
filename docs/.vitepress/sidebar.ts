/**
 * 构建期扫描 docs/ 生成侧边栏。
 *
 * 为什么不手写清单：57 个页面全是中文文件名，手写必漂；新增一篇正文却忘了加进导航，
 * 在站点上就等于没发布。这里按目录扫描，标题取每篇的第一个 `# ` 行，新文档自动出现。
 * 顺序只对「有教学次序」的分组显式指定，其余按文件名排序兜底。
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'

/** 阶段教程的阅读次序；不在表里的 stages 文件排在后面，不会消失。 */
const STAGE_ORDER = [
  'getting-started.md',
  'stage-0-前置知识.md',
  'stage-1-认识BMS.md',
  'stage-2-保护板实践.md',
  'stage-3-AFE-MCU智能BMS.md',
  'stage-4-SOC-SOH算法.md',
  'stage-5-通信与集成.md',
  'stage-6-精通与毕业项目.md',
  '按目标选路线.md',
  'bloom-map.md',
  'bloom-migration.md',
]

/** 电路详解五篇 + 索引 + 画风规范。 */
const CIRCUIT_ORDER = [
  'README.md',
  '01-功率回路-MOS保护与预充.md',
  '02-采样链与AFE芯片.md',
  '03-充电均衡与计量.md',
  '04-系统安全与量产.md',
  '05-BMS电路板绘制与设计要点.md',
  '动画画风规范.md',
]

const COLEARN_ORDER = ['README.md', '01-soc五天.md', '02-协议五天.md', '03-固件五天.md', '04-真实数据五天.md', '05-sop五天.md']

/** docs/ 根下按主题归组；正则按文件名匹配，剩下的统一进「参考与社区」。 */
const ROOT_GROUPS: {
  title: string
  test: (name: string) => boolean
  /** 组内点名排在前面的文件，其余按文件名排序兜底。 */
  order?: string[]
}[] = [
  {
    title: '查资料',
    order: ['bms-resources.md', 'budget.md'],
    test: (n) =>
      [
        'bms-resources.md',
        'budget.md',
        '参数速查卡.md',
        'glossary.md',
        '口诀速查.md',
        '比喻地图.md',
        '基石阅读.md',
      ].includes(n),
  },
  {
    title: '中文导读',
    order: ['导读索引.md'],
    test: (n) => /^(ece57\d\d-notes|renesas-|uccs-|导读索引)/.test(n),
  },
  { title: '动手与实战专题', test: (n) => /专题\.md$/.test(n) || n === '工具箱.md' || n === 'AI陪练卡.md' },
  { title: '一起学', test: (n) => ['擂台.md', '作品墙.md', '共建任务板.md', '更新动态.md'].includes(n) },
  { title: '怎么读与怎么维护', test: (n) => ['obsidian.md', '维护说明.md', 't13-包级手册缺口.md'].includes(n) },
]

interface Item {
  text: string
  link: string
}

interface Group {
  text: string
  items: Item[]
}

/** 每篇的第一个 `# ` 标题；没有就用文件名，保证导航里不会出现空白项。 */
function pageTitle(mdPath: string): string {
  const lines = readFileSync(mdPath, 'utf8').split('\n')
  let inFence = false
  for (const line of lines) {
    if (line.trimStart().startsWith('```')) {
      inFence = !inFence
      continue
    }
    if (inFence) continue
    if (line.startsWith('# ')) return line.slice(2).replace(/\s+#+\s*$/, '').trim()
  }
  return path.basename(mdPath, '.md')
}

function mdFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  return readdirSync(dir).filter((n) => n.endsWith('.md'))
}

/** 按给定次序排，表外的追加在末尾——新文件不会从导航里漏掉。 */
function orderFiles(names: string[], order: string[]): string[] {
  const known = order.filter((n) => names.includes(n))
  const rest = names.filter((n) => !known.includes(n)).sort()
  return [...known, ...rest]
}

function items(dir: string, names: string[], prefix: string): Item[] {
  return names.map((n) => ({
    text: pageTitle(path.join(dir, n)),
    link: `/${prefix}${n.replace(/\.md$/, '')}`,
  }))
}

export function multiSidebar(docsDir: string): Record<string, Group[]> {
  const stagesDir = path.join(docsDir, 'stages')
  const circuitsDir = path.join(docsDir, 'circuits')
  const colearnDir = path.join(docsDir, '共学')

  // docs/ 根下的散页按主题分组，顺序即侧栏顺序。首页是入口不是正文，不进侧边栏。
  const rootNames = mdFiles(docsDir).filter((n) => n !== 'index.md')
  const rootGroups: Group[] = []
  const taken = new Set<string>()
  for (const group of ROOT_GROUPS) {
    const names = orderFiles(rootNames.filter(group.test), group.order ?? []).filter(
      (n) => !taken.has(n)
    )
    names.forEach((n) => taken.add(n))
    if (names.length) rootGroups.push({ text: group.title, items: items(docsDir, names, '') })
  }
  // 兜底组：新加的散页绝不会因为没人改这张表就从导航里消失。但它叫「其他」
  // 不叫「分类」——有东西落进来就是提醒该给它找个正经组了。
  const leftovers = rootNames.filter((n) => !taken.has(n)).sort()
  if (leftovers.length) {
    rootGroups.push({ text: '其他', items: items(docsDir, leftovers, '') })
  }

  return {
    '/stages/': [
      {
        text: '阶段教程',
        items: items(stagesDir, orderFiles(mdFiles(stagesDir), STAGE_ORDER), 'stages/'),
      },
    ],
    '/circuits/': [
      {
        text: '电路详解',
        items: items(circuitsDir, orderFiles(mdFiles(circuitsDir), CIRCUIT_ORDER), 'circuits/'),
      },
    ],
    '/共学/': [
      {
        text: '共学快闪',
        items: items(colearnDir, orderFiles(mdFiles(colearnDir), COLEARN_ORDER), '共学/'),
      },
    ],
    '/': rootGroups,
  }
}

/** 首页要展示的七阶段入口，顺序跟着正文走。 */
export function stageLinks(docsDir: string): Item[] {
  const stagesDir = path.join(docsDir, 'stages')
  return orderFiles(mdFiles(stagesDir), STAGE_ORDER)
    .filter((n) => n.startsWith('stage-'))
    .map((n) => ({
      text: pageTitle(path.join(stagesDir, n)),
      link: `/stages/${n.replace(/\.md$/, '')}`,
    }))
}
