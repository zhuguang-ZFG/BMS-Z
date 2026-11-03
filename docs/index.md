---
layout: home
markdownStyles: false
pageClass: field-guide-home
search: false
description: BMS 电池管理系统开源学习手册。中文阶段教程、原创伴读书、动画与可运行实验，从电芯保护学到状态估算和通信。
---

<script setup>
import { data } from './index.data.ts'
import HomeWorkshop from './.vitepress/theme/HomeWorkshop.vue'
</script>

<HomeWorkshop :content="data" />
