---
layout: home

hero:
  name: BMS-Z
  text: 电池管理系统自学路线
  tagline: 从入门到工程实践的中文原创教程——七篇阶段正文、150 张动画电路图，以及 PC 可跑的配套实验。
  actions:
    - theme: brand
      text: 从这里开始
      link: /stages/getting-started
    - theme: alt
      text: 150 张动画电路图
      link: /circuits/README
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

## 七个阶段

<ol class="stage-list">
  <li v-for="s in data.stages" :key="s.link">
    <a :href="s.link">{{ s.text }}</a>
  </li>
</ol>

## 两个进阶实验

- [PC 综合实验](PC综合实验专题.md)：把采样、SOC、保护与通信接成可追踪的运行记录。
- [SOC 真实数据实验](SOC真实数据专题.md)：用 NASA 实测数据标定模型，在独立随机负载上解释误差。
