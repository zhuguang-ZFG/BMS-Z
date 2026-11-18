// BMS AFE：一颗 ADC 轮流巡逻各串——小人持探针沿串联电芯逐节点测，
// 每测一节，头顶纸带盖一个点、角落钟针走一格；六点错落，没有同一瞬间
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, seg, breathe, pulse, lp, clamp } = R;

  const RED = '#cf222e';
  const N = 6;
  const CELLS = [];                            // 电芯中心 x
  for (let i = 0; i < N; i++) CELLS.push(-132 + i * 44);
  const BENCH = { x0: -152, x1: 134, top: -56, apron: -44 };  // 长实验台
  const CELL_TOP = -80;                        // 电芯顶面（台面上 24）
  const HOME = -166;                           // 起点（排尾左侧）
  const TAPE = { x: -150, y: -170, w: 296, h: 15 };
  const CLOCK = { x: 170, y: -150, r: 15 };

  // 每节测量位（人站在电芯左侧 10，探针垂落正好点在电芯顶面中心）
  const MPOS = CELLS.map(cx => cx - 10);
  // 六段走 + 六次停测（每节 0.85s）：走到位→停→探针点下→纸带点落、钟针走格
  const LEGS = [];
  const MEAS = [];
  let prev = HOME;
  for (let i = 0; i < N; i++) {
    const a = 0.4 + i * 0.85, b = a + 0.38;
    LEGS.push([a, b, prev, MPOS[i]]);
    MEAS.push([b, b + 0.47]);
    prev = MPOS[i];
  }
  const STAMP = MEAS.map(m => m[0] + 0.15);    // 每节落点/盖章时刻
  const TURN = 5.75;                           // 末测后站立转身
  const RETURN_WALK = [5.8, 8.0];              // 回家正向走（2.2s，244u≈111u/s）
  const SETTLE = 8.05;                         // 到点立定
  const DUR = 9;

  function benchAndCells(g, T, fadeK) {
    // 台面 + 台面上的串联电芯
    ln(g, BENCH.x0, BENCH.top, BENCH.x1, BENCH.top, 2, C.ink);
    // 串联排线：一条线把各节顶端的接线端子串起来
    ln(g, CELLS[0] - 14, CELL_TOP - 6, CELLS[N - 1] + 14, CELL_TOP - 6, 1.4, C.ink);
    for (let i = 0; i < N; i++) {
      const cx = CELLS[i];
      // 电芯：小圆柱（立在台面上）
      rr(g, cx - 12, CELL_TOP, 24, BENCH.top - CELL_TOP - 1, 4);
      inkFill(g, C.paper, 1.5);
      g.beginPath(); g.ellipse(cx, CELL_TOP, 12, 3.4, 0, 0, Math.PI * 2);
      g.fillStyle = C.paper; g.fill(); g.lineWidth = 1.4; g.strokeStyle = C.ink; g.stroke();
      // 顶端接线端子
      ln(g, cx - 5, CELL_TOP - 6, cx - 5, CELL_TOP, 1.6, C.ink);
      ln(g, cx + 5, CELL_TOP - 6, cx + 5, CELL_TOP, 1.6, C.ink);
      // 被测中的红圈脉冲：只在真实脉冲窗内出现，收尾淡出只降透明度不重启
      if (T >= 0) {
        const raw = seg(T, STAMP[i], STAMP[i] + 0.55);
        if (raw > 0.01 && raw < 1) {
          g.save();
          g.globalAlpha *= (1 - raw) * 0.9 * fadeK;
          g.beginPath(); g.arc(cx, CELL_TOP - 6, 5 + raw * 7, 0, Math.PI * 2);
          g.lineWidth = 2; g.strokeStyle = RED; g.stroke();
          g.restore();
        }
      }
    }
  }

  function benchFront(g) {
    // 台裙与台腿：画在人物之后，遮住小腿（人站在台后）
    ln(g, BENCH.x0, BENCH.apron, BENCH.x1, BENCH.apron, 1.6, C.ink);
    ln(g, BENCH.x0 + 4, BENCH.apron, BENCH.x0 + 2, 0, 2.2, C.ink);
    ln(g, BENCH.x1 - 4, BENCH.apron, BENCH.x1 - 2, 0, 2.2, C.ink);
    ln(g, (BENCH.x0 + BENCH.x1) / 2 - 30, BENCH.apron, (BENCH.x0 + BENCH.x1) / 2 - 30, 0, 1.6, '#9a9a9a');
    ln(g, (BENCH.x0 + BENCH.x1) / 2 + 30, BENCH.apron, (BENCH.x0 + BENCH.x1) / 2 + 30, 0, 1.6, '#9a9a9a');
  }

  function tape(g, T, fadeK) {
    rr(g, TAPE.x, TAPE.y, TAPE.w, TAPE.h, 3);
    inkFill(g, '#fdfaf2', 1.3, '#c9c4b6');
    // 纸带上的点：每测一节盖一个，逐拍出现，间距即时间差
    for (let i = 0; i < N; i++) {
      const px = TAPE.x + 26 + i * 46;
      if (T < 0) {
        g.beginPath(); g.arc(px, TAPE.y + TAPE.h / 2, 1.6, 0, Math.PI * 2);
        g.fillStyle = '#ddd8ca'; g.fill();
      } else {
        const raw = clamp(seg(T, STAMP[i], STAMP[i] + 0.35), 0, 1);
        if (raw > 0.01) {
          // 盖章后保持满尺寸，收尾只降透明度（防缩小弹跳）
          g.save();
          g.globalAlpha *= fadeK;
          const k = E.back(raw);
          g.beginPath(); g.arc(px, TAPE.y + TAPE.h / 2, 3 * Math.min(k, 1.15), 0, Math.PI * 2);
          g.fillStyle = C.ink; g.fill();
          g.restore();
        }
      }
    }
  }

  function clock(g, stamped, fadeK) {
    // 无数字小钟：四根刻度，一根指针；每测一节走一格
    g.beginPath(); g.arc(CLOCK.x, CLOCK.y, CLOCK.r, 0, Math.PI * 2);
    inkFill(g, C.paper, 1.4, '#c9c4b6');
    for (let i = 0; i < 4; i++) {
      const a = i * Math.PI / 2;
      ln(g, CLOCK.x + Math.sin(a) * (CLOCK.r - 4), CLOCK.y - Math.cos(a) * (CLOCK.r - 4),
         CLOCK.x + Math.sin(a) * (CLOCK.r - 1), CLOCK.y - Math.cos(a) * (CLOCK.r - 1), 1.3, C.ink);
    }
    const a = -Math.PI / 2 + stamped * 0.32 * fadeK;
    ln(g, CLOCK.x, CLOCK.y, CLOCK.x + Math.sin(a) * (CLOCK.r - 5), CLOCK.y - Math.cos(a) * (CLOCK.r - 5), 2, C.ink);
    g.beginPath(); g.arc(CLOCK.x, CLOCK.y, 2, 0, Math.PI * 2); g.fillStyle = C.ink; g.fill();
  }

  SC['bms-afe-patrol'] = {
    dur: DUR,
    width: 400,
    label: '巡逻员持探针沿一排串联电芯逐节点测量：每测一节，头顶纸带盖下一个点，角落小钟的指针走一格；纸带上六点依次排开，没有两个点来自同一瞬间。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      // 朝向：去程面向右；5.75 站立转身面向左走回家；8.05 到点转回右并停立（与 idle 一致，防 end-pop）
      const sx = T < 0 ? 1 : T >= TURN && T < SETTLE ? -1 : 1;
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);
      let fadeK = 1, stamped = 0;

      if (T < 0) {
        // 空闲：站在排尾，探头朝下，遥望这一排
        pose = mix(pose, P({ hF: [14, -78], head: [8, -115], chest: [3, -89] }), pulse(t, 5.5, 2, 2.2));
      } else {
        fadeK = 1 - seg(T, this.dur - 0.5, this.dur);
        stamped = STAMP.filter(v => T >= v).length;
        if (T < RETURN_WALK[0]) {
          // 走位：六段走 + 六个停测位
          let placed = false;
          for (let i = 0; i < N; i++) {
            const [a, b, x0, x1] = LEGS[i];
            if (T < a) break;
            if (T < b) {
              const ws = walkSeg(T, a, b, x0, x1);
              x = ws.x; gait = ws; placed = true; break;
            }
            x = x1;
            const [m0, m1] = MEAS[i];
            if (T < m1) {
              placed = true;
              // 停测：微蹲 + 探针点下，针尖落在电芯顶面中心（蹲身后肩低于目标，手臂下斜避脸）
              const dip = E.soft(seg(T, m0 + 0.03, m0 + 0.26)) * (1 - E.soft(seg(T, m1 - 0.24, m1 - 0.03)));
              pose = mix(pose, P({
                hF: lp([CELLS[i] - 2, CELL_TOP - 16], x, 0, 1), hB: [-6, -56],
                head: [8, -106], chest: [5, -84], ef: 0.35,
                hip: [0, -14], kF: 16, kB: -12, fF: [10, 0], fB: [-8, 0],
              }), dip);
              break;
            }
          }
          if (!placed) { /* 末次测量后停留原位，等待点头 */ }
        } else if (T < SETTLE) {
          // 回家：面向左的正向走（craft.md 通用配方，dir*sx>0 不取负相）
          const ws = walkSeg(T, RETURN_WALK[0], RETURN_WALK[1], MPOS[N - 1], HOME);
          x = ws.x;
          gait = ws.dir * sx < 0 ? { ph: -ws.ph, amp: ws.amp, stride: ws.stride } : ws;
        } else {
          x = HOME;   // 到点立定（breathe 基准姿，与 idle 衔接）
        }
        // 测完全排，站定点头
        const nod = E.soft(seg(T, 5.55, 5.68)) * (1 - E.soft(seg(T, 5.72, 5.85)));
        pose = mix(pose, P({ head: [6, -108], chest: [3, -88], hF: [12, -62], hB: [-4, -52] }), nod);
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride || 26 });

      benchAndCells(g, T, fadeK);
      tape(g, T, fadeK);
      clock(g, T < 0 ? 0 : stamped, T < 0 ? 1 : fadeK);
      fig(g, pose, x, 0, {
        sx, wave: S.wave, wt: S.wt,
        held: (g2, J) => {
          // 手持探针：R.held 把前手世界坐标传给回调，探针从掌心向下垂
          R.held(g2, J, (handF) => {
            ln(g2, handF[0], handF[1], handF[0] + 3, handF[1] + 15, 2.2, C.ink);
            g2.beginPath(); g2.arc(handF[0] + 3.6, handF[1] + 16.5, 2, 0, Math.PI * 2); g2.fillStyle = RED; g2.fill();
          });
        },
      });
      benchFront(g);
    },
  };
})();
