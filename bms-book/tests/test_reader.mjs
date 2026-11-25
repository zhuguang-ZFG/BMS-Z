import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  mountBookLab, normalizeReaderPreferences, ocvValue, ocvSensitivityValues, passiveBalanceValues, protectionTimingValues, sopValues, thermalValues,
  READER_BOOT_SCRIPT, READER_MAX_SCALE, READER_MIN_SCALE, READER_STORAGE_KEY,
} from '../reader.js'
import { bookChapters, siteChapter } from '../../docs/.vitepress/book-sources.mjs'

test('VitePress chapters render one complete reading route', () => {
  const numbered = bookChapters.filter(chapter => /^(?!00-)\d{2}-/.test(chapter.file))
  assert.equal(numbered.length, 32)
  for (const chapter of numbered) {
    const index = bookChapters.indexOf(chapter)
    const page = siteChapter(chapter, index)
    assert.equal(page.match(/<aside class="chapter-route" aria-label="阅读路径">/g)?.length, 1, chapter.file)
    for (const label of ['第一次主线', '第二遍深挖', '动手验证']) {
      assert.equal(page.match(new RegExp(`<strong>${label}</strong><span>`, 'g'))?.length, 1, `${chapter.file} · ${label}`)
    }
    assert.doesNotMatch(page, /^::: chapter-route/m, chapter.file)
  }
})

test('OCV decomposition matches the reference midpoint', () => {
  assert.ok(Math.abs(ocvValue(0.5, 0.8) - 3.75) < 1e-6)
  assert.ok(Math.abs(ocvValue(0.5, 0.4) - 3.55) < 1e-6)
})

test('OCV sensitivity matches independent reference values and rejects invalid inputs', () => {
  for (const [soc, slope, voltage, derivative, errorPp] of [
    [0.5, 0.8, 3.75000061, 0.80001843, 0.62498560],
    [0.05, 0.8, 3.19, 6.8, 0.07352941],
    [0.5, 0.4, 3.55000061, 0.40001843, 1.24994240],
    [0.5, 0.05, 3.37500061, 0.05001843, 9.99631487],
    [0, 0.8, 2.96897035, 1.88423983, 0.26535900],
    [1, 1.2, 4.64525741, 1.33552998, 0.37438321],
  ]) {
    const result = ocvSensitivityValues({ soc, slope })
    for (const key of ['voltage', 'derivative', 'errorPp']) {
      assert.ok(Math.abs(result[key] - ({ voltage, derivative, errorPp })[key]) < 1e-8, key)
    }
    assert.ok(Math.abs(result.terms.reduce((sum, value) => sum + value, 0) - result.voltage) < 1e-12)
    assert.ok(result.comparison[1].errorPp > result.comparison[0].errorPp)
  }
  for (const bad of [{ soc: -0.01 }, { soc: 1.01 }, { soc: NaN }, { soc: '0.5' },
    { slope: 0 }, { slope: 1.21 }, { slope: Infinity }]) {
    assert.throws(() => ocvSensitivityValues({ soc: 0.5, slope: 0.8, ...bad }), RangeError)
  }
})

function ocvFixture() {
  const chapter = readFileSync(new URL('../book/10-模型OCV四项.md', import.meta.url), 'utf8')
  const source = chapter.match(/<section[^>]+data-book-lab="ocv"[\s\S]*?<\/section>/)[0]
  const nodes = [...source.matchAll(/<([a-z]+)\b([^>]+)>/g)].map(([, tag, attrs]) => {
    const attributes = Object.fromEntries([...attrs.matchAll(/([\w-]+)(?:="([^"]*)")?/g)]
      .map(([, key, value]) => [key, value ?? '']))
    const dataset = Object.fromEntries(Object.entries(attributes).filter(([key]) => key.startsWith('data-'))
      .map(([key, value]) => [key.slice(5).replace(/-([a-z])/g, (_, char) => char.toUpperCase()), value]))
    return Object.assign(new EventTarget(), { tag, attributes, dataset, textContent: '',
      value: attributes.value, defaultValue: attributes.value,
      disabled: 'disabled' in attributes, hidden: 'hidden' in attributes,
      setAttribute(name, value) { this.attributes[name] = String(value) },
    })
  })
  const all = selector => {
    const [, key, value] = selector.match(/^\[([\w-]+)(?:="([^"]*)")?\]$/)
    return nodes.filter(node => key in node.attributes && (value === undefined || node.attributes[key] === value))
  }
  const view = new EventTarget()
  const panel = { dataset: { bookLab: 'ocv' }, ownerDocument: { defaultView: view },
    querySelector: selector => all(selector)[0], querySelectorAll: all }
  return { panel, view, all, get: panel.querySelector }
}

test('OCV chapter geometry agrees with runtime defaults and stays within fixed axes', () => {
  const { panel, get } = ocvFixture()
  const curve = get('[data-ocv-curve]')
  const original = curve.attributes.points
  const widths = ['low', 'mid'].map(key => Number(get(`[data-ocv-${key}-bar]`).attributes.width))
  const cleanup = mountBookLab(panel)
  assert.equal(curve.attributes.points, original)
  for (const [i, key] of ['low', 'mid'].entries()) {
    assert.ok(Math.abs(Number(get(`[data-ocv-${key}-bar]`).attributes.width) - widths[i]) < 1e-6)
  }
  const slope = get('[data-param="slope"]')
  const soc = get('[data-param="soc"]')
  for (const k of [0.05, 0.8, 1.2]) {
    for (const position of [0, 0.05, 0.5, 1]) {
      slope.value = String(k); soc.value = String(position)
      slope.dispatchEvent(new Event('input'))
      for (const pair of curve.attributes.points.split(' ')) {
        const [x, y] = pair.split(',').map(Number)
        assert.ok(x >= 50 && x <= 370 && y >= 44 && y <= 224, pair)
      }
      const low = Number(get('[data-ocv-low-bar]').attributes.width)
      const mid = Number(get('[data-ocv-mid-bar]').attributes.width)
      assert.ok(low > 0 && mid > low && mid <= 368)
      const result = ocvSensitivityValues({ soc: position, slope: k })
      assert.ok(Math.abs(mid / low - result.comparison[1].errorPp / result.comparison[0].errorPp) < 1e-10)
    }
  }
  cleanup()
})

test('OCV grading, presets, print restoration, reset and disposal use the actual chapter controls', () => {
  const { panel, view, get, all } = ocvFixture()
  const cleanup = mountBookLab(panel)
  const soc = get('[data-param="soc"]'), slope = get('[data-param="slope"]')
  const feedback = get('[data-ocv-feedback]')
  const read = name => get(`[data-output="${name}"]`).textContent
  assert.ok(all('[data-lab-interactive]').every(node => !node.hidden))
  assert.equal(soc.disabled, false)
  assert.equal(read('voltage'), '3.7500 V')
  assert.equal(read('error'), '0.625 个百分点')
  assert.doesNotMatch(read('terms'), /\+ -/)
  for (const [answer, message] of [['steep', /再想想/], ['same', /除数却不同/], ['plateau', /答对了.*8\.5/]]) {
    get(`[data-ocv-answer="${answer}"]`).dispatchEvent(new Event('click'))
    assert.match(feedback.textContent, message)
  }
  const response = feedback.textContent
  slope.value = '0.40'
  get('[data-ocv-soc="0.05"]').dispatchEvent(new Event('click'))
  assert.equal(slope.value, '0.40')
  assert.equal(read('soc'), '0.05')
  get('[data-ocv-soc="0.50"]').dispatchEvent(new Event('click'))
  assert.equal(read('voltage'), '3.5500 V')
  assert.equal(read('error'), '1.250 个百分点')
  assert.match(get('[data-ocv-live]').textContent, /3\.5500.*1\.250/)
  assert.match(soc.attributes['aria-valuetext'], /SOC 0\.50/)
  view.dispatchEvent(new Event('beforeprint'))
  assert.equal(read('slope'), '0.80')
  assert.equal(read('voltage'), '3.7500 V')
  assert.equal(slope.value, '0.40')
  view.dispatchEvent(new Event('afterprint'))
  assert.equal(read('slope'), '0.40')
  assert.equal(feedback.textContent, response)
  get('[data-lab-reset]').dispatchEvent(new Event('click'))
  assert.equal(read('error'), '0.625 个百分点')
  assert.equal(feedback.textContent, '')
  cleanup()
  slope.value = '0.4'
  slope.dispatchEvent(new Event('input'))
  get('[data-ocv-soc="0.05"]').dispatchEvent(new Event('click'))
  get('[data-ocv-answer="plateau"]').dispatchEvent(new Event('click'))
  view.dispatchEvent(new Event('afterprint'))
  assert.equal(read('slope'), '0.80')
  assert.equal(soc.value, '0.50')
  assert.equal(feedback.textContent, '')
})
test('SOP minimum switches from SOC to voltage constraint', () => {
  const setup = { ocv: 3.7, resistance: 0.02, capacity: 10, soc: 0.5, horizon: 600, cap: 30 }
  const first = sopValues(setup)
  assert.equal(first.current, 24)
  assert.equal(first.binding, 'SOC 墙')
  const second = sopValues({ ...setup, resistance: 0.06 })
  assert.ok(Math.abs(second.current - 15) < 1e-9)
  assert.equal(second.binding, '电压墙')
  assert.ok(Math.abs(second.voltage - 2.8) < 1e-9)
})
test('SOP forbids discharge below the SOC reserve', () => {
  assert.equal(sopValues({ ocv: 3.7, resistance: 0.02, capacity: 10, soc: 0.05, horizon: 600, cap: 30 }).current, 0)
})
test('thermal heat capacity changes speed but not equilibrium', () => {
  const setup = { current:10, resistance:0.049, rth:1, cth:120, ambient:25, initial:25, horizon:120, limit:40 }
  const first = thermalValues(setup)
  const fast = thermalValues({ ...setup, cth:60 })
  assert.equal(first.steady, fast.steady)
  assert.equal(first.tau, fast.tau * 2)
  assert.ok(fast.final > first.final)
  assert.ok(Math.abs(first.final - 28.09739073826) < 1e-6)
  const boundary = thermalValues({ ...setup, current:first.allowed })
  assert.ok(Math.abs(boundary.final - 40) < 1e-9)
  assert.equal(thermalValues({ ...setup, initial:45 }).allowed, 0)
})

test('protection timing separates observed and worst-case detection latency', () => {
  const result = protectionTimingValues({ samplePeriod: 20, confirmCount: 3, decision: 2, actuator: 15, ftti: 100 })
  assert.deepEqual(result, { observed: 57, worstCase: 77, margin: 23, withinBudget: true })
})
test('single-sample confirmation can still exceed the physical fault budget', () => {
  const result = protectionTimingValues({ samplePeriod: 40, confirmCount: 1, decision: 5, actuator: 70, ftti: 100 })
  assert.deepEqual(result, { observed: 75, worstCase: 115, margin: -15, withinBudget: false })
})
test('protection timing rejects impossible confirmation settings', () => {
  assert.throws(
    () => protectionTimingValues({ samplePeriod: 20, confirmCount: 0, decision: 2, actuator: 15, ftti: 100 }),
    RangeError,
  )
})

test('passive balancing matches the chapter example and both slider limits', () => {
  const setup = { cellVoltageV: 4, chargeDeltaAh: 1 }
  for (const [bleedResistanceOhm, current, power, time] of [
    [50, 0.08, 0.32, 12.5], [100, 0.04, 0.16, 25], [200, 0.02, 0.08, 50],
  ]) {
    assert.deepEqual(passiveBalanceValues({ ...setup, bleedResistanceOhm }), { current, power, time })
  }
  for (const bad of [{ bleedResistanceOhm: 0 }, { cellVoltageV: Infinity }, { chargeDeltaAh: -1 }]) {
    assert.throws(() => passiveBalanceValues({ ...setup, bleedResistanceOhm: 100, ...bad }), RangeError)
  }
})

test('passive balance lab updates the diagram, grades answers and preserves the setting after print', () => {
  const node = (fields = {}) => Object.assign(new EventTarget(), { attributes: {},
    setAttribute(name, value) { this.attributes[name] = value }, ...fields })
  const control = node({ min: '50', value: '100', defaultValue: '100', disabled: true })
  const reset = node({ hidden: true })
  const heat = node()
  const feedback = node({ textContent: '' })
  const live = node({ textContent: '' })
  const outputs = ['resistance', 'current', 'power', 'time'].map(() => node())
  const answers = ['current-only', 'half-time', 'half-power'].map(balanceAnswer => node({ dataset: { balanceAnswer } }))
  const groups = [node({ hidden: true }), node({ hidden: true })]
  const view = new EventTarget()
  const elements = {
    '[data-param="bleedResistanceOhm"]': control, '[data-lab-reset]': reset,
    '[data-balance-heat]': heat, '[data-balance-feedback]': feedback, '[data-balance-live]': live,
    ...Object.fromEntries(['resistance', 'current', 'power', 'time'].map((key, i) => [`[data-output="${key}"]`, outputs[i]])),
  }
  const cleanup = mountBookLab({
    dataset: { bookLab: 'passive-balance' }, ownerDocument: { defaultView: view },
    querySelector: selector => elements[selector],
    querySelectorAll: selector => ({ '[data-balance-answer]': answers, '[data-lab-interactive]': groups })[selector],
  })
  const read = () => outputs.map(output => output.textContent)
  const baseline = ['100 Ω', '40 mA', '0.16 W', '25 h']
  assert.equal(control.disabled, false)
  assert.ok(groups.every(group => !group.hidden))
  assert.deepEqual(read(), baseline)
  assert.match(control.attributes['aria-valuetext'], /40 mA.*0\.16 W.*25 h/)
  const baseWeight = Number(heat.attributes['stroke-width'])
  control.value = '50'
  control.dispatchEvent(new Event('input'))
  const halved = ['50 Ω', '80 mA', '0.32 W', '12.5 h']
  assert.deepEqual(read(), halved)
  assert.match(control.attributes['aria-valuetext'], /80 mA.*0\.32 W.*12\.5 h/)
  assert.match(live.textContent, /80 mA.*0\.32 W.*12\.5 h/)
  assert.ok(Number(heat.attributes['stroke-width']) > baseWeight)
  for (const [i, message] of [/再想想/, /答对了.*80 mA.*0\.32 W.*12\.5 h/, /时间确实减半.*功率加倍/].entries()) {
    answers[i].dispatchEvent(new Event('click'))
    assert.match(feedback.textContent, message)
  }
  view.dispatchEvent(new Event('beforeprint'))
  assert.deepEqual(read(), baseline)
  view.dispatchEvent(new Event('afterprint'))
  assert.deepEqual(read(), halved)
  reset.dispatchEvent(new Event('click'))
  assert.deepEqual(read(), baseline)
  cleanup()
  control.value = '200'
  control.dispatchEvent(new Event('input'))
  assert.deepEqual(read(), baseline)
})

test('reader preferences keep calm mode and clamp font scaling', () => {
  assert.deepEqual(normalizeReaderPreferences(), { calm: false, scale: 1 })
  assert.deepEqual(normalizeReaderPreferences({ calm: true, scale: 1.08 }), { calm: true, scale: 1.1 })
  assert.deepEqual(normalizeReaderPreferences({ calm: 1, scale: 9 }), { calm: false, scale: 1.15 })
  assert.deepEqual(normalizeReaderPreferences({ scale: 0.2 }), { calm: false, scale: 0.9 })
})

/** 把首屏内联脚本放进一个最小 DOM 替身里跑，验证它和运行时得出同一个结论。 */
function runBootScript(stored) {
  const classes = new Set()
  const properties = {}
  const documentElement = {
    classList: { add: name => classes.add(name) },
    style: { setProperty: (name, value) => { properties[name] = value } },
  }
  const sandbox = {
    document: { documentElement },
    localStorage: { getItem: key => (key === READER_STORAGE_KEY ? stored : null) },
    JSON, Math, Number, isFinite,
  }
  // 内联脚本是给浏览器全局环境写的，这里用 Function 注入同名替身，不碰真实 DOM。
  const names = Object.keys(sandbox)
  new Function(...names, READER_BOOT_SCRIPT)(...names.map(name => sandbox[name]))
  return { calm: classes.has('book-calm'), scale: properties['--book-reader-scale'] }
}

test('the first-paint boot script agrees with the runtime normaliser', () => {
  for (const preferences of [
    { calm: true, scale: 1.15 }, { calm: false, scale: 1 }, { calm: true, scale: 0.9 },
    { calm: false, scale: 1.08 }, { calm: true, scale: 42 }, { calm: false, scale: -3 },
    { calm: 'yes', scale: '1.1' }, {},
  ]) {
    const expected = normalizeReaderPreferences(preferences)
    const actual = runBootScript(JSON.stringify(preferences))
    assert.deepEqual(
      actual, { calm: expected.calm, scale: String(expected.scale) },
      `首屏脚本与运行时对 ${JSON.stringify(preferences)} 的结论不一致`,
    )
  }
})

test('the boot script survives missing, corrupt and hostile storage', () => {
  // 没存过偏好：按默认值落字号，不加静读类。
  assert.deepEqual(runBootScript(null), { calm: false, scale: '1' })
  // 存了一段不是 JSON 的东西：整段 try 失败，<html> 不留任何痕迹（后续运行时再补）。
  assert.deepEqual(runBootScript('not json'), { calm: false, scale: undefined })
  // 被篡改的值只能变成数字：非数字走默认 1，不会把任意字符串灌进 CSS 自定义属性。
  const injected = runBootScript(JSON.stringify({ calm: true, scale: '2; background:red' }))
  assert.deepEqual(injected, { calm: true, scale: '1' })
  assert.equal(normalizeReaderPreferences({ scale: '2; background:red' }).scale, 1)
  // 超出上限的合法数字按上限收。
  assert.equal(runBootScript(JSON.stringify({ scale: 42 })).scale, String(READER_MAX_SCALE))
  assert.match(runBootScript(JSON.stringify({ scale: 1.05 })).scale, /^\d+(\.\d+)?$/)
})

test('the boot script can be inlined into a document head', () => {
  // 两条硬边界：必须同时落静读类与字号变量；不能含 </script（会截断内联文档）。
  assert.ok(READER_BOOT_SCRIPT.includes('book-calm'))
  assert.ok(READER_BOOT_SCRIPT.includes('--book-reader-scale'))
  assert.ok(!READER_BOOT_SCRIPT.toLowerCase().includes('</script'))
  // 边界常量由运行时常量生成，不是手抄的第二份。
  assert.ok(READER_BOOT_SCRIPT.includes(String(READER_MIN_SCALE)))
  assert.ok(READER_BOOT_SCRIPT.includes(String(READER_MAX_SCALE)))
  assert.ok(READER_BOOT_SCRIPT.includes(JSON.stringify(READER_STORAGE_KEY)))
})
