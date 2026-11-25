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

export function ocvSensitivityValues({ soc, slope }) {
  if (!Number.isFinite(soc) || soc < 0 || soc > 1
    || !Number.isFinite(slope) || slope < 0.05 || slope > 1.2) {
    throw new RangeError('OCV requires SOC in [0, 1] and slope in [0.05, 1.20]')
  }
  const at = position => {
    const low = Math.tanh((position - 0.05) * 30)
    const high = Math.tanh((position - 0.9) * 15)
    const derivative = slope + 6 * (1 - low * low) + 0.75 * (1 - high * high)
    return { voltage: ocvValue(position, slope), derivative, errorPp: 0.005 / derivative * 100,
      terms: [3.2, slope * position, 0.2 * low, 0.05 * high] }
  }
  return { ...at(soc), comparison: [at(0.05), at(0.5)] }
}

function mountOcvLab(panel) {
  const soc = panel.querySelector('[data-param="soc"]')
  const slope = panel.querySelector('[data-param="slope"]')
  const reset = panel.querySelector('[data-lab-reset]')
  const feedback = panel.querySelector('[data-ocv-feedback]')
  const live = panel.querySelector('[data-ocv-live]')
  const outputs = Object.fromEntries(['soc', 'slope', 'voltage', 'derivative', 'error', 'terms',
    'low-error', 'mid-error', 'ratio', 'axis-mid', 'axis-max'].map(key =>
    [key, panel.querySelector(`[data-output="${key}"]`)]))
  const shapes = Object.fromEntries(['curve', 'cursor', 'low-point', 'mid-point', 'low-bar', 'mid-bar'].map(key =>
    [key, panel.querySelector(`[data-ocv-${key}]`)]))
  const answers = [...panel.querySelectorAll('[data-ocv-answer]')]
  const presets = [...panel.querySelectorAll('[data-ocv-soc]')]
  const interactive = [...panel.querySelectorAll('[data-lab-interactive]')]
  if ([soc, slope, reset, feedback, live, ...Object.values(outputs), ...Object.values(shapes)].some(node => !node)
    || answers.length !== 3 || presets.length !== 2 || !interactive.length) return

  const defaults = { soc: Number(soc.defaultValue), slope: Number(slope.defaultValue) }
  const controls = [soc, slope]
  const view = panel.ownerDocument.defaultView
  const x = position => 50 + position * 320
  const y = voltage => 224 - (voltage - 2.8) / 1.9 * 180
  const set = (node, attrs) => Object.entries(attrs).forEach(([name, value]) => node.setAttribute(name, value))
  const draw = state => {
    const result = ocvSensitivityValues(state)
    const [low, mid] = result.comparison
    const axisMax = Math.max(1, Math.ceil(1.2 * Math.max(low.errorPp, mid.errorPp)))
    const text = {
      soc: state.soc.toFixed(2), slope: state.slope.toFixed(2),
      voltage: `${result.voltage.toFixed(4)} V`, derivative: `${result.derivative.toFixed(3)} V/SOC`,
      error: `${result.errorPp.toFixed(3)} 个百分点`,
      terms: result.terms.map((term, index) => `${index ? (term < 0 ? ' − ' : ' + ') : ''}${Math.abs(term).toFixed(4)}`).join('') + ' V',
      'low-error': low.errorPp.toFixed(3), 'mid-error': mid.errorPp.toFixed(3),
      ratio: (mid.errorPp / low.errorPp).toFixed(1), 'axis-mid': String(axisMax / 2), 'axis-max': String(axisMax),
    }
    Object.entries(text).forEach(([key, value]) => { outputs[key].textContent = value })
    shapes.curve.setAttribute('points', Array.from({ length: 101 }, (_, i) =>
      `${x(i / 100).toFixed(3)},${y(ocvValue(i / 100, state.slope)).toFixed(3)}`).join(' '))
    set(shapes.cursor, { cx: x(state.soc), cy: y(result.voltage) })
    set(shapes['low-point'], { cy: y(low.voltage) })
    set(shapes['mid-point'], { y: y(mid.voltage) - 5 })
    set(shapes['low-bar'], { width: 368 * low.errorPp / axisMax })
    set(shapes['mid-bar'], { width: 368 * mid.errorPp / axisMax })
    return text
  }
  const update = () => {
    const text = draw({ soc: Number(soc.value), slope: Number(slope.value) })
    soc.setAttribute('aria-valuetext', `SOC ${text.soc}，OCV ${text.voltage}`)
    slope.setAttribute('aria-valuetext', `${text.slope} 伏每单位 SOC`)
    live.textContent = `SOC ${text.soc}，中段斜率参数 ${text.slope}，OCV ${text.voltage}，局部斜率 ${text.derivative}，5 毫伏局部换算 ${text.error}。`
  }
  const responses = {
    steep: '再想想：陡坡处电压变化快，同样的 5 mV 只对应很小的 SOC 差。默认算例中陡坡为 0.074 个百分点，平台为 0.625。',
    plateau: '答对了。默认算例中平台约 0.625 个百分点，陡坡约 0.074，相差约 8.5 倍。局部换算量 = 5 mV ÷ 局部斜率；平台越平，换算量越大。',
    same: '5 mV 相同，除数却不同。默认两处局部斜率约为 6.800 和 0.800 V/SOC，所以 SOC 换算量不相同。',
  }
  const grade = event => { feedback.textContent = responses[event.currentTarget.dataset.ocvAnswer] }
  const locate = event => { soc.value = event.currentTarget.dataset.ocvSoc; update() }
  const restore = () => {
    soc.value = soc.defaultValue; slope.value = slope.defaultValue
    feedback.textContent = ''; update()
  }
  const printDefault = () => draw(defaults)
  // Render before revealing controls, so a missing/invalid static contract stays readable.
  update()
  interactive.forEach(node => { node.hidden = false })
  controls.forEach(input => { input.disabled = false; input.addEventListener('input', update) })
  answers.forEach(button => button.addEventListener('click', grade))
  presets.forEach(button => button.addEventListener('click', locate))
  reset.addEventListener('click', restore)
  view?.addEventListener('beforeprint', printDefault)
  view?.addEventListener('afterprint', update)
  return () => {
    controls.forEach(input => input.removeEventListener('input', update))
    answers.forEach(button => button.removeEventListener('click', grade))
    presets.forEach(button => button.removeEventListener('click', locate))
    reset.removeEventListener('click', restore)
    view?.removeEventListener('beforeprint', printDefault)
    view?.removeEventListener('afterprint', update)
  }
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

export function passiveBalanceValues({ cellVoltageV, bleedResistanceOhm, chargeDeltaAh }) {
  if (![cellVoltageV, bleedResistanceOhm, chargeDeltaAh].every(value => Number.isFinite(value) && value > 0)) {
    throw new RangeError('Positive, finite passive balancing parameters required')
  }
  const current = cellVoltageV / bleedResistanceOhm
  return { current, power: cellVoltageV * current, time: chargeDeltaAh / current }
}

function mountPassiveBalance(panel) {
  const control = panel.querySelector('[data-param="bleedResistanceOhm"]')
  const reset = panel.querySelector('[data-lab-reset]')
  const heat = panel.querySelector('[data-balance-heat]')
  const feedback = panel.querySelector('[data-balance-feedback]')
  const live = panel.querySelector('[data-balance-live]')
  const answers = [...panel.querySelectorAll('[data-balance-answer]')]
  const interactive = [...panel.querySelectorAll('[data-lab-interactive]')]
  const output = Object.fromEntries(['resistance', 'current', 'power', 'time'].map(key =>
    [key, panel.querySelector(`[data-output="${key}"]`)]))
  if (!control || !reset || !heat || !feedback || !live || !answers.length || !interactive.length
    || Object.values(output).some(node => !node)) return

  const view = panel.ownerDocument.defaultView
  const reference = { cellVoltageV: 4, bleedResistanceOhm: Number(control.defaultValue), chargeDeltaAh: 1 }
  const calculate = bleedResistanceOhm => passiveBalanceValues({ ...reference, bleedResistanceOhm })
  const maxPower = calculate(Number(control.min)).power
  const format = result => ({
    current: `${Number((result.current * 1000).toFixed(1))} mA`,
    power: `${result.power.toFixed(2)} W`,
    time: `${Number(result.time.toFixed(1))} h`,
  })
  const draw = resistance => {
    const result = calculate(resistance)
    for (const [key, value] of Object.entries({ resistance: `${resistance} Ω`, ...format(result) })) {
      output[key].textContent = value
    }
    // Only power controls the line weight; no temperature is calculated.
    heat.setAttribute('stroke-width', (2 + 3 * result.power / maxPower).toFixed(2))
  }
  const update = () => {
    const result = calculate(Number(control.value))
    const values = format(result)
    draw(Number(control.value))
    control.setAttribute('aria-valuetext', `${control.value} 欧姆；电流 ${values.current}；功率 ${values.power}；理想时间 ${values.time}`)
    live.textContent = `电阻 ${control.value} 欧姆，电流 ${values.current}，耗散功率 ${values.power}，理想时间 ${values.time}。`
  }
  const restore = () => { control.value = control.defaultValue; update() }
  const printDefault = () => draw(reference.bleedResistanceOhm)
  const half = format(calculate(reference.bleedResistanceOhm / 2))
  const responses = {
    'current-only': '再想想：电压不变，P = UI。电流加倍，功率也加倍；同样的 1 Ah 泄放得更快。',
    'half-time': `答对了。电流和功率各加倍，时间减半：${half.current}、${half.power}、${half.time}。`,
    'half-power': '时间确实减半。功率却随电流增加：电压固定时，P = U² / R，电阻减半，功率加倍。',
  }
  const grade = event => { feedback.textContent = responses[event.currentTarget.dataset.balanceAnswer] }

  update()
  control.disabled = false
  reset.hidden = false
  interactive.forEach(node => { node.hidden = false })
  control.addEventListener('input', update)
  reset.addEventListener('click', restore)
  answers.forEach(button => button.addEventListener('click', grade))
  view?.addEventListener('beforeprint', printDefault)
  view?.addEventListener('afterprint', update)
  return () => {
    control.removeEventListener('input', update)
    reset.removeEventListener('click', restore)
    answers.forEach(button => button.removeEventListener('click', grade))
    view?.removeEventListener('beforeprint', printDefault)
    view?.removeEventListener('afterprint', update)
  }
}

export function mountBookLab(panel) {
  if (panel.dataset.bookLab === 'passive-balance') return mountPassiveBalance(panel)
  if (panel.dataset.bookLab === 'ocv') return mountOcvLab(panel)
  const controls = [...panel.querySelectorAll('input[data-param]')]
  const output = name => panel.querySelector(`[data-output="${name}"]`)
  const values = () => Object.fromEntries(controls.map(input => [input.dataset.param, Number(input.value)]))
  const update = () => {
    controls.forEach(input => {
      const value = panel.querySelector(`[data-value="${input.dataset.param}"]`)
      if (value) value.textContent = input.value
    })
    if (panel.dataset.bookLab === 'protection') {
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

export const READER_STORAGE_KEY = 'bms-book-reader-v1'
export const READER_MIN_SCALE = 0.9
export const READER_MAX_SCALE = 1.15
const READER_SCALE_STEP = 0.05

export function normalizeReaderPreferences(value = {}) {
  const rawScale = Number(value?.scale)
  const scale = Number.isFinite(rawScale)
    ? Math.min(READER_MAX_SCALE, Math.max(READER_MIN_SCALE,
      Math.round(rawScale / READER_SCALE_STEP) * READER_SCALE_STEP))
    : 1
  return { calm: value?.calm === true, scale: Number(scale.toFixed(2)) }
}

/** Read the stored preferences and put them on <html>. Safe to call repeatedly. */
export function applyReaderPreferences(doc = document) {
  let preferences = normalizeReaderPreferences()
  try {
    preferences = normalizeReaderPreferences(JSON.parse(localStorage.getItem(READER_STORAGE_KEY) || '{}'))
  } catch {}
  doc.documentElement.classList.toggle('book-calm', preferences.calm)
  doc.documentElement.style.setProperty('--book-reader-scale', String(preferences.scale))
  return preferences
}

/**
 * 同一段逻辑的「首屏内联」版本：必须在首次绘制前跑，否则存了静读/大字号的读者
 * 每次冷启动都先看到默认版式、再被跳一下（实测字号差 2.6 px、正文左缘差 187 px、
 * 侧栏凭空出现一次）。VitePress 自己的深色模式也正是用这种内联脚本防闪烁的。
 * 数值边界从上面的常量生成，不手写第二份；clamp 后只写入数字，避免被篡改的
 * localStorage 把任意字符串灌进 CSS 自定义属性。
 */
export const READER_BOOT_SCRIPT = `(()=>{try{` +
  `var p=JSON.parse(localStorage.getItem(${JSON.stringify(READER_STORAGE_KEY)})||"{}");` +
  `var s=Number(p&&p.scale);` +
  `s=isFinite(s)?Math.min(${READER_MAX_SCALE},Math.max(${READER_MIN_SCALE},Math.round(s/${READER_SCALE_STEP})*${READER_SCALE_STEP})):1;` +
  `var e=document.documentElement;` +
  `if(p&&p.calm===true)e.classList.add("book-calm");` +
  `e.style.setProperty("--book-reader-scale",String(Number(s.toFixed(2))));` +
  `}catch(_){}})();`

/** Add a deliberately small reading toolbar to both the offline book and VitePress chapters. */
export function mountCalmReader(root = document) {
  const doc = root?.nodeType === 9 ? root : root?.ownerDocument
  if (!doc?.documentElement || !doc.querySelector('.chapter, .book-reading .vp-doc')) return

  doc.getElementById('book-reader-tools')?.remove()
  doc.getElementById('book-reader-progress')?.remove()

  let preferences = applyReaderPreferences(doc)

  const progress = doc.createElement('div')
  progress.id = 'book-reader-progress'
  progress.className = 'reader-progress'
  progress.setAttribute('aria-hidden', 'true')
  progress.innerHTML = '<span></span>'

  // role="group" 而不是 <aside>：带 aria-label 的 <aside> 会映射成 complementary
  // 地标（HTML-AAM），而整书本来就有 161 个地标（逐章的导读卡、来源锚点、翻页导航，
  // 都是读者真会跳的目标）。再往这张清单里塞一个「四个按钮的设置条」只是噪声——
  // 它是控件组，不是页面区域。
  const tools = doc.createElement('div')
  tools.id = 'book-reader-tools'
  tools.className = 'reader-tools'
  tools.setAttribute('role', 'group')
  tools.setAttribute('aria-label', '阅读设置')
  tools.innerHTML = `
    <button type="button" data-reader-calm aria-pressed="false">静读</button>
    <span class="reader-tools__divider" aria-hidden="true"></span>
    <button type="button" data-reader-smaller aria-label="缩小正文字号">字−</button>
    <output data-reader-scale aria-live="polite">字号 100%</output>
    <button type="button" data-reader-larger aria-label="放大正文字号">字＋</button>`
  doc.body.append(progress, tools)

  const calmButton = tools.querySelector('[data-reader-calm]')
  const smallerButton = tools.querySelector('[data-reader-smaller]')
  const largerButton = tools.querySelector('[data-reader-larger]')
  const scaleOutput = tools.querySelector('[data-reader-scale]')
  const progressBar = progress.firstElementChild

  const store = () => {
    try { localStorage.setItem(READER_STORAGE_KEY, JSON.stringify(preferences)) } catch {}
  }
  const preserveReadingPlace = change => {
    const candidates = [...doc.querySelectorAll(
      '.chapter :is(h2,h3,h4,p,li), .book-reading .vp-doc :is(h1,h2,h3,h4,p,li)'
    )]
    const anchor = candidates.find(element => element.getBoundingClientRect().bottom > window.innerHeight * 0.28)
    const top = anchor?.getBoundingClientRect().top
    const previousOverflowAnchor = doc.documentElement.style.overflowAnchor
    doc.documentElement.style.overflowAnchor = 'none'
    change()
    window.requestAnimationFrame(() => window.requestAnimationFrame(() => {
      if (anchor && Number.isFinite(top)) window.scrollBy(0, anchor.getBoundingClientRect().top - top)
      doc.documentElement.style.overflowAnchor = previousOverflowAnchor
      updateProgress()
    }))
  }
  const render = () => {
    doc.documentElement.classList.toggle('book-calm', preferences.calm)
    doc.documentElement.style.setProperty('--book-reader-scale', String(preferences.scale))
    // 开关键的文字固定写「静读」，状态只由 aria-pressed（和它对应的样式）表达。
    // 原先按状态换成「退出静读」有两处坏处：读屏会念出「退出静读，已按下」——
    // 标签说的是下一步动作、aria-pressed 说的是当前状态，两句自相矛盾；
    // 而且四字比两字宽，一点就把工具条撑宽 23 px，右边三个控件跟着右移 23 px，
    // 想接着点「字＋」会发现它已经从指针下挪走了（实测）。
    calmButton.setAttribute('aria-pressed', String(preferences.calm))
    scaleOutput.textContent = `字号 ${Math.round(preferences.scale * 100)}%`
    smallerButton.disabled = preferences.scale <= READER_MIN_SCALE
    largerButton.disabled = preferences.scale >= READER_MAX_SCALE
  }
  const changeScale = delta => {
    preserveReadingPlace(() => {
      preferences = normalizeReaderPreferences({ ...preferences, scale: preferences.scale + delta })
      render(); store()
    })
  }
  const toggleCalm = () => {
    preserveReadingPlace(() => {
      preferences = { ...preferences, calm: !preferences.calm }
      render(); store()
    })
  }
  const updateProgress = () => {
    const scrolling = doc.scrollingElement || doc.documentElement
    const distance = Math.max(1, scrolling.scrollHeight - window.innerHeight)
    const ratio = Math.min(1, Math.max(0, window.scrollY / distance))
    progressBar.style.transform = `scaleX(${ratio})`
  }

  const onSmaller = () => changeScale(-READER_SCALE_STEP)
  const onLarger = () => changeScale(READER_SCALE_STEP)
  calmButton.addEventListener('click', toggleCalm)
  smallerButton.addEventListener('click', onSmaller)
  largerButton.addEventListener('click', onLarger)
  window.addEventListener('scroll', updateProgress, { passive: true })
  window.addEventListener('resize', updateProgress, { passive: true })
  render(); updateProgress()

  /**
   * 只拆监听与自己建的节点，**不动** <html> 上的 book-calm 与 --book-reader-scale：
   * 逐章路由每次切页都会先 cleanup 再重挂，顺手重置这两项的话，重挂前的那几帧
   * 会按默认版式渲染——静读读者会看到侧栏闪一下、正文左缘跳 187 px、字号跳 2.6 px。
   * 这两项是从 localStorage 读出来的用户偏好，不是本次挂载的副作用，留着才是对的。
   */
  return () => {
    calmButton.removeEventListener('click', toggleCalm)
    smallerButton.removeEventListener('click', onSmaller)
    largerButton.removeEventListener('click', onLarger)
    window.removeEventListener('scroll', updateProgress)
    window.removeEventListener('resize', updateProgress)
    progress.remove(); tools.remove()
  }
}
