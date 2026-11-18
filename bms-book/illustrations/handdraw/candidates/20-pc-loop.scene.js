// BMS 上位机回路：PC 只观察、回放、注入，不进保护回路——小人在台后打字，
// 圆点一串沿上方管道送进桥接木箱，齿轮箱每拍转一格，黄油小包沿回管返回屏幕，
// 屏幕小灯逐对点亮；四拍过后齿轮归位、屏幕复原，一切可以重来
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, fig, inkFill, rr, ln, seg, breathe, pulse, lp, clamp } = R;

  const GREEN = '#1a7f37';
  const BUTTER = '#f0b429';   // 回程小包（与 07 的 butter 系错开，避免与纸张混淆）

  // 走线：上出下回，两条长水平管都在人头上方（人头顶约 -122）
  const DOWN = [[-150, -120], [-150, -160], [82, -160], [82, -80]];   // 屏幕顶 → 桥接木箱顶
  const BACK = [[66, -80], [66, -136], [-163, -136], [-163, -120]];   // 木箱顶 → 屏幕顶（x=82 处跳线）
  const CALL = [[112, -61], [131, -61]];                              // 木箱 → 齿轮箱（每拍调用）

  const DESK = { x0: -196, x1: -96, top: -70 };
  const SCREEN = { x: -190, y: -120, w: 56, h: 46 };                  // 屏幕箱体（含边框）
  const BENCH = { x0: 40, x1: 198, top: -40 };
  const CRATE = { x: 52, y: -80, w: 60, h: 40 };                      // 桥接木箱
  const GEARBOX = { x: 132, y: -84, w: 62, h: 44 };                   // 齿轮箱
  const GC = { x: 163, y: -62, r: 14 };                               // 齿轮
  const LAMP = { x: 104, poleTop: -94, bulbY: -98 };                  // 木箱顶小灯
  const HOME = -84;                                                   // 人站在台右侧，面向左

  const DUR = 8;
  const TICKS = [0.4, 2.0, 3.6, 5.2];   // 四拍
  const BURST = 0.7, DOT_GAP = 0.13, NDOT = 4;
  const PACK0 = 0.85, PACK1 = 1.7;      // 回程小包：起/止（相对拍起点）
  const GEAR_STEP = Math.PI / 8;

  // 折线按弧长取点
  function pathPt(pts, s) {
    let total = 0;
    const lens = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]);
      lens.push(l); total += l;
    }
    let d = clamp(s, 0, 1) * total;
    for (let i = 0; i < lens.length; i++) {
      if (d <= lens[i] || i === lens.length - 1) {
        const k = lens[i] ? d / lens[i] : 0;
        return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k];
      }
      d -= lens[i];
    }
    return pts[pts.length - 1];
  }

  function pipe(g, pts, jumps) {
    // 手绘主管 + 跳线缺口（jumps: [s0,s1] 弧长比例区间留白）
    g.save();
    g.lineWidth = 2.6; g.strokeStyle = C.ink; g.lineCap = 'round';
    if (!jumps || !jumps.length) {
      g.beginPath();
      g.moveTo(pts[0][0], pts[0][1]);
      for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
      g.stroke();
    } else {
      // 分段画，跳过缺口区间
      let total = 0;
      const cum = [0];
      for (let i = 0; i < pts.length - 1; i++) {
        total += Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]);
        cum.push(total);
      }
      const cuts = jumps.map(([a, b]) => [a * total, b * total]).sort((p, q) => p[0] - q[0]);
      const segs = [];
      let cur = 0;
      for (const [a, b] of cuts) { if (a > cur) segs.push([cur, a]); cur = Math.max(cur, b); }
      if (cur < total) segs.push([cur, total]);
      for (const [d0, d1] of segs) {
        const p0 = pathPt(pts, d0 / total), p1 = pathPt(pts, d1 / total);
        g.beginPath(); g.moveTo(p0[0], p0[1]); g.lineTo(p1[0], p1[1]); g.stroke();
        // 端口小圆点，像被剪断的管口
        for (const p of [p0, p1]) { g.beginPath(); g.arc(p[0], p[1], 1.8, 0, Math.PI * 2); g.fillStyle = C.ink; g.fill(); }
      }
    }
    g.restore();
  }

  SC['bms-pc-loop'] = {
    dur: DUR,
    width: 400,
    label: '小人站在控制台的屏幕旁打字：一串圆点沿头顶管道送进桥接木箱，旁边齿轮箱每拍转过一格，一枚黄油色小包沿回管返回屏幕，屏幕上的灯逐对点亮；四拍播完齿轮与屏幕复位，可以重新播放。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      // 收尾复位系数：7.3 后齿轮倒转、屏幕灯退回（与 idle 完全一致，防 end-pop）
      const kBack = T >= 0 ? E.soft(seg(T, 7.3, 7.95)) : 0;

      // 台面、长凳、箱体（先画，管线从箱顶接入时被遮住接缝）
      ln(g, DESK.x0, DESK.top, DESK.x1, DESK.top, 2.2, C.ink);
      ln(g, DESK.x0 + 4, DESK.top, DESK.x0 + 4, 0, 2.2, C.ink);
      ln(g, DESK.x1 - 4, DESK.top, DESK.x1 - 4, 0, 2.2, C.ink);
      ln(g, DESK.x0 + 8, DESK.top - 12, DESK.x1 - 8, DESK.top - 12, 1.2, '#9a9a9a');
      // 键盘（斜面向人）
      rr(g, -128, -76, 30, 6, 2);
      inkFill(g, C.paper, 1.3);
      for (let i = 0; i < 3; i++) ln(g, -122 + i * 8, -75, -122 + i * 8, -71.5, 1, '#9a9a9a');
      // 屏幕箱体 + 暗屏 + 支架
      rr(g, SCREEN.x, SCREEN.y, SCREEN.w, SCREEN.h, 4);
      inkFill(g, C.paper, 1.7);
      ln(g, -167, SCREEN.y + SCREEN.h, -167, DESK.top, 1.8, C.ink);
      ln(g, -159, SCREEN.y + SCREEN.h, -159, DESK.top, 1.8, C.ink);
      rr(g, SCREEN.x + 4, SCREEN.y + 4, SCREEN.w - 8, SCREEN.h - 8, 3);
      inkFill(g, '#262b33', 1.2, C.ink);

      ln(g, BENCH.x0, BENCH.top, BENCH.x1, BENCH.top, 2.2, C.ink);
      ln(g, BENCH.x0 + 4, BENCH.top, BENCH.x0 + 2, 0, 2.2, C.ink);
      ln(g, BENCH.x1 - 4, BENCH.top, BENCH.x1 - 2, 0, 2.2, C.ink);
      ln(g, (BENCH.x0 + BENCH.x1) / 2 - 40, BENCH.top, (BENCH.x0 + BENCH.x1) / 2 - 40, 0, 1.6, '#9a9a9a');
      ln(g, (BENCH.x0 + BENCH.x1) / 2 + 40, BENCH.top, (BENCH.x0 + BENCH.x1) / 2 + 40, 0, 1.6, '#9a9a9a');

      // 管线（先画管再画箱，箱顶遮住管端口接缝；两条管走向错开，不相交）
      pipe(g, DOWN);
      pipe(g, BACK);
      pipe(g, CALL);

      // 桥接木箱
      rr(g, CRATE.x, CRATE.y, CRATE.w, CRATE.h, 4);
      inkFill(g, '#fdfaf2', 1.7);
      ln(g, CRATE.x + 8, CRATE.y + 10, CRATE.x + CRATE.w - 8, CRATE.y + 10, 1, '#c9c4b6');
      ln(g, CRATE.x + 8, CRATE.y + 16, CRATE.x + CRATE.w - 8, CRATE.y + 16, 1, '#c9c4b6');
      // 齿轮箱
      rr(g, GEARBOX.x, GEARBOX.y, GEARBOX.w, GEARBOX.h, 4);
      inkFill(g, '#fdfaf2', 1.7);
      // 齿轮：外圈 + 固定刻度 + 随拍转动的齿标
      g.beginPath(); g.arc(GC.x, GC.y, GC.r, 0, Math.PI * 2);
      inkFill(g, C.paper, 1.8);
      for (let i = 0; i < 4; i++) {
        const a = i * Math.PI / 2 + Math.PI / 4;
        ln(g, GC.x + Math.sin(a) * (GC.r - 3.5), GC.y - Math.cos(a) * (GC.r - 3.5),
           GC.x + Math.sin(a) * (GC.r - 0.5), GC.y - Math.cos(a) * (GC.r - 0.5), 1.3, '#9a9a9a');
      }
      let gearA = 0;
      for (let i = 0; i < TICKS.length; i++) {
        gearA += GEAR_STEP * E.in(T >= 0 ? seg(T, TICKS[i] + 0.7, TICKS[i] + 1.25) : 0);
      }
      gearA *= (1 - kBack);
      ln(g, GC.x, GC.y, GC.x + Math.sin(gearA) * (GC.r - 4), GC.y - Math.cos(gearA) * (GC.r - 4), 2.4, C.ink);
      g.beginPath(); g.arc(GC.x, GC.y, 2.4, 0, Math.PI * 2); g.fillStyle = C.ink; g.fill();
      // 箱顶小灯：拍到即绿一下
      ln(g, LAMP.x, CRATE.y, LAMP.x, LAMP.poleTop, 1.6, C.ink);
      let lampK = 0;
      for (let i = 0; i < TICKS.length; i++) {
        lampK = Math.max(lampK, T >= 0
          ? seg(T, TICKS[i] + 0.7, TICKS[i] + 0.82) * (1 - seg(T, TICKS[i] + 1.45, TICKS[i] + 1.65))
          : 0);
      }
      g.beginPath(); g.arc(LAMP.x, LAMP.bulbY, 4.5, 0, Math.PI * 2);
      inkFill(g, lampK > 0.02 ? `rgba(26,127,37,${0.25 + 0.75 * lampK})` : '#efece4', 1.4, C.ink);

      // 管内圆点：一拍四粒，送进木箱
      if (T >= 0) {
        for (let i = 0; i < TICKS.length; i++) {
          for (let j = 0; j < NDOT; j++) {
            const s = seg(T, TICKS[i] + j * DOT_GAP, TICKS[i] + j * DOT_GAP + BURST);
            if (s > 0.01 && s < 0.99) {
              const p = pathPt(DOWN, E.in(s) * 0.06 + s * 0.94);
              g.beginPath(); g.arc(p[0], p[1], 2.2, 0, Math.PI * 2);
              g.fillStyle = C.ink; g.fill();
            }
          }
          // 回程黄油小包
          const sp = seg(T, TICKS[i] + PACK0, TICKS[i] + PACK1);
          if (sp > 0.01 && sp < 0.99) {
            const p = pathPt(BACK, sp);
            rr(g, p[0] - 4.5, p[1] - 3, 9, 6, 2.5);
            inkFill(g, BUTTER, 1.3);
          }
          // 每拍调用：木箱 → 齿轮箱一枚绿点
          const sc = seg(T, TICKS[i] + 1.1, TICKS[i] + 1.42);
          if (sc > 0.01 && sc < 0.99) {
            const p = pathPt(CALL, sc);
            g.beginPath(); g.arc(p[0], p[1], 2, 0, Math.PI * 2);
            g.fillStyle = GREEN; g.fill();
          }
        }
      }

      // 屏幕灯：每回来一包点亮一对，收尾复位
      const nArr = T >= 0 ? TICKS.filter(t0 => T >= t0 + PACK1).length : 0;
      for (let j = 0; j < 8; j++) {
        const col = j % 2, row = (j / 2) | 0;
        const dx = -180 + col * 11, dy = -108 + row * 8.5;
        const lit = j < nArr * 2 && kBack < 0.98;
        g.beginPath(); g.arc(dx, dy, 2, 0, Math.PI * 2);
        g.save();
        if (lit) { g.globalAlpha *= (1 - kBack); g.fillStyle = GREEN; }
        else g.fillStyle = '#5b6472';
        g.fill(); g.restore();
      }

      // 人物：台后打字，包到点头。所有姿势变体都显式携带打字手位，
      // mix 只动头/胸——默认手臂是垂手，漏带会被打成 rest（probe D/E 定位的坑）。
      const bob = Math.sin(t * 22) * 2.2;
      const typeF = lp([-116 + bob, -76], HOME, 0, -1);
      const typeB = lp([-126 - bob * 0.6, -78], HOME, 0, -1);
      const base = { hF: typeF, hB: typeB, head: [3, -114], chest: [2, -90] };
      let pose = breathe(P(base), t);
      if (T < 0) {
        // 空闲：抬头看一眼回管
        pose = mix(pose, P({ ...base, head: [5, -119], chest: [3, -89] }), pulse(t, 6, 2, 2.2));
      } else {
        let nod = 0;
        for (let i = 0; i < TICKS.length; i++) {
          const a = TICKS[i] + PACK1;
          nod += E.soft(seg(T, a, a + 0.14)) * (1 - E.soft(seg(T, a + 0.3, a + 0.48)));
        }
        pose = mix(pose, P({ ...base, head: [4, -109], chest: [2.5, -88] }), clamp(nod, 0, 1) * 0.8);
      }
      pose = legs(pose, 0, 0, { arms: false });
      fig(g, pose, HOME, 0, { sx: -1, wave: S.wave, wt: S.wt });
    },
  };
})();
