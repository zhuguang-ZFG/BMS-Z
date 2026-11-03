<script setup>
import { computed, ref } from 'vue'

const current = ref(20)
const resistance = 0.020
const openCircuitVoltage = 3.70
const drop = computed(() => Number(current.value) * resistance)
const terminalVoltage = computed(() => openCircuitVoltage - drop.value)
const curve = computed(() => `M 44 60 L 112 60 L 112 ${60 + drop.value * 100} L 278 ${60 + drop.value * 100} L 278 60 L 338 60`)
</script>

<template>
  <section class="voltage-notebook" :class="{ 'is-current-flowing': current > 0 }" aria-labelledby="notebook-title">
    <div class="notebook-heading">
      <span class="notebook-number">实验 01</span>
      <h2 id="notebook-title">一带负载，电压去哪了？</h2>
      <span class="notebook-unit">V / A</span>
    </div>

    <svg class="notebook-drawing" viewBox="0 0 480 252" role="img" aria-labelledby="cell-drawing-title cell-drawing-desc">
      <title id="cell-drawing-title">电芯与端电压测量示意</title>
      <desc id="cell-drawing-desc">放电电流经过等效内阻时产生压降。右侧电压表显示开路电压减去内阻压降后的端电压。</desc>
      <g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
        <path class="drawing-wash" d="M83 67 Q124 52 165 68 L164 211 Q124 232 84 211 Z" stroke="none" />
        <path d="M83 66 C84 48 165 48 166 66 L165 210 C162 229 85 229 83 210 Z" stroke-width="2" />
        <path d="M84 66 C88 84 163 84 166 66 M99 57 L99 47 Q124 38 150 47 L150 57" stroke-width="1.8" />
        <path d="M93 87 L94 202 M156 88 L155 203" stroke-width="1" opacity=".35" />
        <path d="M102 100 L101 188 M118 105 L119 193 M134 104 L133 194 M149 101 L148 188" stroke-width="1.3" opacity=".6" />
        <path d="M118 62 L132 62 M125 55 L125 69" stroke-width="1.5" />
        <path d="M124 42 L125 25 L420 25 L420 82 M420 174 L420 238 L125 238 L125 226 M291 25 L291 80 M291 190 L291 238" stroke-width="1.6" />
        <path d="M420 82 L420 94 L412 102 L428 114 L412 126 L428 138 L412 150 L420 158 L420 174" stroke-width="1.8" />
        <path class="drawing-current" d="M183 25 L230 25 M222 19 L230 25 L222 31" stroke-width="2" />
        <circle class="drawing-charge drawing-charge--outbound" cx="176" cy="25" r="2.6" stroke="none" />
        <circle class="drawing-charge drawing-charge--return" cx="232" cy="238" r="2.6" stroke="none" />
        <path d="M253 80 Q290 76 329 80 L330 188 Q292 193 253 189 Z" stroke-width="2" />
        <path class="drawing-screen" d="M263 94 L320 94 L320 151 L263 151 Z" stroke-width="1" />
        <circle cx="292" cy="173" r="7" stroke-width="1.3" />
        <path d="M292 166 L295 170" stroke-width="1.3" />
        <path d="M172 131 Q204 120 234 130 M227 125 L235 130 L227 135" stroke-width="1.2" />
      </g>
      <g class="drawing-labels" fill="currentColor">
        <text x="292" y="121" text-anchor="middle" class="drawing-voltage">{{ terminalVoltage.toFixed(2) }}</text>
        <text x="292" y="140" text-anchor="middle">V</text>
        <text x="202" y="16" text-anchor="middle">{{ current }} A</text>
        <text x="341" y="137">端电压</text>
        <text x="439" y="123">负载</text>
        <text x="16" y="151">电芯</text>
        <text x="16" y="170" class="drawing-note">R₀ = 20 mΩ</text>
      </g>
    </svg>

    <div class="notebook-control">
      <label for="load-current">拖一拖，改变放电电流</label>
      <output for="load-current">{{ current }} <span>A</span></output>
      <input id="load-current" v-model.number="current" type="range" min="0" max="30" step="1" :aria-valuetext="`${current} 安培，端电压 ${terminalVoltage.toFixed(2)} 伏`" />
      <div class="notebook-range"><span>0 A · 撤去负载</span><span>30 A</span></div>
    </div>

    <div class="notebook-result" aria-live="polite" aria-atomic="true">
      <span>端电压</span>
      <strong>{{ terminalVoltage.toFixed(2) }} <small>V</small></strong>
      <span class="notebook-equation">3.70 − {{ current }} × 0.020 = {{ terminalVoltage.toFixed(2) }}</span>
    </div>
    <svg class="notebook-plot" viewBox="0 0 380 140" role="img" aria-labelledby="plot-title">
      <title id="plot-title">接通负载时压降 {{ drop.toFixed(2) }} 伏，撤去负载后回到示例开路电压 3.70 伏</title>
      <path d="M44 24 L44 120 L350 120" fill="none" stroke="var(--bms-line)" />
      <path d="M44 60 L346 60" fill="none" stroke="var(--bms-line)" stroke-dasharray="3 5" />
      <path :d="curve" fill="none" stroke="var(--bms-accent)" stroke-width="2.5" stroke-linejoin="round" />
      <g fill="currentColor" font-size="11">
        <text x="36" y="64" text-anchor="end">3.70</text>
        <text x="113" y="137">接入负载</text>
        <text x="276" y="137">撤去负载</text>
        <text x="184" :y="48 + drop * 100" text-anchor="middle">压降 {{ drop.toFixed(2) }} V</text>
      </g>
    </svg>
    <p class="notebook-caption">仅示意瞬时欧姆压降，未计入极化、温度变化与容量消耗。电压下降不等于电量按比例减少。</p>
  </section>
</template>
