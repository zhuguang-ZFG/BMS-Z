import { readFileSync, readdirSync } from 'node:fs'
import path from 'node:path'
import { checklistKey, extractTaskItems } from './checklist.ts'

const checklistSources = [
  { number: '00', name: '电芯与基础', page: 'stages/stage-0-前置知识.md' },
  { number: '01', name: '认识 BMS', page: 'stages/stage-1-认识BMS.md' },
  { number: '02', name: '保护板实践', page: 'stages/stage-2-保护板实践.md', readingPage: 'stages/stage-2-主线-实测与验收.md' },
  { number: '03', name: 'AFE 与 MCU', page: 'stages/stage-3-AFE-MCU智能BMS.md', readingPage: 'stages/stage-3-主线-PCB调试与验收.md' },
  { number: '04', name: '状态估算', page: 'stages/stage-4-SOC-SOH算法.md', readingPage: 'stages/stage-4-主线-SOH与SOP.md' },
  { number: '05', name: '通信与集成', page: 'stages/stage-5-通信与集成.md', readingPage: 'stages/stage-5-主线-协议逆向与安全.md' },
  { number: '06', name: '工程与交付', page: 'bms-resources.md', fragment: '精通自检清单' },
]

export function loadLearningChecklists(docsDirectory, base) {
  const pages = readdirSync(path.join(docsDirectory, 'stages'))
    .filter(file => /^stage-\d+-.*\.md$/.test(file))
    .map(file => `stages/${file}`)
  const pageItems = new Map([...pages, 'bms-resources.md'].map(page => [
    page,
    extractTaskItems(readFileSync(path.join(docsDirectory, page), 'utf8')),
  ]))

  return checklistSources.map(source => {
    const items = pageItems.get(source.page)
    if (!items?.length) throw new Error(`阶段 ${source.number} 的验收清单为空：${source.page}`)
    const stagePrefix = `stages/stage-${Number(source.number)}-`
    const readingPage = source.readingPage ?? source.page
    const link = `${base}${readingPage.replace(/\.md$/, '.html')}${source.fragment ? `#${source.fragment}` : ''}`
    return {
      index: source.number,
      name: source.name,
      page: source.page,
      link,
      total: items.length,
      items: items.map(text => ({
        sources: [...pageItems].filter(([page, candidates]) =>
          (page === source.page || page.startsWith(stagePrefix)) && candidates.includes(text)
        ).map(([page]) => ({ page, key: checklistKey(page, text) })),
      })),
    }
  })
}
