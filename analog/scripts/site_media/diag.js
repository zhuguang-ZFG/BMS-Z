/* 入场诊断：6 题 → 4 条真实路线。确定性评分，无存储、无随机。 */
(function () {
  var QUESTIONS = [
    { q: '你的电路底子有多深？', key: 'f', opts: [
      ['几乎零基础，欧姆定律都还给老师了', 0],
      ['物理课学过，会串并联和欧姆定律', 1],
      ['焊过东西、用万用表量过电压', 2],
      ['正在做硬件/嵌入式相关工作', 3]] },
    { q: '数学工具还剩多少？', key: 'm', opts: [
      ['四则运算最稳', 0],
      ['阻抗、RC 时间常数 vaguely 记得', 1],
      ['复数、微分方程能上手', 2],
      ['拉普拉斯变换、极零点分析是日常', 3]] },
    { q: '每周能投入多少时间？', key: 't', opts: [
      ['不到 1 小时', 0],
      ['2～4 小时', 1],
      ['6～8 小时', 2],
      ['8 小时以上', 3]] },
    { q: '学模拟电路为了什么？', key: 'g', opts: [
      ['考试/面试需要', 0],
      ['DIY：做个小项目让它响/亮/动', 1],
      ['工作：调板子、排故障', 2],
      ['转行做模拟设计（板级或 IC）', 3]] },
    { q: '手边有什么装备？', key: 'e', opts: [
      ['只有手机/电脑', 0],
      ['万用表', 1],
      ['烙铁 + 万用表', 2],
      ['焊台 + 示波器', 3]] },
    { q: '最想先干哪件事？', key: 's', opts: [
      ['先看动画找物理感觉', 0],
      ['把公式推明白', 1],
      ['拆块真板子对着量', 2],
      ['照成品项目直接焊一个', 3]] }
  ];
  var TIMELINES = [
    ['t-min', '5 分钟'],
    ['t-1h', '1 小时'],
    ['t-week', '一周末']
  ];
  var RESULTS = [
    { id: 'practice', title: '工程实战线：从方法论切入',
      who: '你在调真板子，最缺的是章法而不是知识。',
      steps: [
        ['第 14 章：设计方法论——需求 → 规格 → 器件', 'p3-01-ch14.html#ch14'],
        ['第 16 章：排故五步法，一次只改一个变量', 'p4-01-ch16.html#ch16'],
        ['第 17 章：症状 → 原因 → 对策速查总表', 'p4-02-ch17.html#ch17']],
      calc: [['速查表·设计与可靠性', '#design'], ['速查表·排故', '#debug']],
      timeNote: '按你的时间预算，把 14/16/17 章排进' },
    { id: 'deep', title: '模拟设计深造线：打穿器件与拓扑',
      who: '目标是模拟设计岗：定性直觉 + 定量估算两条腿都要。',
      steps: [
        ['第 0～4 章快速过：只精读第 3、4 章（BJT/MOS）', 'p1-04-ch3.html#ch3'],
        ['第 11 章：三种组态与电流镜——IC 设计的语言', 'p2-01-ch11.html#ch11'],
        ['沿路线图 ⑥ → 方向深化（板级 / IC 分支）', 'p0-06-roadmap.html#roadmap']],
      calc: [['速查表·MOSFET', '#mos'], ['速查表·拓扑·噪声·稳定', '#topo']],
      timeNote: '深造靠的是复利，把 3/4/11 章排进' },
    { id: 'weekend', title: '一周末硬件线：先让它动起来',
      who: '有工具、想动手：最短路径是「读一章 → 焊一章」。',
      steps: [
        ['第 0 章：水路比喻 + 分压带载（半天）', 'p1-01-ch0.html#ch0'],
        ['第 1 章 + 第 5 章：无源件与推挽开漏（一天）', 'p1-02-ch1.html#ch1'],
        ['焊一个里程碑项目，卡住就翻第 16 章', 'p4-01-ch16.html#ch16']],
      calc: [['速查表·直流基础', '#dc'], ['速查表·输出级', '#outstage']],
      timeNote: '读一章焊一章，按预算执行' },
    { id: 'intuition', title: '5 分钟直觉线：先建立画面感',
      who: '时间紧或零基础：别碰公式，先看动画建立直觉。',
      steps: [
        ['0.1 水路比喻：电压/电流/回路三件套', 'p1-01-ch0.html#ch0'],
        ['动画中心：108 张 SMIL 动画随便点', 'p5-00-part5.html#part5'],
        ['★ 必读精选：虚短虚断等 5 分钟套餐', 'p0-05-picks.html#picks']],
      calc: [['速查表·直流基础', '#dc']],
      timeNote: '先花最小的成本建立画面，从' }
  ];
  function decide(a) {
    if (a.g === 2 && a.f >= 2) return RESULTS[0];
    if (a.g === 3 && a.f >= 2 && a.m >= 2) return RESULTS[1];
    if (a.e >= 2 && a.t >= 1 && (a.g === 1 || a.g === 3 || a.s >= 2)) return RESULTS[2];
    return RESULTS[3];
  }
  function timelineFor(t) {
    return TIMELINES[t >= 2 ? 2 : t];
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function linkRow(list, item) {
    var a = el('a', null, item[0]);
    a.href = item[1];
    var li = el('li');
    li.append(a);
    list.append(li);
  }
  function app(root) {
    var stage = el('div', 'diag-stage');
    root.replaceChildren(stage);
    var answers = {};
    function renderResult(r) {
      var card = el('div', 'diag-result');
      card.dataset.diagResult = r.id;
      card.append(el('h2', null, r.title), el('p', 'diag-who', r.who));
      var steps = el('ol', 'diag-steps');
      r.steps.forEach(function (s) { linkRow(steps, s); });
      var tl = timelineFor(answers.t);
      var time = el('p', 'diag-time');
      var ta = el('a', null, ' ' + r.timeNote + '「' + tl[1] + '」档 → 三条时间线');
      ta.href = 'p0-03-timeline.html#' + tl[0];
      time.append(ta);
      var calc = el('p', 'diag-calc');
      calc.append(el('span', null, '顺手算：'));
      r.calc.forEach(function (c, i) {
        if (i) { calc.append(document.createTextNode(' · ')); }
        var ca = el('a', null, c[0]);
        ca.href = 'p0-08-cheatsheet.html' + c[1];
        calc.append(ca);
      });
      card.append(steps, time, calc);
      var again = el('button', 'diag-btn', '重测一次');
      again.type = 'button';
      again.addEventListener('click', function () { start(); });
      card.append(again);
      stage.replaceChildren(card);
    }
    function start() {
      answers = {};
      step(0);
    }
    function step(i) {
      if (i >= QUESTIONS.length) { renderResult(decide(answers)); return; }
      var item = QUESTIONS[i];
      var card = el('div', 'diag-card');
      var head = el('p', 'diag-progress', '第 ' + (i + 1) + ' / ' + QUESTIONS.length + ' 题');
      card.append(head, el('h2', null, item.q));
      var list = el('div', 'diag-opts');
      item.opts.forEach(function (opt) {
        var b = el('button', 'diag-btn', opt[0]);
        b.type = 'button';
        b.addEventListener('click', function () {
          answers[item.key] = opt[1];
          step(i + 1);
        });
        list.append(b);
      });
      card.append(list);
      if (i > 0) {
        var back = el('button', 'diag-back', '← 上一题');
        back.type = 'button';
        back.addEventListener('click', function () { step(i - 1); });
        card.append(back);
      }
      stage.replaceChildren(card);
    }
    start();
  }
  function init() {
    document.querySelectorAll('.diag-root').forEach(function (root) {
      if (root.isConnected && !root.dataset.diagReady) {
        root.dataset.diagReady = '1';
        app(root);
      }
    });
  }
  if (typeof document$ !== 'undefined') { document$.subscribe(init); }
  else if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); }
  else { init(); }
}());
