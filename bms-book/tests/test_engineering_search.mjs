/**
 * 搜索的行为测试：只碰消费者能看到的东西——小节怎么切、中文句中词能不能命中、
 * 答案文字有没有进索引，以及无结果是不是干净地返回 0。
 *
 * 这里不测浏览器挂载（没有 DOM 依赖）：用最小的节点树喂 collectSections，
 * 真实浏览器里的输入/清空/层级显露由装配侧在产物上验证。
 */

import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildSearchIndex,
  collectSections,
  searchSections,
  snippetFor,
} from '../engineering/search-client.js'

function text(value) {
  return { nodeType: 3, nodeValue: value, firstChild: null, nextSibling: null }
}

function element(tag, props = {}, nodes = []) {
  const el = {
    nodeType: 1,
    tagName: tag.toUpperCase(),
    id: props.id || '',
    hidden: Boolean(props.hidden),
    open: Boolean(props.open),
    children: [],
    firstChild: null,
    nextSibling: null,
    classList: {
      contains(name) {
        return (props.classes || []).includes(name)
      },
    },
    getAttribute(name) {
      if (name === 'aria-hidden') {
        return props.ariaHidden === undefined ? null : String(props.ariaHidden)
      }
      return null
    },
  }
  let previous = null
  for (const node of nodes) {
    if (node.nodeType === 1) el.children.push(node)
    if (previous) previous.nextSibling = node
    else el.firstChild = node
    previous = node
  }
  return el
}

function chapterFixture() {
  const answer = element('details', {}, [
    element('summary', {}, [text('核对答案')]),
    element('p', {}, [text('冻住的旧值会一直顶在量程边缘。')]),
  ])
  const chapter = element('section', { id: 's1--toc', classes: ['book-chapter'] }, [
    element('h1', {}, [text('S1 精度够了保护为什么反而慢了')]),
    element('aside', { classes: ['chapter-route'] }, [
      element('p', {}, [text('先读误差源。')]),
    ]),
    element('h2', { id: 's1--a' }, [
      text('1.1 采样窗口'),
      element('a', { classes: ['header-anchor'], ariaHidden: true }, [text('\u200b')]),
    ]),
    element('p', {}, [text('母线电压已经起来了，预充时序还差四样证据。')]),
    answer,
    element('script', {}, [text('脚本噪声不该进索引')]),
    element('mjx-container', {}, [text('数学排版副本')]),
    element('nav', {}, [text('导航噪声')]),
    element('h2', {}, [text('1.2 没有 id 的小节')]),
    element('p', {}, [text('第二小节正文。')]),
    element('div', { classes: ['book-search'] }, [text('搜索界面不该进索引')]),
  ])
  return { main: element('main', {}, [chapter]), answer }
}

test('collectSections splits on h2, keeps answers closed and drops page chrome', () => {
  const { main, answer } = chapterFixture()
  const sections = collectSections(main)

  assert.deepEqual(
    sections.map((section) => section.url),
    ['#s1--toc', '#s1--a', '#s1--toc'],
    'h2 用自身 id；没有 id 时退回章节 id',
  )
  assert.equal(sections[0].title, 'S1 精度够了保护为什么反而慢了')
  assert.match(sections[0].text, /先读误差源/)

  assert.equal(sections[1].title, '1.1 采样窗口', '标题锚点与零宽字符不进标题')
  assert.match(sections[1].text, /母线电压已经起来了/)
  assert.match(sections[1].text, /冻住的旧值/, '折叠答案必须进索引')
  assert.doesNotMatch(
    sections[1].text,
    /脚本噪声|数学排版副本|导航噪声|搜索界面|先读误差源/,
    '脚本、MathJax、目录与搜索 UI 不是正文',
  )
  assert.equal(answer.open, false, '建索引不能顺手展开 details')

  assert.equal(sections[2].title, '1.2 没有 id 的小节')
  assert.equal(sections[2].text, '第二小节正文。')
})

test('Chinese sentence fragments hit the section that owns the anchor', () => {
  const { main } = chapterFixture()
  const sections = collectSections(main)
  const index = buildSearchIndex(sections)

  const sentence = searchSections(index, sections, '母线起来')
  assert.ok(
    sentence.hits.some((hit) => hit.section.url === '#s1--a'),
    '句中二元组必须命中「母线电压已经起来了」所在小节',
  )

  const answer = searchSections(index, sections, '冻住')
  assert.ok(
    answer.hits.some((hit) => hit.section.url === '#s1--a'),
    '只出现在封闭 details 里的词同样可搜',
  )
  assert.match(snippetFor(sections[1].text, '冻住'), /冻住/)
})

test('empty and unmatched queries stay quiet', () => {
  const { main } = chapterFixture()
  const sections = collectSections(main)
  const index = buildSearchIndex(sections)

  assert.equal(searchSections(index, sections, '量子纠缠').total, 0)
  assert.deepEqual(searchSections(index, sections, '   ').hits, [])
})

