<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { withBase } from 'vitepress'
import { countCompletedChecklistItems, readChecklistStore } from '../checklist'
import VoltageNotebook from './VoltageNotebook.vue'

const props = defineProps({ content: { type: Object, required: true } })
function pageLink(route) {
  const [page, anchor] = route.split('#')
  const target = page.endsWith('/') || page.endsWith('.html') ? page : `${page}.html`
  return withBase(`${target}${anchor ? `#${anchor}` : ''}`)
}

const ticks = ref({})
const refreshProgress = () => { ticks.value = readChecklistStore() }

onMounted(() => {
  refreshProgress()
  window.addEventListener('storage', refreshProgress)
  window.addEventListener('pageshow', refreshProgress)
})
onUnmounted(() => {
  window.removeEventListener('storage', refreshProgress)
  window.removeEventListener('pageshow', refreshProgress)
})

const cells = computed(() => props.content.pack.cells.map(cell => {
  const done = countCompletedChecklistItems(cell.items, ticks.value)
  return { ...cell, done, ratio: cell.total ? done / cell.total : 0 }
}))
const doneTotal = computed(() => cells.value.reduce((sum, cell) => sum + cell.done, 0))
const completedStages = computed(() => cells.value.filter(cell => cell.total > 0 && cell.done === cell.total).length)
const hasProgress = computed(() => doneTotal.value > 0)
const nextCell = computed(() => cells.value.find(cell => cell.total > 0 && cell.done < cell.total))

const questions = [
  { number: '01', title: '满电一拧把，为什么掉两格？', topic: '内阻与端电压', link: '/核心问题地图#2-满电一拧把掉两格电量真的瞬间消失了吗' },
  { number: '02', title: '保护为什么不能等到危险点？', topic: '误差与动作延时', link: '/stages/stage-2-主线-实测与验收' },
  { number: '03', title: '电流归零，就能查出 SOC 吗？', topic: '静置、极化与估算', link: '/stages/stage-4-主线-模型与校正' },
]

const resources = [
  { label: '查术语', details: '缩写、单位与中英文对照', link: '/glossary' },
  { label: '找公式', details: '参数、公式与适用条件', link: '/参数速查卡' },
  { label: '看电路', details: '功率、采样、均衡与安全', link: '/circuits/README' },
  { label: '备器材', details: '按阶段列出的预算清单', link: '/budget' },
]
</script>

<template>
<div class="workshop">
  <section class="workshop-hero" aria-labelledby="workshop-title">
    <div class="workshop-hero-copy">
      <p class="workshop-kicker">
        <span class="terminal-mark" aria-hidden="true">
        </span>电池管理系统 · 开源学习手册</p>
        <h1 id="workshop-title">弄懂一块电池，<br />再做一套 <span class="ink-underline">BMS</span>
      </h1>
      <p class="workshop-lead">从电芯、保护板，到状态估算与通信。用中文教程读原理，用动画看过程，再用代码和测量核对结果。</p>
      <div class="workshop-actions">
        <a class="workshop-button" :href="pageLink('/stages/getting-started')">零基础：从第 0 天开始 <span aria-hidden="true">→</span>
      </a>
      <a class="workshop-text-link" :href="pageLink('/stages/按目标选路线')">按目标选路线 <span aria-hidden="true">↗</span>
    </a>
    <a class="workshop-text-link" :href="pageLink('/核心问题地图')">查一个问题 <span aria-hidden="true">↘</span>
  </a>
  </div>
  <p class="workshop-availability">中文 · 免费开放 · 只用电脑也能动手</p>
  <div class="workshop-margin-note">
    <span aria-hidden="true">↳</span> 先试试右边的电流滑块，<br />看电压下降，再把负载撤掉。</div>
  </div>
  <VoltageNotebook />
</section>

<nav class="workshop-index" aria-label="学习资料">
  <a href="#stage-syllabus">
    <strong>07</strong>
    <span>阶段教程</span>
    <span aria-hidden="true">↗</span>
  </a>
  <a :href="pageLink('/reading')">
    <strong>32</strong>
    <span>章原创伴读书</span>
    <span aria-hidden="true">↗</span>
  </a>
  <a :href="pageLink('/circuits/README')">
    <strong :data-animation-count="content.animationCount">{{ content.animationCount }}</strong>
    <span>张动画与电路图</span>
    <span aria-hidden="true">↗</span>
  </a>
  <a :href="pageLink('/视频伴读路线')">
    <strong>08</strong>
    <span>集视频伴读</span>
    <span aria-hidden="true">↗</span>
  </a>
</nav>

<section id="learning-routes" class="workshop-section" aria-labelledby="routes-title">
  <div class="workshop-section-heading">
    <div>
      <p class="workshop-section-number">01 / 选一条路</p>
      <h2 id="routes-title">从你要做的事开始</h2>
    </div>
    <a class="workshop-text-link" :href="pageLink('/stages/按目标选路线')">查看全部六条路线 <span aria-hidden="true">↗</span>
  </a>
</div>
<div class="workshop-routes">
  <a v-for="(route, index) in content.goalRoutes" :key="route.id" class="workshop-route" :href="route.link">
    <div class="workshop-route-heading">
      <span class="workshop-route-number">0{{ index + 1 }}</span>
      <span class="workshop-route-time">{{ route.duration }}</span>
    </div>
    <h3>{{ route.title }}</h3>
    <p>{{ route.forWho }}</p>
    <dl>
      <div>
        <dt>先做</dt>
        <dd>{{ route.start }}</dd>
      </div>
      <div>
        <dt>完成时</dt>
        <dd>{{ route.output }}</dd>
      </div>
    </dl>
    <span class="workshop-route-footer">
      <span>{{ route.hardware }}</span>
      <span>进入路线 <span aria-hidden="true">→</span>
    </span>
  </span>
</a>
</div>
<p class="workshop-sidenote">做车辆项目，先读<a :href="pageLink('/车辆应用分流')">车辆应用分流</a>，再看<a :href="pageLink('/开源硬件剖析')">原理图与 PCB 案例</a>。车辆类别和安全要求需要单独确认。</p>
</section>

<section class="workshop-section workshop-questions" aria-labelledby="questions-title">
  <div class="workshop-question-intro">
    <p class="workshop-section-number">02 / 带着问题读</p>
    <h2 id="questions-title">先弄懂一个<br />想不通的地方</h2>
    <p>每个问题都有对应的讲解、图解和练习。先看解释，再算一次。</p>
    <a class="workshop-text-link" :href="pageLink('/核心问题地图')">全部十三个问题 <span aria-hidden="true">↗</span>
  </a>
</div>
<div class="workshop-question-list">
  <a v-for="question in questions" :key="question.number" :href="pageLink(question.link)">
    <span>{{ question.number }}</span>
    <div>
      <h3>{{ question.title }}</h3>
      <p>{{ question.topic }}</p>
    </div>
    <span aria-hidden="true">↗</span>
  </a>
</div>
</section>

<section id="stage-syllabus" class="workshop-section" aria-labelledby="syllabus-title">
  <div class="workshop-section-heading">
    <div>
      <p class="workshop-section-number">03 / 系统学习</p>
      <h2 id="syllabus-title">七个阶段，按顺序接起来</h2>
    </div>
    <p>主线分节阅读，完整讲义随时回查</p>
  </div>
  <div class="workshop-syllabus">
    <a v-for="stage in content.syllabus" :key="stage.number" :href="stage.link">
      <span class="syllabus-number">{{ stage.number }}</span>
      <h3>{{ stage.title }}</h3>
      <p>{{ stage.description }}</p>
      <span class="syllabus-duration">{{ stage.duration }}</span>
      <span aria-hidden="true">↗</span>
    </a>
  </div>
  <a class="workshop-postscript" :href="pageLink('/stages/stage-7-BMS与AI')">
    <span>选读 / 阶段 7</span>
    <strong>BMS × AI：怎么用，哪些判断要自己做</strong>
    <span aria-hidden="true">↗</span>
  </a>
</section>

<section class="workshop-section workshop-reading" aria-labelledby="reading-title">
  <div class="workshop-book" aria-hidden="true">
    <div class="workshop-book-spine">
    </div>
    <div class="workshop-book-cover">
      <span>BMS-Z · 原创伴读书</span>
      <strong>从一颗电芯<br />到一套证据链</strong>
      <svg viewBox="0 0 200 100" fill="none" stroke="currentColor" stroke-linecap="round">
        <path d="M20 50 L60 50 M60 23 L60 78 M70 35 L70 65 M70 50 L100 50 L110 35 L125 65 L140 35 L155 65 L165 50 L190 50" stroke-width="2" />
        <circle cx="20" cy="50" r="3" fill="currentColor" />
        <circle cx="190" cy="50" r="3" fill="currentColor" />
      </svg>
      <span>原理 · 算例 · 可运行实验<br />32 章 / 5 篇附录</span>
    </div>
  </div>
  <div class="workshop-reading-copy">
    <p class="workshop-section-number">04 / 想再读深一点</p>
    <h2 id="reading-title">把实验里遇到的事，<br />放回书里讲清楚</h2>
    <p>伴读书从一次带载掉压开始，接着讲采样、保护、模型、算法与工程验证。每章保留公式、图解和适用条件，也留一道读完能回答的问题。</p>
    <div class="workshop-actions">
      <a class="workshop-button" :href="pageLink('/book/00-前言')">开始读伴读书 <span aria-hidden="true">→</span>
    </a>
    <a class="workshop-text-link" :href="pageLink('/downloads/')">下载 PDF / HTML <span aria-hidden="true">↗</span>
  </a>
</div>
<p class="workshop-sidenote">已有教材？<a :href="pageLink('/reading')">按目标选择阅读章节</a>
</p>
</div>
</section>

<section class="workshop-section" aria-labelledby="practice-title">
  <div class="workshop-section-heading">
    <div>
      <p class="workshop-section-number">05 / 自己做一次</p>
      <h2 id="practice-title">打开电脑，就能开始的实验</h2>
    </div>
    <a class="workshop-text-link" :href="pageLink('/共学/README')">十一期共学 <span aria-hidden="true">↗</span>
  </a>
</div>
<div class="workshop-experiments">
  <a v-for="experiment in content.experiments" :key="experiment.number" :href="experiment.link">
    <span class="experiment-number">实验 {{ experiment.number }}</span>
    <h3>{{ experiment.title }}</h3>
    <p>{{ experiment.description }}</p>
    <span class="experiment-output">要看什么 <span>{{ experiment.output }}</span>
  </span>
  <span class="workshop-text-link">打开实验 <span aria-hidden="true">→</span>
</span>
</a>
</div>
<details class="workshop-ability">
  <summary>不确定该从哪一层开始？<span>查看能力地图</span>
</summary>
<div class="workshop-ability-grid">
  <a v-for="layer in content.learningLayers" :key="layer.number" :href="layer.link">
    <span>{{ layer.number }} / {{ layer.name }}</span>
    <strong>{{ layer.verb }}</strong>
    <p>{{ layer.summary }}</p>
    <p class="workshop-sidenote">核对：{{ layer.proof }}</p>
  </a>
</div>
<div class="workshop-practice-links">
  <a v-for="route in content.practiceRoutes" :key="route.tag" :href="route.link">{{ route.linkText }} <span aria-hidden="true">↗</span>
</a>
</div>
</details>
</section>

<section class="workshop-section workshop-progress" aria-labelledby="progress-title">
  <div class="workshop-progress-intro">
    <p class="workshop-section-number">06 / 留下学习记录</p>
    <h2 id="progress-title">下次来，接着学</h2>
    <p>阶段末尾的验收清单可以勾选。记录保存在当前浏览器，回来时从没完成的地方继续。</p>
    <div class="workshop-progress-total">
      <strong>{{ doneTotal }}<span> / {{ content.pack.total }}</span>
    </strong>
    <span>已勾条目 · {{ completedStages }} / {{ cells.length }} 份清单完成</span>
  </div>
  <a class="workshop-text-link" :href="nextCell?.link || content.pack.cells[0].link">{{ hasProgress ? '继续核对清单' : '打开第一份清单' }} <span aria-hidden="true">→</span>
</a>
<p class="workshop-sidenote">这里只记录七份清单的勾选情况，供学习回顾。</p>
</div>
<div class="workshop-checklists">
  <a v-for="cell in cells" :key="cell.page" :href="cell.link">
    <span class="checklist-stage">{{ cell.index }}</span>
    <span class="checklist-name">{{ cell.name }}</span>
    <span class="checklist-count">{{ cell.done }} / {{ cell.total }}</span>
    <span class="checklist-track" role="progressbar" :aria-label="`${cell.name}验收清单`" :aria-valuenow="cell.done" :aria-valuemax="cell.total" aria-valuemin="0">
      <span :style="{ width: `${cell.ratio * 100}%` }">
      </span>
    </span>
  </a>
</div>
</section>

<nav class="workshop-reference" aria-label="随手查阅">
  <a v-for="resource in resources" :key="resource.label" :href="pageLink(resource.link)">
    <span>{{ resource.label }} <span aria-hidden="true">↗</span>
  </span>
  <span>{{ resource.details }}</span>
</a>
</nav>
<p class="workshop-safety">实物实验前，先读<a :href="pageLink('/stages/stage-2-主线-实测与验收')">安全条件与测量方法</a>。本站阈值为教学示例，器件选型与实际设计应核对电芯和芯片手册。</p>
</div>
</template>
