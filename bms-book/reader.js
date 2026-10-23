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
  controls.forEach(input => { input.disabled = false; input.addEventListener('input', update) })
  update()
  return () => controls.forEach(input => input.removeEventListener('input', update))
}
