// BMS 三拍保护：电压针越过红线，保护员数满三拍拉下切断杆；电压只是高位略回落，充电电流归零后才亮起“已切断”
(function () {
  const SC = (window.SCENES = window.SCENES || {});
  const R = window.RIG;
  const { C, E, P, mix, legs, walkSeg, fig, inkFill, rr, ln, text, seg, breathe, pulse, lp, sparks, tickBadge, clamp } = R;
  const lerp = (a, b, k) => a + (b - a) * k;

  const RED = '#cf222e', GREEN = '#1a7f37', GREEN_BG = '#dafbe1';
  const PANEL = { x: -196, y: -150, w: 116, h: 104 };   // 仪表盘箱体
  const GC = { x: -138, y: -84, r: 34 };                  // 表盘中心（面板下半）
  const THR = -0.42;                                      // 红线角度（弧度，0=竖直向上，正值顺时针）
  const LEVER = { x: 56, w: 46, h: 46, top: -46 };        // 杠杆箱
  const PIVOT = { x: 79, y: LEVER.top };                  // 手柄支点
  const HANDLE = 40;
  const REST_ANG = -0.55, PULL_SWING = 1.05;              // 拉杆摆幅：画图与握点共用，必须一致
  const HOME = 6, AT = 50;   // 站在杠杆左侧，面向它；肩点(58,-89)到杆身目标点全程在正前方

  // 表针角度：idle 略偏左；+1=越线。切断充电只撤去 IR 压降，电压高位略回落，不归零
  function needleAngle(kTrip, kCut) {
    const idleA = -0.75;
    const tripA = THR + 0.5;
    const relaxA = lerp(idleA, tripA, 0.62);   // 回落终点仍压在红线以上
    let a = lerp(idleA, tripA, E.back(clamp(kTrip, 0, 1)));
    if (kCut > 0) a = lerp(a, relaxA, E.in(clamp(kCut, 0, 1)));
    return a + Math.sin(kTrip * 40) * 0;
  }

  function gauge(g, kTrip, kCut, tickN, cutBadgeK, fadeK, kI) {
    ln(g, PANEL.x + 20, PANEL.y + PANEL.h, PANEL.x + 8, 0, 2.2);
    ln(g, PANEL.x + PANEL.w - 20, PANEL.y + PANEL.h, PANEL.x + PANEL.w - 10, 0, 2.2);
    rr(g, PANEL.x, PANEL.y, PANEL.w, PANEL.h, 6);
    inkFill(g, C.paper, 1.7);
    // 表盘弧刻度
    for (let i = 0; i <= 4; i++) {
      const a = -1.35 + i * 0.45;
      ln(g, GC.x + Math.sin(a) * (GC.r - 5), GC.y - Math.cos(a) * (GC.r - 5),
         GC.x + Math.sin(a) * GC.r, GC.y - Math.cos(a) * GC.r, 1.4, i === 3 ? RED : '#9a9a9a');
    }
    // 红线
    ln(g, GC.x + Math.sin(THR) * (GC.r - 8), GC.y - Math.cos(THR) * (GC.r - 8),
       GC.x + Math.sin(THR) * (GC.r + 6), GC.y - Math.cos(THR) * (GC.r + 6), 2.2, RED);
    // 指针：压在红线上就是红色，切断后也不变
    const a = needleAngle(kTrip, kCut);
    const nCol = kTrip > 0.5 ? RED : C.ink;
    ln(g, GC.x, GC.y, GC.x + Math.sin(a) * (GC.r - 6), GC.y - Math.cos(a) * (GC.r - 6), 2.4, nCol);
    g.beginPath(); g.arc(GC.x, GC.y, 3, 0, Math.PI * 2); g.fillStyle = C.ink; g.fill();
    // 充电电流条：拉杆后电流先归零，之后才亮绿勾（无文字）
    const TX = PANEL.x + 12, TW = PANEL.w - 24, TY = PANEL.y + PANEL.h - 13;
    rr(g, TX, TY, TW, 4.5, 2);
    inkFill(g, '#efece4', 1, '#c9c4b6');
    if (kI > 0.003) {
      rr(g, TX + 1, TY + 1, Math.max((TW - 2) * kI, 2), 2.5, 1.2);
      inkFill(g, '#5d8f6f', 0);
    }
    // 拍数计数牌：无数字，用圆点个数表示第几拍，第三拍变红
    if (tickN > 0 && fadeK > 0) {
      g.save();
      g.globalAlpha *= fadeK;
      const w = 34, h = 16, bx = PANEL.x + PANEL.w - 24, by = PANEL.y + 30;
      rr(g, bx - w / 2, by - h / 2, w, h, 4);
      inkFill(g, tickN >= 3 ? '#ffebe9' : C.butter, 1.4, tickN >= 3 ? RED : '#b98a1a');
      for (let i = 0; i < 3; i++) {
        const px = bx - 9 + i * 9;
        g.beginPath(); g.arc(px, by, 3, 0, Math.PI * 2);
        if (i < tickN) { g.fillStyle = tickN >= 3 ? RED : C.umber; g.fill(); }
        else { g.fillStyle = '#ffffff'; g.fill(); g.lineWidth = 1.2; g.strokeStyle = '#c9c4b6'; g.stroke(); }
      }
      g.restore();
    }
    // 切断确认：无文字，大号绿勾（电流归零后才弹出）
    if (cutBadgeK > 0) {
      tickBadge(g, PANEL.x + 18, PANEL.y + PANEL.h + 2, cutBadgeK, 11, GREEN_BG, GREEN);
      tickBadge(g, PANEL.x + PANEL.w - 8, PANEL.y + PANEL.h - 8, cutBadgeK, 7, GREEN_BG, GREEN);
    }
  }

  function lever(g, kPull) {
    ln(g, LEVER.x + 8, LEVER.top, LEVER.x + 2, 0, 2.2);
    ln(g, LEVER.x + LEVER.w - 8, LEVER.top, LEVER.x + LEVER.w - 2, 0, 2.2);
    rr(g, LEVER.x, LEVER.top - 14, LEVER.w, 14, 3);
    inkFill(g, C.paper, 1.5);
    rr(g, LEVER.x + 6, LEVER.top - LEVER.h, LEVER.w - 12, LEVER.h, 4);
    inkFill(g, C.paper, 1.5);
    // 手柄：REST_ANG=上（待命），REST_ANG+PULL_SWING=下（切断）
    const ang = REST_ANG + PULL_SWING * E.in(clamp(kPull, 0, 1));
    const hx = PIVOT.x + Math.sin(ang) * HANDLE, hy = PIVOT.y - Math.cos(ang) * HANDLE;
    ln(g, PIVOT.x, PIVOT.y, hx, hy, 3, C.ink);
    g.beginPath(); g.arc(hx, hy, 4.5, 0, Math.PI * 2); g.fillStyle = RED; g.fill();
    g.lineWidth = 1.4; g.strokeStyle = C.ink; g.stroke();
    return [hx, hy];
  }

  SC['bms-tick-guard'] = {
    dur: 6.5,
    width: 400,
    label: '保护员盯着电压表：指针越过红线后连续三拍计数，第三拍拉下切断杆；电压针只是高位略回落，充电电流条归零后才亮起“已切断”。',
    draw(g, S) {
      const T = S.on ? S.u * this.dur : -1;
      const t = S.t;
      let x = HOME, gait = { ph: 0, amp: 0 };
      let pose = breathe(P({ hF: [12, -60], hB: [-4, -52] }), t);

      let kTrip = 0, tickN = 0, kPull = 0, cutBadgeK = 0, fadeK = 1;

      if (T < 0) {
        pose = mix(pose, P({ hF: [10, -96], head: [7, -116], hB: [-4, -54] }), pulse(t, 5.5, 2, 2.2));
      } else {
        fadeK = 1 - seg(T, this.dur - 0.5, this.dur);
        kTrip = seg(T, 0.2, 0.5);
        tickN = T >= 2.7 ? 3 : T >= 1.7 ? 2 : T >= 0.8 ? 1 : 0;
        // 走动：2.5–3.1 去杆，5.0–5.9 回位
        const ws = T < 3.1 ? walkSeg(T, 2.5, 3.1, HOME, AT) : walkSeg(T, 5.0, 5.9, AT, HOME);
        x = ws.x; gait = ws;
        kPull = seg(T, 3.45, 3.85);
        cutBadgeK = seg(T, 4.3, 4.7);

        // 看表（数拍）：身体微前倾，手指向表（本地坐标，sx=-1 时镜像指向左）
        const watch = E.soft(seg(T, 0.5, 0.9)) * (1 - E.soft(seg(T, 2.5, 2.9)));
        pose = mix(pose, P({ hF: [30, -100], hB: [-4, -54], head: [9, -115], chest: [4, -89] }), watch);
        // 伸手够杆（先行），再抓杆：手握杆身中段——杆头弧正好扫过肩点，握中点让目标始终离肩 20+，IK 不翻面
        const restAng = REST_ANG;
        const GRIP_R = HANDLE * 0.55;
        const rx = PIVOT.x + Math.sin(restAng) * GRIP_R, ry = PIVOT.y - Math.cos(restAng) * GRIP_R;
        const reach = E.in(seg(T, 3.08, 3.28)) * (1 - E.soft(seg(T, 3.3, 3.5)));
        pose = mix(pose, P({ hF: lp([rx, ry], x, 0, 1), hB: [-6, -56], head: [6, -114], chest: [3, -90], ef: 0.45 }), reach);
        // 抓杆：右手跟住杆身
        const pullAng = restAng + PULL_SWING * E.in(clamp(kPull, 0, 1));   // 与 lever() 同一摆幅，手握在杆上
        const hx = PIVOT.x + Math.sin(pullAng) * GRIP_R, hy = PIVOT.y - Math.cos(pullAng) * GRIP_R;
        const grip = E.soft(seg(T, 3.25, 3.45)) * (1 - E.soft(seg(T, 4.75, 5.0)));   // 回家前必须先松手
        pose = mix(pose, P({ hF: lp([hx, hy], x, 0, 1), hB: [-6, -56], head: [6, -114], chest: [4, -90], ef: 0.45 }), grip);
        // 确认点头（小幅，不起跳）
        const nod = E.soft(seg(T, 4.55, 4.75)) * (1 - E.soft(seg(T, 4.9, 5.1)));
        pose = mix(pose, P({ head: [5, -108], chest: [3, -88] }), nod);
      }
      pose = legs(pose, gait.ph, gait.amp, { arms: false, stride: gait.stride || 26 });

      lever(g, T >= 0 ? kPull * fadeK : 0);
      const kI = T >= 0 ? (1 - E.in(seg(T, 3.65, 4.25))) * fadeK : 1;   // 空闲时在充电，电流条是满的
      const kV = T >= 0 ? seg(T, 4.2, 4.7) * fadeK : 0;                 // 电压回落跟在电流归零之后
      gauge(g, kTrip * (T >= 0 ? fadeK : 1), kV, T >= 0 ? tickN : 0, cutBadgeK * fadeK, T >= 0 ? fadeK : 1, kI);
      const sx = T < 0 ? -1 : (T >= 2.5 && T < 5.0 ? 1 : -1);   // 看守/回家面向表；去拉杆与操作期间面向杠杆
      fig(g, pose, x, 0, { sx, wave: S.wave, wt: S.wt });
      if (T >= 0) {
        sparks(g, PIVOT.x + 10, LEVER.top - 10, seg(T, 3.85, 4.3) * fadeK, 12, 5);
      }
    },
  };
})();
