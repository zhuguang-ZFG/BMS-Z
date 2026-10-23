import test from 'node:test'
import assert from 'node:assert/strict'
import { ocvValue, sopValues } from '../reader.js'

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
