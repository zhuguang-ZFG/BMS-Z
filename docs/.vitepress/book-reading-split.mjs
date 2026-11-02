const SPLIT_RULES = {
  '12-SOC三条路.md': { sections: ['练习', '参考资料'], labelledSubsections: true },
  '14-SOP与热.md': { sections: ['14.4', '14.5', '14.6', '练习', '参考资料'], labelledSubsections: true },
  '24-BMS与AI.md': { sections: ['24.4', '24.5', '24.6', '24.7', '24.8', '练习', '参考资料'] },
  '27-EKF的六个矩阵.md': { sections: ['27.2', '27.5', '27.6', '练习', '参考资料'], labelledSubsections: true },
}

export const splitChapterFiles = Object.keys(SPLIT_RULES)

export function splitBookReading(file, source) {
  const rule = SPLIT_RULES[file]
  if (!rule) return { main: source, deep: '' }

  const main = []
  const deep = []
  const deepParents = new Set()
  let parent = ''
  let parentDeep = false
  let destination = main
  let fence = ''

  for (const line of source.split(/\r?\n/)) {
    const delimiter = line.match(/^\s*(`{3,}|~{3,})/)
    if (delimiter) {
      if (!fence) fence = delimiter[1][0]
      else if (delimiter[1][0] === fence) fence = ''
    } else if (!fence) {
      const h2 = line.match(/^## (.+)$/)
      const h3 = line.match(/^### (.+)$/)
      if (h2) {
        parent = h2[1]
        parentDeep = rule.sections.some((section) => parent === section || parent.startsWith(`${section} `))
        destination = parentDeep ? deep : main
      } else if (h3) {
        const labelledDeep = rule.labelledSubsections && /^第二遍[：:]/.test(h3[1])
        destination = parentDeep || labelledDeep ? deep : main
        if (labelledDeep && !parentDeep && !deepParents.has(parent)) {
          deep.push(`## ${parent}（选读）`, '')
          deepParents.add(parent)
        }
      }
    }
    destination.push(line)
  }

  if (!deep.some((line) => line.startsWith('## ')) || !main[0].startsWith('# ')) {
    throw new Error(`章节拆分缺少正文或进阶内容：${file}`)
  }
  return { main: `${main.join('\n').trim()}\n`, deep: `${deep.join('\n').trim()}\n` }
}
