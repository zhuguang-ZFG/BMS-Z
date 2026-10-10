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

## 七个阶段

<ol class="stage-list">
  <li v-for="s in data.stages" :key="s.link">
    <a :href="s.link">{{ s.text }}</a>
  </li>
</ol>

## 两个进阶实验

- [PC 综合实验](PC综合实验专题.md)：把采样、SOC、保护与通信接成可追踪的运行记录。
- [SOC 真实数据实验](SOC真实数据专题.md)：用 NASA 实测数据标定模型，在独立随机负载上解释误差。
