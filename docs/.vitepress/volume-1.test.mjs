import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import test from 'node:test'

import {
  animationIndex, galleryPage, landingPage, volumeOne, volumeOneAssets,
} from './volume-1-sources.mjs'
import {
  generatedAssetsDir, generatedCalcFile, generatedDir, prepareVolumeOne,
} from './prepare-volume-1.mjs'

const prepared = prepareVolumeOne()
const generated = (file) => readFileSync(path.join(generatedDir, file), 'utf8')

test('卷一共 63 个内容页，顺序表与书稿目录一致', () => {
  assert.equal(volumeOne.pages.filter((page) => page.file !== galleryPage.file).length, 63)
  assert.equal(volumeOne.pages.find((page) => page.file === 'p5-00-part5.md').title, '第五篇：动画演示中心')
  for (const file of ['p0-07-toc.md', 'p1-00-part1.md', 'p5-00-part5.md', 'p9-00-quiz.md']) {
    assert.ok(volumeOne.pages.some((page) => page.file === file), `缺少 ${file}`)
  }
  assert.ok(!volumeOne.pages.some((page) => page.file === 'index.md'))
  assert.equal(new Set(volumeOne.pages.map((page) => page.file)).size, volumeOne.pages.length)
})

test('每个页面只有一个 h1，且不再残留 MkDocs 专用标记', () => {
  for (const page of volumeOne.pages) {
    if (page.file === galleryPage.file) continue
    const content = generated(page.file)
    // 先剥掉围栏代码块：「跟做实验」脚本里的 `# 11.7 …` 是 Python 注释不是标题
    const prose = content.replace(/^```[\s\S]*?^```/gm, '')
    assert.equal((prose.match(/^# /gm) || []).length, 1, `${page.file} h1 数量`)
    assert.ok(!/<[^>]+\smarkdown="1"/.test(content), `${page.file} 残留 markdown="1"`)
    assert.ok(!content.includes('<!-- slot:'), `${page.file} 残留 slot 注释`)
  }
})

test('跨页链接落在站内 .html，资源引用全部有文件', () => {
  const files = [landingPage.file, galleryPage.file, ...volumeOne.pages.map((page) => page.file)]
  for (const file of new Set(files)) {
    const content = generated(file)
    assert.ok(!/\]\((?!https?:)[^)]*\.md[^)]*\)/.test(content.replace(/\]\(\.\.\/reading\.md\)/g, '')), `${file} 残留 .md 链接`)
    assert.ok(!/href="[^"]*\.md[^"]*"/.test(content), `${file} 残留 raw .md href`)
    for (const match of content.matchAll(/(?:\.\.)?\/volume-1-assets\/([^"#?)\s]+)/g)) {
      assert.ok(existsSync(path.join(generatedAssetsDir, decodeURIComponent(match[1]))), `${file} 缺资源 ${match[1]}`)
    }
  }
})

test('正文 img 标签可被 Vue 模板编译（alt 内不留裸引号和尖括号）', () => {
  const files = [landingPage.file, galleryPage.file, ...volumeOne.pages.map((page) => page.file)]
  for (const file of new Set(files)) {
    const content = generated(file)
    for (const match of content.matchAll(/<img\b([^>]*src="(?:\/|\.\.\/)volume-1-assets[^>]*)>/g)) {
      const attributes = match[1]
      assert.equal((attributes.match(/"/g) || []).length % 2, 0, `${file} img 引号不成对：${attributes.slice(0, 80)}`)
      assert.ok(!attributes.includes('<'), `${file} img 属性含裸尖括号：${attributes.slice(0, 80)}`)
    }
  }
})

test('动画图都有减弱动效静止版，路线图只替换一次', () => {
  for (const page of volumeOne.pages) {
    if (page.file === galleryPage.file) continue
    const content = generated(page.file)
    for (const match of content.matchAll(/<source srcset="(?:\.\.)?\/volume-1-assets\/(svg\/[^"]+\.reduce\.svg)"/g)) {
      assert.ok(existsSync(path.join(generatedAssetsDir, match[1])), `缺静止版 ${match[1]}`)
    }
  }
  const roadmap = generated('p0-06-roadmap.md')
  assert.equal((roadmap.match(/v1-roadmap/g) || []).length, 1)
  assert.ok(existsSync(path.join(generatedAssetsDir, 'static', 'roadmap.svg')))
})

test('11 只计算器全部来自正文，默认输出与算一笔对齐', async () => {
  const { CALCS } = await import(`./volume-1-generated/calc.js?${Date.now()}`)
  assert.equal(Object.keys(CALCS).length, 11)
  const defaults = (key) => {
    const values = {}
    for (const input of CALCS[key].inputs) values[input.key] = input.value
    return values
  }
  const divider = CALCS.divider.compute(defaults('divider')).map((row) => row.value)
  assert.deepEqual(divider, ['5.00', '3.33', '33.3'])
  const electrolyte = CALCS.electrolyte.compute(defaults('electrolyte')).map((row) => row.value)
  assert.deepEqual(electrolyte, ['32000', '3.7'])
  const hysteresis = CALCS.hysteresis.compute(defaults('hysteresis')).map((row) => row.value)
  assert.ok(Math.abs(Number(hysteresis[0]) - 2.515) <= 0.011)
  assert.ok(Math.abs(Number(hysteresis[1]) - 2.415) <= 0.011)
  assert.equal(hysteresis[2], '0.100')
  const probe = CALCS.probe.compute(defaults('probe')).map((row) => row.value)
  assert.deepEqual(probe, ['0.909', '9.1', '15.9'])
  const buck = CALCS.buck.compute(defaults('buck')).map((row) => row.value)
  assert.deepEqual(buck, ['0.417', '0.884', '7.4'])
  const noise = CALCS.noise.compute(defaults('noise')).map((row) => row.value)
  assert.deepEqual(noise, ['4.1', '4.07'])
  const loop = CALCS.loop.compute(defaults('loop')).map((row) => row.value)
  assert.deepEqual(loop, ['100.0', '40.0', '60', '稳'])

  const containers = [...volumeOne.pages.filter((page) => page.file !== galleryPage.file)]
    .map((page) => generated(page.file))
    .join('\n')
    .match(/<div class="calc" data-calc="[a-z]+"><\/div>/g) || []
  assert.equal(containers.length, 11)
})

test('画廊收齐动画索引，卡片与筛选都写进页面', () => {
  const items = animationIndex()
  assert.equal(items.length, 153)
  const gallery = generated(galleryPage.file)
  assert.equal((gallery.match(/class="gal-card"/g) || []).length, 153)
  assert.ok(gallery.includes('data-ch="all"'))
  for (const item of items) {
    assert.ok(gallery.includes(`./p5-00-part5.html#${item.anchor}`), `缺动画 ${item.anchor}`)
    const relative = item.static_svg.replace(/^assets\//, '')
    assert.ok(existsSync(path.join(volumeOneAssets, relative)), `缺原图 ${item.static_svg}`)
  }
  assert.ok(existsSync(generatedCalcFile))
  assert.equal(prepared.pages, 65)
})

test('多属性图片的 alt 不被吞，模态图有真实占位', () => {
  // 回归 2026-11-12：repairImageAttributes 扫描不止于首个候选收尾引号，
  // 会把 width/height 等后续属性整段吞进 alt 再转义成 &quot;，
  // check_pages 因此对路线图页报「宽高」缺失。
  const roadmap = generated('p0-06-roadmap.md')
  const figure = roadmap.match(/<figure class="v1-roadmap"><img ([^>]*)>/)
  assert.ok(figure, '路线图 figure 缺失')
  assert.ok(figure[1].includes('alt="六阶段学习路线与方向深化"'), `alt 被污染：${figure[1].slice(0, 120)}`)
  assert.ok(figure[1].includes('width="560"'), `缺真实 width：${figure[1].slice(0, 120)}`)
  assert.ok(figure[1].includes('height="940"'), `缺真实 height：${figure[1].slice(0, 120)}`)
  assert.ok(figure[1].includes('loading="lazy"'), '路线图缺懒加载')

  const gallery = generated(galleryPage.file)
  const modal = gallery.match(/<img id="gal-modal-img" ([^>]*)>/)
  assert.ok(modal, '模态图缺失')
  assert.ok(/\bsrc="\/volume-1-assets\/[^"]+"/.test(modal[1]), `模态图缺占位 src：${modal[1]}`)
  assert.ok(/\bwidth="\d+"/.test(modal[1]) && /\bheight="\d+"/.test(modal[1]), `模态图缺宽高：${modal[1]}`)
  assert.ok(modal[1].includes('loading="lazy"'), '模态图缺懒加载')
})
