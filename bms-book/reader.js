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
