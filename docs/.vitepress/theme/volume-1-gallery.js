/**
 * 卷一动画画廊：筛选、搜索、随机与放大播放。
 *
 * 与 MkDocs 版同一套交互，但监听器全部随页面卸载——VitePress 是 SPA，
 * 换页后旧节点没了，挂在 document 上的 keydown 必须自己拆掉。
 */
import { withBase } from 'vitepress'

export function mountVolume1Gallery(root = document) {
  const cards = Array.from(root.querySelectorAll('.gal-card'))
  if (!cards.length) return undefined

  const search = root.getElementById('gal-search')
  const chips = Array.from(root.querySelectorAll('.gal-chip'))
  const empty = root.getElementById('gal-empty')
  const counter = root.getElementById('gal-count')
  const randomBtn = root.getElementById('gal-random')
  const modal = root.getElementById('gal-modal')
  if (!modal) return undefined

  const image = root.getElementById('gal-modal-img')
  const title = root.getElementById('gal-modal-title')
  const link = root.getElementById('gal-modal-link')
  const close = root.getElementById('gal-modal-close')
  const prev = root.getElementById('gal-modal-prev')
  const next = root.getElementById('gal-modal-next')
  const position = root.getElementById('gal-modal-pos')
  const state = { chapter: 'all', query: '' }
  let visible = cards.slice()
  let current = -1
  let returnFocus = null
  let previousOverflow = ''

  function apply() {
    visible = []
    for (const card of cards) {
      const chapterOk = state.chapter === 'all' || card.dataset.ch === state.chapter
      const haystack = `${card.dataset.title || ''} ${card.dataset.file || ''}`.toLowerCase()
      const queryOk = !state.query || haystack.includes(state.query)
      const show = chapterOk && queryOk
      card.style.display = show ? '' : 'none'
      if (show) visible.push(card)
    }
    if (empty) empty.style.display = visible.length ? 'none' : ''
    if (counter) counter.textContent = `${visible.length} / ${cards.length}`
    if (randomBtn) randomBtn.disabled = !visible.length
    for (const chip of chips) chip.setAttribute('aria-pressed', String(chip.dataset.ch === state.chapter))
  }

  function pickSvg(src, reduced) {
    if (!reduced) return src
    const query = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)')
    return query && query.matches ? src.replace(/\.svg$/, '.reduce.svg') : src
  }

  function render(card) {
    const button = card.querySelector('.gal-play')
    if (!button) return
    image.setAttribute('src', withBase(pickSvg(button.dataset.svg, button.dataset.reduce === '1')))
    image.setAttribute('alt', button.dataset.title)
    title.textContent = button.dataset.title
    link.setAttribute('href', button.dataset.href)
    current = visible.indexOf(card)
    const many = current >= 0 && visible.length > 1
    position.textContent = current >= 0 ? `${current + 1} / ${visible.length}` : ''
    prev.style.visibility = many ? '' : 'hidden'
    next.style.visibility = many ? '' : 'hidden'
  }

  function isOpen() { return modal.classList.contains('is-open') }

  function open(card) {
    if (!isOpen()) {
      returnFocus = document.activeElement
      previousOverflow = document.body.style.overflow
    }
    render(card)
    modal.classList.add('is-open')
    document.body.style.overflow = 'hidden'
    close.focus()
  }

  function closeModal() {
    if (!isOpen()) return
    modal.classList.remove('is-open')
    image.removeAttribute('src')
    document.body.style.overflow = previousOverflow
    current = -1
    if (returnFocus && returnFocus.isConnected) returnFocus.focus()
  }

  function step(delta) {
    if (!isOpen() || !visible.length) return
    const base = current < 0 ? (delta > 0 ? -1 : 0) : current
    render(visible[(base + delta + visible.length) % visible.length])
  }

  function onClick(event) {
    const target = event.target
    const play = target.closest && target.closest('.gal-play')
    if (play) {
      event.preventDefault()
      open(play.closest('.gal-card'))
      return
    }
    if (target.closest && target.closest('#gal-modal-prev')) { step(-1); return }
    if (target.closest && target.closest('#gal-modal-next')) { step(1); return }
    if (target === modal || (target.closest && target.closest('#gal-modal-close'))) closeModal()
  }

  function onKeydown(event) {
    if (event.defaultPrevented || event.isComposing || event.ctrlKey || event.altKey || event.metaKey) return
    if (event.key === 'Escape') { closeModal(); return }
    if (!isOpen()) {
      const target = event.target
      const editing = target && (target.isContentEditable
        || (target.closest && target.closest('input, textarea, select, [role="textbox"]')))
      if (event.key === '/' && search && !editing) {
        event.preventDefault()
        search.focus()
      }
      return
    }
    if (event.key === 'Tab') {
      const focusable = Array.from(modal.querySelectorAll('button, a[href]'))
        .filter((node) => !node.disabled && node.getClientRects().length
          && window.getComputedStyle(node).visibility !== 'hidden')
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (focusable.indexOf(document.activeElement) < 0
        || (event.shiftKey && document.activeElement === first)
        || (!event.shiftKey && document.activeElement === last)) {
        event.preventDefault()
        ;(event.shiftKey ? last : first).focus()
      }
    }
    if (event.key === 'ArrowLeft') { event.preventDefault(); step(-1) }
    else if (event.key === 'ArrowRight') { event.preventDefault(); step(1) }
  }

  function onSearch() {
    state.query = search.value.trim().toLowerCase()
    apply()
  }

  function onChip(event) {
    state.chapter = event.currentTarget.dataset.ch
    apply()
  }

  function onRandom() {
    if (!visible.length) return
    const pick = visible[Math.floor(Math.random() * visible.length)]
    if (pick.scrollIntoView) pick.scrollIntoView({ block: 'center' })
    open(pick)
  }

  if (search) search.addEventListener('input', onSearch)
  for (const chip of chips) chip.addEventListener('click', onChip)
  if (randomBtn) randomBtn.addEventListener('click', onRandom)
  root.addEventListener('click', onClick)
  root.addEventListener('keydown', onKeydown)
  apply()

  return () => {
    if (search) search.removeEventListener('input', onSearch)
    for (const chip of chips) chip.removeEventListener('click', onChip)
    if (randomBtn) randomBtn.removeEventListener('click', onRandom)
    root.removeEventListener('click', onClick)
    root.removeEventListener('keydown', onKeydown)
    if (isOpen()) document.body.style.overflow = previousOverflow
  }
}
