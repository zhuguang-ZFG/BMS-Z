import test from 'node:test'
import assert from 'node:assert/strict'
import { ocvValue, protectionTimingValues, sopValues, thermalValues } from '../reader.js'

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
