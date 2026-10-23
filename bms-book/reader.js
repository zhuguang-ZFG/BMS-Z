/** Shared progressive enhancement for offline and VitePress book readers. */
export function mountBookMotion(button) {
  const figure = button.closest('.book-motion')
  const picture = figure?.querySelector('img')
  if (!figure || !picture?.dataset.motionSrc) return
  const snapshot = picture.getAttribute('src')
  const stop = () => {
    picture.setAttribute('src', snapshot)
    figure.dataset.mode = 'static'
    button.setAttribute('aria-pressed', 'false')
    button.textContent = '播放动画'
  }
  button.hidden = false
  const toggle = () => {
    if (figure.dataset.mode === 'playing') return stop()
    picture.setAttribute('src', picture.dataset.motionSrc)
    figure.dataset.mode = 'playing'
    button.setAttribute('aria-pressed', 'true')
    button.textContent = '停止 · 看静态图'
  }
  button.addEventListener('click', toggle)
  window.addEventListener('beforeprint', stop)
  const observer = typeof IntersectionObserver === 'undefined' ? null : new IntersectionObserver(entries => {
    if (!entries[0].isIntersecting && figure.dataset.mode === 'playing') stop()
  })
  observer?.observe(figure)
  return () => { observer?.disconnect(); button.removeEventListener('click', toggle); window.removeEventListener('beforeprint', stop) }
}

export function ocvValue(soc, slope) {
  return 3.2 + slope * soc + 0.2 * Math.tanh((soc - 0.05) * 30)
    + 0.05 * Math.tanh((soc - 0.9) * 15)
}

export function sopValues({ ocv, resistance, capacity, soc, horizon, cap }) {
  // Positive discharge magnitude. Fixed OCV/Rint example, not an RC/thermal solver.
  const voltageCurrent = Math.max(0, (ocv - 2.8) / resistance)
  const socCurrent = Math.max(0, (soc - 0.10) * 3600 * capacity / horizon)
  const current = Math.min(voltageCurrent, socCurrent, cap)
  const voltage = ocv - current * resistance
  const limits = [['电压墙', voltageCurrent], ['SOC 墙', socCurrent], ['电流帽', cap]]
  const binding = limits.filter(([, value]) => Math.abs(value - current) < 1e-9).map(([label]) => label).join(' + ')
  return { voltageCurrent, socCurrent, current, voltage, power: current * voltage,
    heat: current * current * resistance, binding }
}

export function thermalValues({ current, resistance, rth, cth, ambient, initial, horizon, limit }) {
  if (resistance <= 0 || rth <= 0 || cth <= 0 || horizon <= 0) throw new RangeError('Positive thermal parameters required')
  const tau = rth * cth
  const a = Math.exp(-horizon / tau)
  const heat = current ** 2 * resistance
  const steady = ambient + heat * rth
  const final = steady + (initial - steady) * a
  const numerator = limit - ambient - (initial - ambient) * a
  const allowed = initial > limit ? 0 : Math.sqrt(Math.max(0, numerator) / (resistance * rth * (1 - a)))
  return { tau, heat, steady, final, allowed }
}

export function protectionTimingValues({ samplePeriod, confirmCount, decision, actuator, ftti }) {
  const values = [samplePeriod, confirmCount, decision, actuator, ftti]
  if (!values.every(Number.isFinite) || samplePeriod <= 0 || !Number.isInteger(confirmCount)
    || confirmCount < 1 || decision < 0 || actuator < 0 || ftti <= 0) {
    throw new RangeError('Valid protection timing parameters required')
  }
  const observed = (confirmCount - 1) * samplePeriod + decision + actuator
  const worstCase = confirmCount * samplePeriod + decision + actuator
  const margin = ftti - worstCase
  return { observed, worstCase, margin, withinBudget: margin >= 0 }
}

export function mountBookLab(panel) {
  const controls = [...panel.querySelectorAll('input[data-param]')]
  const output = name => panel.querySelector(`[data-output="${name}"]`)
  const values = () => Object.fromEntries(controls.map(input => [input.dataset.param, Number(input.value)]))
  const update = () => {
    controls.forEach(input => {
      const value = panel.querySelector(`[data-value="${input.dataset.param}"]`)
      if (value) value.textContent = input.value
    })
    if (panel.dataset.bookLab === 'ocv') {
      const { soc, slope } = values()
      const voltage = ocvValue(soc, slope)
      const low = Math.tanh((soc - 0.05) * 30)
      const high = Math.tanh((soc - 0.90) * 15)
      const derivative = slope + 6 * (1 - low * low) + 0.75 * (1 - high * high)
      output('voltage').textContent = `${voltage.toFixed(4)} V`
      output('derivative').textContent = `${derivative.toFixed(3)} V/SOC`
      output('error').textContent = `${(0.005 / derivative * 100).toFixed(2)} 个百分点`
      const points = Array.from({ length: 101 }, (_, index) => {
        const s = index / 100
        return `${60 + s * 600},${270 - (ocvValue(s, slope) - 2.8) * 130}`
      }).join(' ')
      panel.querySelector('[data-curve]').setAttribute('points', points)
      const x = 60 + soc * 600
      const y = 270 - (voltage - 2.8) * 130
      const dot = panel.querySelector('[data-cursor]')
      dot.setAttribute('cx', x); dot.setAttribute('cy', y)
      panel.querySelector('[data-band]').setAttribute('y', y - 4)
      output('terms').textContent = `3.2000 + ${(slope * soc).toFixed(4)} + ${(0.2 * low).toFixed(4)} + ${(0.05 * high).toFixed(4)} V`
    } else if (panel.dataset.bookLab === 'protection') {
      const p = values()
      const result = protectionTimingValues(p)
      output('observed').textContent = `${result.observed.toFixed(0)} ms`
      output('worst').textContent = `${result.worstCase.toFixed(0)} ms`
      output('margin').textContent = `${result.margin >= 0 ? '+' : ''}${result.margin.toFixed(0)} ms`
      const status = output('status')
      status.textContent = result.withinBudget ? '预算内' : '超出预算'
      status.dataset.state = result.withinBudget ? 'within' : 'over'
      const durations = [p.samplePeriod, (p.confirmCount - 1) * p.samplePeriod, p.decision, p.actuator]
      const scale = Math.max(result.worstCase, p.ftti)
      panel.querySelectorAll('[data-timing-phase]').forEach((segment, index) => {
        segment.style.width = `${durations[index] / scale * 100}%`
      })
      panel.querySelector('[data-timing-ftti]').style.left = `${p.ftti / scale * 100}%`
    } else if (panel.dataset.bookLab === 'thermal') {
      const p = values()
      const setup = { current: p.current, resistance: 0.049, rth: p.rth, cth: p.cth,
        ambient: 25, initial: p.initial, horizon: p.horizon, limit: 40 }
      const result = thermalValues(setup)
      output('tau').textContent = `${result.tau.toFixed(0)} s`
      output('heat').textContent = `${result.heat.toFixed(2)} W`
      output('final').textContent = `${result.final.toFixed(3)} °C`
      output('steady').textContent = `${result.steady.toFixed(2)} °C`
      output('allowed').textContent = `${result.allowed.toFixed(3)} A`
      const maxT = Math.max(45, result.steady + 3, setup.initial + 3)
      const y = temperature => 260 - (temperature - 20) / (maxT - 20) * 210
      const points = Array.from({ length: 101 }, (_, index) => {
        const t = index / 100 * setup.horizon
        const temperature = result.steady + (setup.initial - result.steady) * Math.exp(-t / result.tau)
        return `${60 + index * 6},${y(temperature)}`
      }).join(' ')
      panel.querySelector('[data-thermal-curve]').setAttribute('points', points)
      panel.querySelector('[data-limit-line]').setAttribute('d', `M60 ${y(40)}H660`)
      panel.querySelector('[data-end-label]').textContent = `${setup.horizon} s`
      panel.querySelector('[data-top-label]').textContent = `${maxT.toFixed(0)} °C`
    } else {
      const p = values()
      const result = sopValues({ ocv: p.ocv, resistance: p.resistance / 1000,
        capacity: 10, soc: p.soc, horizon: p.horizon, cap: 30 })
      const limits = [result.voltageCurrent, result.socCurrent, 30]
      limits.forEach((value, i) => {
        const rect = panel.querySelector(`[data-bar="${i}"]`)
        rect.setAttribute('width', Math.min(100, value) / 100 * 470)
        output(`limit-${i}`).textContent = `${value.toFixed(1)} A`
      })
      output('current').textContent = `${result.current.toFixed(1)} A`
      output('power').textContent = `${result.power.toFixed(1)} W`
      output('heat').textContent = `${result.heat.toFixed(1)} W`
      output('binding').textContent = result.binding
      output('terminal').textContent = `${result.voltage.toFixed(3)} V`
    }
  }
  const defaults = controls.map(input => input.value)
  const reset = () => { controls.forEach((input,index) => { input.value = defaults[index] }); update() }
  const resetButton = panel.querySelector('[data-lab-reset]')
  if (resetButton) { resetButton.hidden = false; resetButton.addEventListener('click', reset) }
  controls.forEach(input => { input.disabled = false; input.addEventListener('input', update) })
  update()
  return () => { controls.forEach(input => input.removeEventListener('input', update)); resetButton?.removeEventListener('click', reset) }
}
