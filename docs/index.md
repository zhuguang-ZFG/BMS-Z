---
layout: home

hero:
  name: BMS-Z
  text: 电池管理系统自学路线
  tagline: 从入门到工程实践的中文原创教程——七篇阶段正文、十一期共学打卡、150 张动画电路图，以及 PC 可跑的配套实验。
  actions:
    - theme: brand
      text: 从这里开始
      link: /stages/getting-started
    - theme: alt
      text: 150 张动画电路图
      link: /circuits/README
    - theme: alt
      text: 共学快闪十一期
      link: /共学/README.html
    - theme: alt
      text: 一页导航总图
      link: /BMS%E5%AD%A6%E4%B9%A0%E8%B7%AF%E5%BE%84.html

features:
  - title: 七篇阶段教程
    details: 前置知识 → 认识 BMS → 保护板实践 → AFE+MCU 智能方案 → SOC/SOH 算法 → 通信与集成 → 毕业项目，每篇都有可勾选的过关标准。
  - title: 150 张 SMIL 动画电路图
    details: 功率回路、采样链、充电均衡计量、系统安全与量产、电路板绘制五个板块，逐个电路看清电流怎么走；画风统一，双击就能在浏览器里播放。
  - title: 代码 PC 可跑
    details: 在 PC 上完成 SOC、协议和固件核心实验，再通过综合案例把模块连接起来；硬件调试与实物验收需要相应设备。
---

<script setup>
import { data } from './index.data.ts'
import { readChecklistStore } from './.vitepress/checklist'
import { computed, onMounted, ref } from 'vue'

// 服务端没有 localStorage，初值就取空态：SSR 渲出的骨架与客户端挂载前的第一帧逐字节
// 相同，才不会报 hydration 告警。真数据在 onMounted 之后才进来。
const ticks = ref({})
onMounted(() => {
  ticks.value = readChecklistStore()
})

const cells = computed(() =>
  data.pack.cells.map((cell) => {
    const page = ticks.value[cell.page]
    const done = page ? cell.keys.filter((key) => page[key]).length : 0
    return {
      ...cell,
      done,
      ratio: cell.total === 0 ? 0 : done / cell.total,
      sampled: done > 0,
    }
  })
)

const sampled = computed(() => cells.value.filter((cell) => cell.sampled))

// 木桶读数：串联认最小。一格都没采到样就没有可信 SOC——宁缺毋滥，
// 也不能让 Math.min() 的空集把 -Infinity 抬上首页。
const soc = computed(() =>
  sampled.value.length === 0 ? null : Math.min(...sampled.value.map((cell) => cell.ratio))
)

// 平均是另一种算法，这里明确标成安慰值：它会把最弱那一格藏起来。
const average = computed(() =>
  sampled.value.length === 0
    ? null
    : sampled.value.reduce((sum, cell) => sum + cell.ratio, 0) / sampled.value.length
)

// 最弱单体常常不止一格（两格同为 50% 太常见了）。只报第一个就是把并列说成独占。
const weakestNames = computed(() => {
  if (soc.value === null) return '尚无采样'
  const tied = sampled.value.filter((cell) => cell.ratio === soc.value).map((cell) => cell.name)
  if (tied.length <= 2) return tied.join('、')
  return `${tied.slice(0, 2).join('、')} 等 ${tied.length} 格`
})

const doneTotal = computed(() => cells.value.reduce((sum, cell) => sum + cell.done, 0))

function percent(ratio) {
  return `${Math.round(ratio * 100)}%`
}
</script>

## 全程先看一张图

![BMS 学习路线总览：七个阶段从入门到产品级](circuits/assets/bms-roadmap.svg)

每一站都有对应的阶段正文，过关标准写在每篇末尾——先看清全程，再决定从哪一站进场。
<section class="learning-cockpit" aria-labelledby="learning-cockpit-title">
  <div class="learning-cockpit__intro">
    <p class="learning-cockpit__eyebrow">把“看过”变成“会做”</p>
    <h2 id="learning-cockpit-title">先定位能力，再留下证据</h2>
    <p>不用把七个阶段从头刷一遍。先选自己所在的认知层，完成一个有输出的入口，再沿着证据链向上走：会叫名、会解释、会运行、会诊断、会取舍，最后交付别人能复现的作品。</p>
  </div>

  <div class="learning-ladder" role="list" aria-label="六层能力地图">
    <div v-for="layer in data.learningLayers" :key="layer.number" role="listitem">
      <a class="learning-step" :href="layer.link">
        <span class="learning-step__number" aria-hidden="true">{{ layer.number }}</span>
        <span class="learning-step__content">
          <span class="learning-step__heading">
            <strong>{{ layer.name }}</strong>
            <span>{{ layer.verb }}</span>
          </span>
          <span class="learning-step__summary">{{ layer.summary }}</span>
          <span class="learning-step__proof"><b>验收</b>{{ layer.proof }}</span>
        </span>
        <span class="learning-step__arrow" aria-hidden="true">↗</span>
      </a>
    </div>
  </div>

  <div class="practice-rail" aria-label="从定位到交付的实践闭环">
    <a v-for="route in data.practiceRoutes" :key="route.tag" class="practice-card" :href="route.link">
      <span class="practice-card__tag">{{ route.tag }}</span>
      <strong>{{ route.title }}</strong>
      <span>{{ route.details }}</span>
      <span class="practice-card__link">{{ route.linkText }} <span aria-hidden="true">→</span></span>
    </a>
  </div>
</section>

## 验收电池组

<section class="pack-monitor" aria-labelledby="pack-monitor-title">
  <div class="pack-monitor__intro">
    <p class="pack-monitor__eyebrow">读数存在这台浏览器</p>
    <h2 id="pack-monitor-title">包的容量由最弱那一节决定</h2>
    <p>七篇末尾的验收清单，勾上就记住。每一格按自己的完成度充电，但包的读数取<b>最弱单体</b>：串联认最小。平均是安慰，不是容量——它恰好能把漏检的那一节藏得干干净净。</p>
  </div>

  <div class="pack-readout">
    <div class="pack-stat">
      <span class="pack-stat__label">包 SOC</span>
      <strong class="pack-stat__value">{{ soc === null ? '未测量' : percent(soc) }}</strong>
    </div>
    <div class="pack-stat">
      <span class="pack-stat__label">最弱单体</span>
      <strong class="pack-stat__value">{{ weakestNames }}</strong>
    </div>
    <div class="pack-stat">
      <span class="pack-stat__label">平均（安慰值）</span>
      <strong class="pack-stat__value">{{ average === null ? '—' : percent(average) }}</strong>
    </div>
    <div class="pack-stat">
      <span class="pack-stat__label">已勾</span>
      <strong class="pack-stat__value">{{ doneTotal }} / {{ data.pack.total }}</strong>
    </div>
  </div>

  <div class="pack-cells" role="list" aria-label="七篇验收清单的完成度">
    <span
      v-if="soc !== null"
      class="pack-threshold"
      :style="{ top: 'calc(var(--cell-track) * ' + (1 - soc).toFixed(3) + ')' }"
      aria-hidden="true"
    ></span>
    <div v-for="cell in cells" :key="cell.page" role="listitem">
      <a
        class="pack-cell"
        :class="{ 'is-unsampled': !cell.sampled, 'is-weakest': soc !== null && cell.ratio === soc }"
        :href="cell.link"
      >
        <span class="pack-cell__level">
          <span class="pack-cell__fill" :style="{ height: (cell.ratio * 100).toFixed(1) + '%' }"></span>
          <span v-if="!cell.sampled" class="pack-cell__float">未采样</span>
        </span>
        <span class="pack-cell__meta">
          <span class="pack-cell__index">{{ cell.index }}</span>
          <span class="pack-cell__name">{{ cell.name }}</span>
          <span class="pack-cell__count">{{ cell.done }} / {{ cell.total }}</span>
        </span>
      </a>
    </div>
  </div>

  <p class="pack-monitor__foot">
    <template v-if="soc === null">
      一块电芯都还没采到样，所以没有可信读数。从
      <a :href="data.pack.cells[0].link">{{ data.pack.cells[0].name }}</a>
      的清单勾第一条开始。
    </template>
    <template v-else>这块包只量七篇验收的 {{ data.pack.total }} 条。入门与电路板绘制另有自检，各算各的，不进这块包。</template>
  </p>
</section>

## 七个阶段

<ol class="stage-list">
  <li v-for="s in data.stages" :key="s.link">
    <a :href="s.link">{{ s.text }}</a>
  </li>
</ol>

## 两个进阶实验

- [PC 综合实验](PC综合实验专题.md)：把采样、SOC、保护与通信接成可追踪的运行记录。
- [SOC 真实数据实验](SOC真实数据专题.md)：用 NASA 实测数据标定模型，在独立随机负载上解释误差。
