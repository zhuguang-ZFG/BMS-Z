---
layout: home

hero:
  name: BMS-Z
  text: 从一个问题，走到一份工程证据
  tagline: 不从资料海开始。先选目标或核心问题，再沿着阶段教程、伴读书、154 张动画、视频和 PC 实验走到可复算结果。
  actions:
    - theme: brand
      text: 30 分钟开始
      link: /stages/getting-started
    - theme: alt
      text: 按目标选路线
      link: /stages/按目标选路线
    - theme: alt
      text: 从核心问题进入
      link: /核心问题地图

features:
  - title: 四条目标路线
    details: 零基础、保护板与硬件、SOC/SOH 算法、产品级工程。每条路线都写清时间、前置和交付物。
    link: /stages/按目标选路线
  - title: 十三个核心问题
    details: 从“满电为何掉两格”到“SOP 为什么取最小”，每题同时接上书、动画、视频与实验。
    link: /核心问题地图
  - title: 深读与动画
    details: 32 章原创伴读书和 154 张动画保留完整深度，但不再要求第一次从头扫完。
    link: /reading
  - title: 用证据过关
    details: PC 实验、共学、挑战和阶段清单都要求留下可运行、可解释、可复算的结果。
    link: /共学/README.html
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

## 先选目标，不从资源海里游

<section class="goal-route-grid" aria-label="四条任务导向学习路线">
  <a v-for="route in data.goalRoutes" :key="route.id" class="goal-route" :href="route.link">
    <span class="goal-route__meta">{{ route.duration }} · {{ route.hardware }}</span>
    <strong>{{ route.title }}</strong>
    <span class="goal-route__for">适合：{{ route.forWho }}</span>
    <span class="goal-route__start"><b>先做</b>{{ route.start }}</span>
    <span class="goal-route__proof"><b>交付</b>{{ route.output }}</span>
    <span class="goal-route__link">进入路线 <span aria-hidden="true">→</span></span>
  </a>
</section>

还不知道目标，就从[十三个核心问题](核心问题地图.md)里挑一个最想解决的；完全零基础，直接做[第 0 天小实验](stages/getting-started.md#第-0-天30-分钟小胜利零器材也能做一半)。

要做道路车辆，先选[电动自行车／电动摩托车／电动汽车三条应用路线](车辆应用分流.md)，再进入[固定版本的开源原理图与 PCB 剖析](开源硬件剖析.md)；不要按“48 V、72 V、400 V”直接猜车辆类别。

## 全程先看一张图

![BMS 学习路线总览：七个阶段从入门到产品级](circuits/assets/bms-roadmap.svg)

每一站都有对应的阶段正文，过关标准写在每篇末尾；全库 154 张动画负责把电流、热、数据与状态变化画出来——先看清全程，再决定从哪一站进场。
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

## 三个进阶实验

- [PC 综合实验](PC综合实验专题.md)：把采样、SOC、保护与通信接成可追踪的运行记录。
- [SOC 真实数据实验](SOC真实数据专题.md)：用 NASA 实测数据标定模型，在独立随机负载上解释误差。
- [扩散与常相位实验](扩散与常相位专题.md)：把活性颗粒当球算一遍扩散，看一阶 RC 差多少、奈奎斯特尾巴的斜率是谁的读数。
