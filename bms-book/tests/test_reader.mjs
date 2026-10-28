import test from 'node:test'
import assert from 'node:assert/strict'
import {
  normalizeReaderPreferences, ocvValue, protectionTimingValues, sopValues, thermalValues,
  READER_BOOT_SCRIPT, READER_MAX_SCALE, READER_MIN_SCALE, READER_STORAGE_KEY,
} from '../reader.js'

test('OCV decomposition matches the reference midpoint', () => {
  assert.ok(Math.abs(ocvValue(0.5, 0.8) - 3.75) < 1e-6)
  assert.ok(Math.abs(ocvValue(0.5, 0.4) - 3.55) < 1e-6)
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
