/*  就地算：正文算例旁的可调参数小计算器。
 *
 * docs/ 里只放一个空容器 `<div class="calc" data-calc="型号"></div>`，
 * 这里在客户端把输入项和结果行画出来。铁律：**每个型号的默认值 = 正文里
 * 那笔算例的原数**，输出口径与正文一致——读者改参数前后，书上的数永远
 * 能对上（test_calcs.py 用正文算例的数逐项回归）。
 * JavaScript 关掉时容器是空的，无害：紧挨着的那条  算一笔就是兜底算例。
 */
(function () {
  'use strict';

  function fmt(v, d) {
    if (!isFinite(v)) return '—';
    var m = Math.pow(10, d);
    return (Math.round(v * m) / m).toFixed(d);
  }

  var CALCS = {
    divider: {
      name: '分压器带载',
      note: '带载 = 给 R2 并联一只 RL：先算 R2∥RL，再代回分压式。空载公式只在空载成立。',
      inputs: [
        { key: 'vin', label: '输入电压', unit: 'V', value: 10, step: 0.5, min: 0 },
        { key: 'r1', label: 'R1', unit: 'kΩ', value: 10, step: 1, min: 0.1 },
        { key: 'r2', label: 'R2', unit: 'kΩ', value: 10, step: 1, min: 0.1 },
        { key: 'rl', label: '负载 RL', unit: 'kΩ', value: 10, step: 1, min: 0.1 }
      ],
      compute: function (x) {
        var vz = x.vin * x.r2 / (x.r1 + x.r2);
        var r2p = (x.r2 * x.rl) / (x.r2 + x.rl);
        var vl = x.vin * r2p / (x.r1 + r2p);
        var sag = vz > 0 ? (1 - vl / vz) * 100 : 0;
        return [
          { label: '空载输出', value: fmt(vz, 2), unit: 'V' },
          { label: '带载输出', value: fmt(vl, 2), unit: 'V' },
          { label: '塌陷', value: fmt(sag, 1), unit: '%' }
        ];
      },
      presets: [
        { label: '空载', set: { rl: 9999 } },
        { label: 'RL = 10 kΩ', set: { rl: 10 } },
        { label: 'RL = 1 kΩ', set: { rl: 1 } }
      ]
    },
    electrolyte: {
      name: '电解电容寿命',
      note: '10℃ 翻倍法则：环境每比额定低 10℃，寿命翻一倍（阿伦尼乌斯的粗口径，纹波发热另算）。',
      inputs: [
        { key: 'hours', label: '额定寿命', unit: 'h', value: 2000, step: 500, min: 100 },
        { key: 't0', label: '额定温度', unit: '℃', value: 105, step: 5, min: 25 },
        { key: 'ta', label: '工作温度', unit: '℃', value: 65, step: 5, min: 0 }
      ],
      compute: function (x) {
        var life = x.hours * Math.pow(2, (x.t0 - x.ta) / 10);
        return [
          { label: '预期寿命', value: fmt(life, 0), unit: 'h' },
          { label: '约合', value: fmt(life / 8760, 1), unit: '年（连续通电）' }
        ];
      }
    },
    hysteresis: {
      name: '迟滞窗口',
      note: '开集电极比较器的双阈值：VTH± = VREF(1+R1/R2) − (R1/R2)·VOL/OH，窗口 = (R1/R2)(VOH−VOL)。',
      inputs: [
        { key: 'vref', label: '基准 VREF', unit: 'V', value: 2.5, step: 0.1, min: 0 },
        { key: 'r1', label: 'R1', unit: 'kΩ', value: 1, step: 0.5, min: 0.1 },
        { key: 'r2', label: 'R2', unit: 'kΩ', value: 100, step: 10, min: 0.1 },
        { key: 'voh', label: 'VOH', unit: 'V', value: 10, step: 1, min: 0 },
        { key: 'vol', label: 'VOL', unit: 'V', value: 0, step: 0.1, min: 0 }
      ],
      compute: function (x) {
        var k = x.r1 / x.r2;
        var vthp = x.vref * (1 + k) - k * x.vol;
        var vthm = x.vref * (1 + k) - k * x.voh;
        return [
          { label: '上门槛 VTH+', value: fmt(vthp, 3), unit: 'V' },
          { label: '下门槛 VTH−', value: fmt(vthm, 3), unit: 'V' },
          { label: '窗口 ΔV', value: fmt(vthp - vthm, 3), unit: 'V' }
        ];
      }
    },
    probe: {
      name: '探头负载',
      note: '×1 = 1MΩ∥100pF，×10 = 10MΩ∥10pF：源阻越大被分走越多，带宽被 RC 拖垮。',
      inputs: [
        { key: 'rs', label: '源阻抗', unit: 'kΩ', value: 100, step: 10, min: 0.1 },
        { key: 'mode', label: '探头档位', type: 'select', value: 'x1',
          options: [['x1', '×1 档'], ['x10', '×10 档']] }
      ],
      compute: function (x) {
        var zin = x.mode === 'x10' ? 10e6 : 1e6;
        var cap = x.mode === 'x10' ? 10e-12 : 100e-12;
        var rs = x.rs * 1e3;
        var ratio = zin / (zin + rs);
        var fc = 1 / (2 * Math.PI * rs * cap);
        return [
          { label: '分压系数', value: fmt(ratio, 3), unit: '' },
          { label: '幅度误差', value: fmt((1 - ratio) * 100, 1), unit: '%' },
          { label: '带宽截止', value: fmt(fc / 1e3, 1), unit: 'kHz' }
        ];
      }
    },
    opamp: {
      name: '运放选型双判据',
      note: '小信号看 GBW：闭环带宽 ≈ GBW ÷ 增益，选型留 10 倍（GBW ≥ 增益×f×10）；大信号看 SR：满功率带宽 = SR/(2π·Vp)，不够正弦变三角。',
      inputs: [
        { key: 'av', label: '闭环增益', unit: 'V/V', value: 100, step: 10, min: 1 },
        { key: 'f', label: '信号频率', unit: 'kHz', value: 10, step: 1, min: 0.1 },
        { key: 'vpp', label: '输出峰峰值', unit: 'V', value: 10, step: 1, min: 0.1 },
        { key: 'gbw', label: 'GBW', unit: 'MHz', value: 0.7, step: 0.1, min: 0.01 },
        { key: 'sr', label: '压摆率', unit: 'V/µs', value: 0.5, step: 0.1, min: 0.01 }
      ],
      compute: function (x) {
        var fb = (x.gbw * 1e6) / x.av;
        var need = x.av * (x.f * 1e3) * 10;
        var vp = x.vpp / 2;
        var fp = (x.sr * 1e6) / (2 * Math.PI * vp);
        return [
          { label: '闭环带宽', value: fmt(fb / 1e3, 1), unit: 'kHz' },
          { label: 'GBW 需 ≥', value: fmt(need / 1e6, 1), unit: 'MHz' },
          { label: '满功率带宽', value: fmt(fp / 1e3, 1), unit: 'kHz' }
        ];
      }
    },
    buck: {
      name: 'Buck 占空比与纹波',
      note: '伏秒平衡给 D = Vout/Vin；电感纹波 ΔIL = (Vin−Vout)·D/(L·fsw)；输出纹波 ΔV = ΔIL/(8·fsw·C)（容性项，ESR 另算）。',
      inputs: [
        { key: 'vin', label: '输入电压', unit: 'V', value: 12, step: 1, min: 0.5 },
        { key: 'vout', label: '输出电压', unit: 'V', value: 5, step: 0.5, min: 0.5 },
        { key: 'fsw', label: '开关频率', unit: 'kHz', value: 150, step: 10, min: 1 },
        { key: 'l', label: '电感量', unit: 'µH', value: 22, step: 1, min: 0.1 },
        { key: 'c', label: '输出电容', unit: 'µF', value: 100, step: 10, min: 0.1 }
      ],
      compute: function (x) {
        var d = x.vout / x.vin;
        var dIl = (x.vin - x.vout) * d / ((x.l * 1e-6) * (x.fsw * 1e3));
        var dv = dIl / (8 * (x.fsw * 1e3) * (x.c * 1e-6));
        return [
          { label: '占空比 D', value: fmt(d, 3), unit: '' },
          { label: '电感纹波 ΔIL', value: fmt(dIl, 3), unit: 'A' },
          { label: '输出纹波 ΔV', value: fmt(dv * 1e3, 1), unit: 'mV' }
        ];
      },
      chart: {
        title: 'ΔV(C)：Vin、Vout、fsw、L 取当前值',
        xlabel: 'C / µF', ylabel: 'ΔV / mV',
        /* 域收到工作点邻域：ΔV 是 1/C 双曲线，横轴从 1µF 起会让 ymax 被
           小电容端撑大 100 倍，红点贴底 1% 看不见。取 [C/2, 4C]，红点落在
           43% 高度，形状仍是双曲线，读者能看出「电容翻倍、纹波减半」。 */
        domain: function (x) { return [x.c / 2, x.c * 4]; },
        curve: function (c, x) {
          var d = x.vout / x.vin;
          var dIl = (x.vin - x.vout) * d / ((x.l * 1e-6) * (x.fsw * 1e3));
          return dIl / (8 * (x.fsw * 1e3) * (c * 1e-6)) * 1e3;
        },
        spot: function (x) {
          var d = x.vout / x.vin;
          var dIl = (x.vin - x.vout) * d / ((x.l * 1e-6) * (x.fsw * 1e3));
          return [x.c, dIl / (8 * (x.fsw * 1e3) * (x.c * 1e-6)) * 1e3];
        }
      }
    },
    noise: {
      name: '热噪声预算',
      note: '约翰逊噪声只看 R、T、B：e_n=√(4kTR) 是密度（nV/√Hz），总噪声 = e_n×√B；一阶系统的噪声带宽 ≈1.57×(−3dB 带宽)，别拿 −3dB 带宽直接乘。',
      inputs: [
        { key: 'r', label: '源电阻', unit: 'kΩ', value: 1, step: 0.5, min: 0.01 },
        { key: 'b', label: '带宽', unit: 'kHz', value: 1000, step: 100, min: 0.1 }
      ],
      compute: function (x) {
        var k = 1.38e-23;
        var r = x.r * 1e3;
        var b = x.b * 1e3;
        var en = Math.sqrt(4 * k * 300 * r);
        return [
          { label: '噪声密度', value: fmt(en * 1e9, 1), unit: 'nV/√Hz' },
          { label: '总噪声', value: fmt(en * Math.sqrt(b) * 1e6, 2), unit: 'µV' }
        ];
      }
    },
    miller: {
      name: 'Miller 电容与输入极点',
      note: 'Miller 放大：基极看进去的等效电容 = (1+|A|)×C_bc；输入极点 f_p = 1/(2π·Rs·C_in)。砍增益、降源阻、cascode 拆桥——三条路都在拿别的东西换带宽。',
      inputs: [
        { key: 'av', label: '第一级增益 |A|', unit: 'V/V', value: 50, step: 5, min: 1 },
        { key: 'rs', label: '源电阻 Rs', unit: 'kΩ', value: 10, step: 1, min: 0.1 },
        { key: 'cbc', label: 'C_bc', unit: 'pF', value: 5, step: 1, min: 0.1 }
      ],
      compute: function (x) {
        var cin = (1 + x.av) * x.cbc;                       // pF
        var fp = 1 / (2 * Math.PI * (x.rs * 1e3) * (cin * 1e-12));  // Hz
        return [
          { label: '等效电容 C_in', value: fmt(cin, 0), unit: 'pF' },
          { label: '输入极点 f_p', value: fmt(fp / 1e3, 1), unit: 'kHz' },
          { label: '达成比 f_p/100k', value: fmt(fp / 1e5, 2), unit: '' }
        ];
      },
      chart: {
        title: 'f_p(|A|)：Rs、C_bc 取当前值',
        xlabel: '|A|', ylabel: 'f_p / kHz',
        domain: function (x) { return [5, Math.max(120, x.av * 1.3)]; },
        curve: function (a, x) {
          return 1 / (2 * Math.PI * (x.rs * 1e3) * ((1 + a) * x.cbc * 1e-12)) / 1e3;
        },
        target: { y: 100, label: '目标 100 kHz' },
        spot: function (x) {
          return [x.av, 1 / (2 * Math.PI * (x.rs * 1e3) * ((1 + x.av) * x.cbc * 1e-12)) / 1e3];
        }
      }
    },
    swcap: {
      name: '动态功耗（CV²f）',
      note: '每翻转一次，负载电容被充放一遍，C·V² 的能量一半烧在上管、一半烧在下管：P = C·V²·f。功耗按电压平方缩——5V 降到 3.3V 同样的线省一半还多；直通项另算，栅驱动越慢共同导通窗口越宽。',
      inputs: [
        { key: 'c', label: '负载电容', unit: 'pF', value: 20, step: 5, min: 0.1 },
        { key: 'vdd', label: '电源电压', unit: 'V', value: 5, step: 0.5, min: 0.5 },
        { key: 'f', label: '翻转频率', unit: 'MHz', value: 10, step: 1, min: 0.01 },
        { key: 'lines', label: '同时翻转的线数', unit: '根', value: 1, step: 1, min: 1 }
      ],
      compute: function (x) {
        var per = x.c * 1e-12 * x.vdd * x.vdd * x.f * 1e6 * 1e3;   // mW
        return [
          { label: '单线功耗', value: fmt(per, 2), unit: 'mW' },
          { label: '总线功耗', value: fmt(per * x.lines, 1), unit: 'mW' },
          { label: '每次充放能耗', value: fmt(x.c * 1e-12 * x.vdd * x.vdd * 1e9, 2), unit: 'nJ' }
        ];
      },
      presets: [
        { label: '64 根数据线', set: { lines: 64 } },
        { label: '降压到 3.3V', set: { vdd: 3.3 } }
      ]
    },
    samplehold: {
      name: '电荷注入与采集时间',
      note: '断开瞬间沟道电荷一半踢进保持电容：ΔV = Q/(2C)，加大电容摊薄台阶，但 τ = R·C 同步放大——注入定电容下限，采集速度定上限。§8.4 的预算口径按 2pC 兜底，比典型值狠 10 倍。',
      inputs: [
        { key: 'q', label: '沟道电荷', unit: 'pC', value: 0.2, step: 0.1, min: 0.01 },
        { key: 'ch', label: '保持电容', unit: 'pF', value: 10, step: 5, min: 1 },
        { key: 'ron', label: '导通电阻', unit: 'Ω', value: 45, step: 5, min: 1 },
        { key: 'bits', label: 'ADC 位数', unit: '位', value: 12, step: 1, min: 8 },
        { key: 'vref', label: '量程 VREF', unit: 'V', value: 2.048, step: 0.512, min: 0.1 }
      ],
      compute: function (x) {
        var lsb = x.vref / Math.pow(2, x.bits);                    // V
        var dv = (x.q * 1e-12) / (2 * x.ch * 1e-12);               // V
        var tau = x.ron * x.ch * 1e-12;                            // s
        return [
          { label: '1 LSB', value: fmt(lsb * 1e6, 1), unit: 'µV' },
          { label: '注入台阶 ΔV', value: fmt(dv * 1e3, 2), unit: 'mV' },
          { label: '折合误差', value: fmt(dv / lsb, 1), unit: 'LSB' },
          { label: '采集 8.3τ', value: fmt(8.3 * tau * 1e9, 1), unit: 'ns' }
        ];
      },
      presets: [
        { label: '加到 100pF', set: { ch: 100 } },
        { label: '预算口径 2pC', set: { q: 2 } }
      ],
      chart: {
        title: 'ΔV(C_h)：电荷、R_on 取当前值',
        xlabel: 'C_h / pF', ylabel: 'ΔV / mV',
        /* 1/C 双曲线：域收到 [C/2, 4C]，工作点落在中带，小电容端不撑爆 ymax（同 buck）。 */
        domain: function (x) { return [x.ch / 2, x.ch * 4]; },
        curve: function (c, x) { return (x.q * 1e-12) / (2 * c * 1e-12) * 1e3; },
        spot: function (x) { return [x.ch, (x.q * 1e-12) / (2 * x.ch * 1e-12) * 1e3]; }
      }
    },
    loop: {
      name: '环路增益与相位裕度',
      note: '在 |T|=|A·β|≥1 的交越频率上判稳：相位裕度 = 180° + 该频率的总相移。≥45° 稳；30~45° 勉强，振铃可见；<30° 危险，落地前先补偿。环路增益不到 1 时这条判据没有意义。',
      inputs: [
        { key: 'avdb', label: '开环增益', unit: 'dB', value: 60, step: 5, min: 0 },
        { key: 'phase', label: '总相移', unit: '°', value: -120, step: 5, min: -179 },
        { key: 'beta', label: '反馈系数 β', unit: '', value: 0.1, step: 0.05, min: 0.001 }
      ],
      compute: function (x) {
        var t = Math.pow(10, x.avdb / 20) * x.beta;
        var margin = 180 + x.phase;
        var verdict = margin >= 45 ? '稳' : (margin >= 30 ? '勉强' : '危险');
        return [
          { label: '环路增益 A·β', value: fmt(t, 1), unit: '×' },
          { label: '环路增益 dB', value: fmt(20 * Math.log(t) / Math.LN10, 1), unit: 'dB' },
          { label: '相位裕度', value: fmt(margin, 0), unit: '°' },
          { label: '判定', value: verdict, unit: '' }
        ];
      },
      presets: [
        { label: '补偿足够 −120°', set: { phase: -120 } },
        { label: '补偿不足 −170°', set: { phase: -170 } }
      ]
    }
  };

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function drawChart(cfg, x) {
    /* 就地算曲线：纯 inline SVG，无依赖；随每次 render 重建（60 点，毫秒级）。 */
    var W = 360, H = 150, L = 46, R = 10, T = 22, B = 28;
    var iw = W - L - R, ih = H - T - B;
    var dom = cfg.domain(x);
    var n = 60, ys = [];
    var i, t;
    for (i = 0; i <= n; i++) {
      t = dom[0] + (dom[1] - dom[0]) * i / n;
      ys.push(cfg.curve(t, x));
    }
    var ymax = Math.max.apply(null, ys.concat(cfg.target ? [cfg.target.y] : [0])) * 1.12 || 1;
    function sx(v) { return L + (v - dom[0]) / (dom[1] - dom[0]) * iw; }
    function sy(v) { return T + ih - (v / ymax) * ih; }
    var pts = [];
    for (i = 0; i <= n; i++) {
      t = dom[0] + (dom[1] - dom[0]) * i / n;
      pts.push(sx(t).toFixed(1) + ',' + sy(ys[i]).toFixed(1));
    }
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + cfg.title + '">';
    s += '<text x="' + L + '" y="14" font-size="10.5" font-weight="bold" fill="#475569">' + cfg.title + '</text>';
    s += '<line x1="' + L + '" y1="' + (T + ih) + '" x2="' + (L + iw) + '" y2="' + (T + ih) + '" stroke="#94a3b8" stroke-width="1"/>';
    s += '<line x1="' + L + '" y1="' + T + '" x2="' + L + '" y2="' + (T + ih) + '" stroke="#94a3b8" stroke-width="1"/>';
    if (cfg.target) {
      s += '<line x1="' + L + '" y1="' + sy(cfg.target.y).toFixed(1) + '" x2="' + (L + iw) + '" y2="' + sy(cfg.target.y).toFixed(1) + '" stroke="#b45309" stroke-width="1.2" stroke-dasharray="4,3"/>';
      s += '<text x="' + (L + iw - 2) + '" y="' + (sy(cfg.target.y) - 4).toFixed(1) + '" text-anchor="end" font-size="9.5" font-weight="bold" fill="#b45309">' + cfg.target.label + '</text>';
    }
    s += '<polyline points="' + pts.join(' ') + '" fill="none" stroke="#2563eb" stroke-width="2" stroke-linejoin="round"/>';
    var sp = cfg.spot(x);
    var cx = Math.min(Math.max(sp[0], dom[0]), dom[1]);
    s += '<circle cx="' + sx(cx).toFixed(1) + '" cy="' + sy(sp[1]).toFixed(1) + '" r="4" fill="#dc2626"/>';
    s += '<text x="' + sx(dom[0]).toFixed(1) + '" y="' + (H - 8) + '" font-size="9.5" fill="#475569">' + fmt(dom[0], dom[0] < 10 ? 1 : 0) + '</text>';
    s += '<text x="' + sx(dom[1]).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="end" font-size="9.5" fill="#475569">' + fmt(dom[1], 0) + ' ' + cfg.xlabel + '</text>';
    s += '<text x="6" y="' + (T + 4) + '" font-size="9.5" fill="#475569">' + cfg.ylabel + '</text>';
    s += '<text x="6" y="' + (T + ih) + '" font-size="9.5" fill="#475569">0</text>';
    s += '</svg>';
    return s;
  }

  function build(root, key) {
    var spec = CALCS[key];
    if (!spec) return;
    root.dataset.calcReady = '1';
    var box = el('div', 'calc-box');
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', '就地算：' + spec.name);

    var title = el('p', 'calc-title', '就地算 · ' + spec.name);
    box.appendChild(title);

    var inputs = el('div', 'calc-inputs');
    var values = {};
    spec.inputs.forEach(function (input) {
      var label = el('label', 'calc-field');
      label.appendChild(el('span', 'calc-field-label', input.label));
      var widget;
      if (input.type === 'select') {
        widget = document.createElement('select');
        widget.setAttribute('aria-label', input.label);
        input.options.forEach(function (opt) {
          var option = document.createElement('option');
          option.value = opt[0];
          option.textContent = opt[1];
          if (opt[0] === input.value) option.selected = true;
          widget.appendChild(option);
        });
      } else {
        widget = document.createElement('input');
        widget.type = 'number';
        widget.value = input.value;
        widget.step = input.step;
        if (input.min !== undefined) widget.min = input.min;
        widget.setAttribute('aria-label', input.label + '（' + input.unit + '）');
      }
      widget.addEventListener('input', render);
      widget.addEventListener('change', render);
      values[input.key] = { input: input, widget: widget };
      label.appendChild(widget);
      label.appendChild(el('span', 'calc-unit', input.unit || ''));
      inputs.appendChild(label);
    });
    box.appendChild(inputs);

    if (spec.presets) {
      var presets = el('div', 'calc-presets');
      spec.presets.forEach(function (preset) {
        var btn = el('button', null, preset.label);
        btn.type = 'button';
        btn.setAttribute('aria-label', '预设：' + preset.label);
        btn.addEventListener('click', function () {
          Object.keys(preset.set).forEach(function (k) {
            if (values[k]) values[k].widget.value = preset.set[k];
          });
          render();
        });
        presets.appendChild(btn);
      });
      box.appendChild(presets);
    }

    var outputs = el('div', 'calc-outputs');
    box.appendChild(outputs);
    var chartBox = null;
    if (spec.chart) {
      chartBox = el('div', 'calc-chart');
      box.appendChild(chartBox);
    }
    box.appendChild(el('p', 'calc-note', spec.note));
    root.appendChild(box);

    function read() {
      var x = {};
      Object.keys(values).forEach(function (key) {
        var entry = values[key];
        if (entry.input.type === 'select') {
          x[key] = entry.widget.value;
        } else {
          var v = parseFloat(entry.widget.value);
          x[key] = isNaN(v) ? 0 : v;
        }
      });
      return x;
    }

    function render() {
      var x = read();
      var rows = spec.compute(x);
      outputs.textContent = '';
      rows.forEach(function (row) {
        var chip = el('span', 'calc-out');
        var value = el('b', null, row.value);
        chip.appendChild(value);
        chip.appendChild(el('span', 'calc-out-unit', row.unit ? ' ' + row.unit : ''));
        chip.appendChild(el('span', 'calc-out-label', row.label));
        outputs.appendChild(chip);
      });
      if (chartBox) chartBox.innerHTML = drawChart(spec.chart, x);
    }

    render();
  }

  function init() {
    document.querySelectorAll('.calc[data-calc]').forEach(function (root) {
      if (root.isConnected && !root.dataset.calcReady) {
        build(root, root.dataset.calc);
      }
    });
  }

  if (typeof document$ !== 'undefined') { document$.subscribe(init); }
  else if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
}());
