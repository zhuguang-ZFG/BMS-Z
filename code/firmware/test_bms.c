/* BMS 状态机场景测试（无框架，assert 驱动）。
 *
 * 构建运行：
 *   gcc -std=c99 -Wall -Wextra -Werror -o test_bms bms.c test_bms.c && ./test_bms
 *
 * 每个 test_* 对应教程里的一条工程纪律或保护行为。
 */
#include "bms.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

#define CELLS 4

static const BmsConfig CFG = {
    .ovp_mv = 4250,        .ovp_release_mv = 4150,  .ovp_debounce = 3,
    .uvp_mv = 2800,        .uvp_release_mv = 3000,  .uvp_debounce = 3,
    .ocd_ma = 10000,                                .ocd_debounce = 5,
    .scd_ma = 30000,
    .ot_c10 = 600,                                /* 60.0°C */
    .balance_start_mv = 3600,
    .balance_delta_mv = 30,
    .full_mv = 4180,
    .full_cutoff_ma = 500,                        /* 0.05C 截止示例 */
    .sleep_idle_ticks = 10,
};

static BmsInputs nominal(void) {
    BmsInputs in = {0};
    for (int i = 0; i < CELLS; i++) in.cell_mv[i] = 3700;
    in.current_ma = 0;
    in.temp_c10 = 250;
    in.charger_present = false;
    return in;
}

static Bms make_bms(void) {
    Bms b;
    bms_init(&b, &CFG, CELLS, 50);
    return b;
}

static Bms make_bms_cfg(const BmsConfig *cfg) {
    Bms b;
    bms_init(&b, cfg, CELLS, 50);
    return b;
}

static void test_init_goes_standby(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    puts("ok init->standby");
}

static void test_charge_and_full_reset(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);

    /* CV 截止：电压高位 + 电流衰减 → 满充校准 SOC=100% */
    for (int i = 0; i < CELLS; i++) in.cell_mv[i] = 4190;
    in.current_ma = 300;                          /* < full_cutoff_ma */
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    assert(b.soc_pct == 100);
    puts("ok charge->full reset");
}

static void test_ovp_debounce_and_fault_snapshot(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);

    /* 超限 2 拍 < 去抖 3 拍：不应动作（躲开毛刺）。
     * 注意此时压差满足均衡入口，状态可能是 BALANCE——保护去抖与状态机无关 */
    in.cell_mv[2] = 4300;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    assert(b.state != ST_FAULT);
    assert(b.active_fault == FC_NONE);

    /* 第 3 拍：触发。快照必须冻结现场 */
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT);
    assert(b.active_fault == FC_OVP);
    /* 方向性断口：OVP 断充电留放电——恢复靠放电把电压拉到回差以下 */
    assert(b.charge_mos_on == false);
    assert(b.discharge_mos_on == true);
    assert(b.snapshot_valid);
    assert(b.snapshot.code == FC_OVP);
    assert(b.snapshot.cell_mv[2] == 4300);
    assert(b.snapshot.current_ma == 2000);
    puts("ok ovp debounce+snapshot");
}

static void test_any_state_can_enter_fault(void) {
    /* 纪律 3：从 DISCHARGE 态（不是充电态）触发 OVP 也必须立即进 FAULT */
    Bms b = make_bms();
    BmsInputs in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -3000;                        /* 放电 */
    bms_tick(&b, &in);
    assert(b.state == ST_DISCHARGE);

    in.cell_mv[1] = 4300;                         /* 放电中电压异常高（采样失效场景） */
    for (int i = 0; i < CFG.ovp_debounce; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT);
    assert(b.active_fault == FC_OVP);
    puts("ok any-state->fault");
}

static void test_ovp_recovery(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    in.cell_mv[0] = 4300;
    for (int i = 0; i < CFG.ovp_debounce; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT);

    /* 放电把电压拉到恢复阈值以下 → 回 STANDBY */
    in.charger_present = false;
    in.current_ma = -1000;
    in.cell_mv[0] = 4100;
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    assert(b.active_fault == FC_NONE);
    puts("ok ovp recovery");
}

static void test_uvp_recovery_requires_charger(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -2000;
    bms_tick(&b, &in);
    assert(b.state == ST_DISCHARGE);

    in.cell_mv[3] = 2700;
    for (int i = 0; i < CFG.uvp_debounce; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT);
    assert(b.active_fault == FC_UVP);

    /* 无充电器，即使电压回升也不恢复（防放电-恢复-再放电死循环） */
    in.current_ma = 0;
    in.cell_mv[3] = 3100;
    for (int i = 0; i < 5; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT);

    /* 插上充电器 + 电压回恢复值 → 恢复 */
    in.charger_present = true;
    in.current_ma = 1000;
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    puts("ok uvp recovery needs charger");
}

static void test_scd_immediate_and_latched(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -50000;                       /* 50A 短路 */
    bms_tick(&b, &in);                            /* 一拍即断，无去抖 */
    assert(b.state == ST_FAULT);
    assert(b.active_fault == FC_SCD);
    assert(b.fault_latched);

    /* 锁存：电流先不归零，不能恢复 */
    in.current_ma = -20000;
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT);

    /* 卸载（电流归零）→ 解除锁存 → 恢复 */
    in.current_ma = 0;
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    puts("ok scd immediate+latched");
}

static void test_balance_entry_and_exit(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);

    /* 充电末端：最高串 3700 ≥ 3600，压差 60 ≥ 30 → 进均衡 */
    in.cell_mv[0] = 3700;
    in.cell_mv[1] = 3680;
    in.cell_mv[2] = 3640;
    in.cell_mv[3] = 3640;
    bms_tick(&b, &in);                            /* 迁移拍：CHARGE → BALANCE */
    assert(b.state == ST_BALANCE);
    bms_tick(&b, &in);                            /* 执行拍：置均衡开关 */
    assert(b.balance_on[0] && b.balance_on[1]);
    assert(!b.balance_on[2] && !b.balance_on[3]);

    /* 压差收敛到一半以下（<15mV）→ 退出均衡回充电 */
    in.cell_mv[1] = 3690;
    in.cell_mv[2] = 3690;
    in.cell_mv[3] = 3690;
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);
    assert(!b.balance_on[0]);
    puts("ok balance entry/exit");
}

static void test_sleep_and_wakeup(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    for (uint32_t i = 0; i <= CFG.sleep_idle_ticks; i++) bms_tick(&b, &in);
    assert(b.state == ST_SLEEP);
    assert(b.charge_mos_on == false);
    assert(b.discharge_mos_on == false);

    in.charger_present = true;                    /* 插充电器唤醒 */
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    puts("ok sleep/wakeup");
}

static void test_first_snapshot_not_overwritten(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    in.cell_mv[0] = 4300;
    for (int i = 0; i < CFG.ovp_debounce; i++) bms_tick(&b, &in);
    uint32_t first_tick = b.snapshot.tick;

    in.cell_mv[1] = 4300;                         /* 故障保持期间再来一条 */
    for (int i = 0; i < 3; i++) bms_tick(&b, &in);
    assert(b.snapshot.tick == first_tick);        /* 第一现场不被覆盖 */
    puts("ok first-snapshot kept");
}

/* 回归：短路锁存不得被"充电电流"解除。
 * 曾经的写法是 `-current_ma < 100`——任何充电电流都满足，等于插上充电器
 * 就放行短路锁存，两拍后 MOS 重新闭合。卸载确认必须是双向窗口。 */
static void test_scd_latch_survives_charger_current(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -50000;                       /* 短路跳闸 */
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT && b.fault_latched);

    /* 充电器仍在灌 +2A：不是"已卸载"，锁存必须保持 */
    in.charger_present = true;
    in.current_ma = 2000;
    for (int i = 0; i < 5; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT);
    assert(b.active_fault == FC_SCD);
    assert(b.fault_latched);
    assert(b.charge_mos_on == false && b.discharge_mos_on == false);

    /* 真正卸载（电流归零）才允许恢复 */
    in.charger_present = false;
    in.current_ma = 0;
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    assert(!b.fault_latched);
    puts("ok scd latch survives charger current");
}

/* 回归：去抖配 0 的语义是"首次超限即动作"，不是"恒真误判 + 静默断开"。
 * 曾经的写法 `cnt >= debounce` 在 debounce=0 时恒真：每拍先误判进 FAULT，
 * 再被同一拍的 fault_cleared 放行并 return——状态停在 STANDBY，MOS 却永远
 * 合不上，且没有任何故障上报。 */
static void test_zero_debounce_is_immediate_not_broken(void) {
    BmsConfig cfg = CFG;
    cfg.ovp_debounce = 0;

    /* 正常电压 + 去抖 0：不得误判，MOS 必须能合上 */
    Bms b = make_bms_cfg(&cfg);
    BmsInputs in = nominal();
    for (int i = 0; i < 3; i++) bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    assert(b.active_fault == FC_NONE);
    assert(b.charge_mos_on && b.discharge_mos_on);

    /* 真超限：首拍即动作（去抖 0 = 不去抖，与短路分支语义一致） */
    in.cell_mv[0] = 4300;
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT);
    assert(b.active_fault == FC_OVP);
    assert(b.charge_mos_on == false && b.discharge_mos_on == true);   /* OVP 断充留放 */
    puts("ok zero debounce = immediate, not silent-off");
}

/* 回归：满充校准只认"CV 段衰减中的充电电流"。负载把电流拉成反向时
 * （充电器仍挂着），`current < cutoff` 对负值同样成立——不判 > 0 会把
 * 放电误判成满充、SOC 错置 100%。且净电流反向后状态机不得停在 CHARGE。 */
static void test_full_reset_requires_positive_current(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);

    /* 电压已到满充阈值，但负载大过充电器 → 净电流反向：不得校准 SOC */
    for (int i = 0; i < CELLS; i++) in.cell_mv[i] = 4190;
    in.current_ma = -800;                         /* |负载| > 充电器输出 */
    bms_tick(&b, &in);
    assert(b.soc_pct != 100);
    assert(b.state == ST_DISCHARGE);              /* 反向即放电，别赖在 CHARGE */
    puts("ok full reset requires positive current");
}

/* 回归：CHARGE 中电流归零（充电器限流/拔枪瞬间）不迁移、不误判满充；
 * 恢复正向充电电流后继续留在 CHARGE。 */
static void test_charge_zero_current_stays(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);

    in.current_ma = 0;
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);
    assert(b.soc_pct != 100);
    in.current_ma = 1500;
    bms_tick(&b, &in);
    assert(b.state == ST_CHARGE);
    puts("ok charge zero current stays");
}

/* 回归：断口方向必须保住"本故障自己的恢复路径"（教程 circuits/01 §2.2 与 §4 自测答案 3）。
 * 曾一律双断：UVP 的恢复条件是"插充电器 + 电压抬回恢复值"，但充电 MOS
 * 也被断开时充电器灌不进电——硬件上永远恢复不了，等于锁死。 */
static void test_fault_cut_direction_preserves_recovery(void) {
    /* UVP：断放电、留充电 */
    Bms b = make_bms();
    BmsInputs in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -2000;
    bms_tick(&b, &in);
    in.cell_mv[3] = 2700;
    for (int i = 0; i < CFG.uvp_debounce; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT && b.active_fault == FC_UVP);
    assert(b.charge_mos_on == true);              /* 恢复路径必须导通 */
    assert(b.discharge_mos_on == false);

    /* OCD：断放电、留充电 */
    b = make_bms();
    in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -15000;
    for (int i = 0; i < CFG.ocd_debounce; i++) bms_tick(&b, &in);
    assert(b.state == ST_FAULT && b.active_fault == FC_OCD);
    assert(b.charge_mos_on == true);
    assert(b.discharge_mos_on == false);

    /* OT：两路全断（任何方向的电流都在继续加热） */
    b = make_bms();
    in = nominal();
    bms_tick(&b, &in);
    in.temp_c10 = 650;
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT && b.active_fault == FC_OT);
    assert(b.charge_mos_on == false && b.discharge_mos_on == false);

    /* SCD：两路全断且锁存（短路可能涉及内部损伤，保守处置） */
    b = make_bms();
    in = nominal();
    bms_tick(&b, &in);
    in.current_ma = -50000;
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT && b.active_fault == FC_SCD);
    assert(b.charge_mos_on == false && b.discharge_mos_on == false);
    puts("ok fault cut direction preserves recovery");
}

/* 回归：BALANCE 中净电流反向（负载大过充电器）必须停均衡转 DISCHARGE，
 * 别一边放电一边烧均衡电阻。 */
static void test_balance_exits_on_reversed_current(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    in.cell_mv[0] = 3700;
    in.cell_mv[1] = 3680;
    in.cell_mv[2] = 3640;
    in.cell_mv[3] = 3640;
    bms_tick(&b, &in);
    assert(b.state == ST_BALANCE);
    bms_tick(&b, &in);
    assert(b.balance_on[0]);

    in.current_ma = -800;                          /* 净电流反向 */
    bms_tick(&b, &in);
    assert(b.state == ST_DISCHARGE);
    assert(!b.balance_on[0] && !b.balance_on[1]);
    puts("ok balance exits on reversed current");
}

/* 回归：名称查询必须是全函数——任何越界值都落到 "?"，不得读到表外。
 * 旧判据 `s < ST_COUNT` / `f <= FC_OT` 的成败取决于枚举底层类型是否带符号：
 * GCC 对全非负枚举取 unsigned（-1 转成大正数，恰好落在界外），MSVC 取 int
 * （-1 < ST_COUNT 为真 → 读 names[-1]）。改成无符号比较后两种编译器一致。
 * 注意：本测试在 GCC 上跑旧代码也会通过，它锁的是契约、防的是 MSVC 路径。 */
static void test_name_lookup_is_total(void) {
    assert(strcmp(bms_state_name((BmsState)-1), "?") == 0);
    assert(strcmp(bms_state_name((BmsState)ST_COUNT), "?") == 0);
    assert(strcmp(bms_fault_name((FaultCode)-1), "?") == 0);
    assert(strcmp(bms_fault_name((FaultCode)(FC_OT + 1)), "?") == 0);
    /* 合法值不受影响 */
    assert(strcmp(bms_state_name(ST_INIT), "INIT") == 0);
    assert(strcmp(bms_state_name(ST_FAULT), "FAULT") == 0);
    assert(strcmp(bms_fault_name(FC_NONE), "NONE") == 0);
    assert(strcmp(bms_fault_name(FC_OT), "OT") == 0);
    puts("ok name lookup total");
}

static void test_init_clamps_cell_count(void) {
    /* cell_count 是 uint8_t，调用方传 255 也必须被钳到 BMS_MAX_CELLS，
     * 否则 cell_max/cell_min 会读出 cell_mv 数组之外 */
    Bms b;
    bms_init(&b, &CFG, 255, 50);
    assert(b.cell_count == BMS_MAX_CELLS);
    /* 钳位后的串数要真能跑：16 串全部在窗口内，不越界也不误保护 */
    BmsInputs in = {0};
    for (int i = 0; i < BMS_MAX_CELLS; i++) in.cell_mv[i] = 3700;
    in.temp_c10 = 250;
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY);
    assert(b.active_fault == FC_NONE);
    puts("ok init clamps cell_count");
}

/* 故障态仍须检测新短路；升级后第一现场与短路锁存各守各的生命周期。 */
static void test_fault_escalates_to_scd(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.cell_mv[0] = 4300;
    for (int i = 0; i < CFG.ovp_debounce; i++) bms_tick(&b, &in);
    uint32_t first_tick = b.snapshot.tick;
    in.current_ma = -50000;
    bms_tick(&b, &in);
    assert(b.active_fault == FC_SCD && b.fault_latched);
    assert(!b.charge_mos_on && !b.discharge_mos_on);
    assert(b.snapshot.code == FC_OVP && b.snapshot.tick == first_tick);

    in.current_ma = 2000;                 /* 充电电流不得解锁，OVP 也不得覆盖 SCD */
    for (int i = 0; i < 6; i++) bms_tick(&b, &in);
    assert(b.active_fault == FC_SCD && b.fault_latched);
    assert(!b.charge_mos_on && !b.discharge_mos_on);
    in.current_ma = 0;
    bms_tick(&b, &in);
    assert(!b.fault_latched && b.active_fault == FC_OVP);
    assert(b.state == ST_FAULT && !b.charge_mos_on && b.discharge_mos_on);
    puts("ok fault escalates to SCD without losing snapshot or OVP");
}

static void test_simultaneous_voltage_faults_recover_independently(void) {
    for (int first = 0; first < 2; first++) {
        Bms b = make_bms();
        BmsInputs in = nominal();
        in.cell_mv[0] = 4300;
        in.cell_mv[1] = 2700;
        for (int i = 0; i < 3; i++) bms_tick(&b, &in);
        assert(b.state == ST_FAULT);
        assert(b.fault_mask == (FM_OVP | FM_UVP));
        assert(!b.charge_mos_on && !b.discharge_mos_on);
        /* 都回到触发与释放阈值之间：两项都须保持，不可只看当拍是否超限 */
        in.cell_mv[0] = 4200;
        in.cell_mv[1] = 2900;
        bms_tick(&b, &in);
        assert(!b.charge_mos_on && !b.discharge_mos_on);
        if (first == 0) {
            in.cell_mv[0] = 4100;
            bms_tick(&b, &in);
            assert(b.active_fault == FC_UVP && b.charge_mos_on && !b.discharge_mos_on);
        } else {
            in.cell_mv[1] = 3100;
            in.charger_present = true;
            bms_tick(&b, &in);
            assert(b.active_fault == FC_OVP && !b.charge_mos_on && b.discharge_mos_on);
        }
        assert(b.state == ST_FAULT);
        in.cell_mv[0] = 4100;
        in.cell_mv[1] = 3100;
        in.charger_present = true;
        bms_tick(&b, &in);
        assert(b.state == ST_STANDBY && b.active_fault == FC_NONE);
        assert(b.fault_mask == FM_NONE && b.level == FL_NONE);
        bms_tick(&b, &in);
        assert(b.charge_mos_on && b.discharge_mos_on);
    }
    puts("ok simultaneous OVP/UVP recover independently in either order");
}

static void test_ot_not_masked_by_ovp(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.cell_mv[0] = 4300;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    in.temp_c10 = 700;                    /* 与 OVP 去抖到期同拍 */
    bms_tick(&b, &in);
    assert(b.active_fault == FC_OT);
    assert(!b.charge_mos_on && !b.discharge_mos_on);
    in.temp_c10 = 570;                    /* 已不超温，但尚未满足 5°C 回差 */
    bms_tick(&b, &in);
    assert(b.active_fault == FC_OT && !b.discharge_mos_on);
    in.temp_c10 = 540;
    bms_tick(&b, &in);
    assert(b.active_fault == FC_OVP && !b.charge_mos_on && b.discharge_mos_on);
    puts("ok OT is not masked by OVP and keeps its hysteresis");
}

static void test_debounce_continues_during_fault_and_recovery(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.temp_c10 = 700;
    bms_tick(&b, &in);
    in.current_ma = -15000;
    for (int i = 0; i < CFG.ocd_debounce - 1; i++) bms_tick(&b, &in);
    in.temp_c10 = 250;                    /* 过流确认与过温恢复同拍 */
    bms_tick(&b, &in);
    assert(b.state == ST_FAULT && b.active_fault == FC_OCD);
    assert(b.charge_mos_on && !b.discharge_mos_on);

    b = make_bms();
    in = nominal();
    in.temp_c10 = 700;
    bms_tick(&b, &in);
    in.cell_mv[0] = 4300;
    bms_tick(&b, &in);                    /* OVP 第 1 拍 */
    in.temp_c10 = 250;
    bms_tick(&b, &in);                    /* OVP 第 2 拍，OT 已恢复 */
    bms_tick(&b, &in);                    /* 第 3 拍必须动作，不能清零后重数 */
    assert(b.state == ST_FAULT && b.active_fault == FC_OVP);
    puts("ok debounce continues through fault and recovery");
}

static void test_debounce_saturates_and_scd_handles_min_current(void) {
    BmsConfig cfg = CFG;
    cfg.ovp_debounce = UINT8_MAX;
    Bms b = make_bms_cfg(&cfg);
    BmsInputs in = nominal();
    in.cell_mv[0] = 4300;
    for (int i = 0; i < 300; i++) bms_tick(&b, &in);
    assert(b.active_fault == FC_OVP && b.cnt_ovp == UINT8_MAX);
    assert(!b.charge_mos_on);
    in.current_ma = INT32_MIN;
    bms_tick(&b, &in);
    assert(b.active_fault == FC_SCD && b.fault_latched);
    assert(!b.charge_mos_on && !b.discharge_mos_on);
    puts("ok debounce saturates and INT32_MIN trips SCD");
}

/* 充电方向与充电器状态必须先于均衡／满充条件判断。 */
static void test_charge_activity_takes_priority_over_balance(void) {
    const struct {
        bool charger;
        int32_t current;
        BmsState expected;
    } cases[] = {
        {true,  -800, ST_DISCHARGE},
        {false, -800, ST_DISCHARGE},
        {false,  200, ST_STANDBY},
        {false,    0, ST_STANDBY},
        {true,     0, ST_CHARGE},
    };
    for (unsigned k = 0; k < sizeof(cases) / sizeof(cases[0]); k++) {
        Bms b = make_bms();
        BmsInputs in = nominal();
        in.charger_present = true;
        in.current_ma = 2000;
        bms_tick(&b, &in);
        bms_tick(&b, &in);
        assert(b.state == ST_CHARGE);
        for (int i = 0; i < CELLS; i++) in.cell_mv[i] = 4130;
        in.cell_mv[0] = 4190;         /* 电压与压差满足均衡入口 */
        in.charger_present = cases[k].charger;
        in.current_ma = cases[k].current;
        bms_tick(&b, &in);
        assert(b.state == cases[k].expected);
        assert(b.soc_pct == 50);
        for (int i = 0; i < CELLS; i++) assert(!b.balance_on[i]);
    }
    puts("ok charge activity takes priority over balance");
}

static void test_balance_rechecks_activity_and_voltage_floor(void) {
    const struct {
        bool charger;
        int32_t current, vmax, delta;
        BmsState expected;
    } cases[] = {
        {true,  -800, 3700, 60, ST_DISCHARGE},
        {true,  -800, 3700, 10, ST_DISCHARGE},  /* 与压差收敛同时发生 */
        {false,    0, 3700, 60, ST_STANDBY},
        {false,    0, 3700, 10, ST_STANDBY},
        {false,  200, 3700, 60, ST_STANDBY},
        {true,     0, 3700, 60, ST_CHARGE},
        {true,  2000, 3500, 60, ST_CHARGE},    /* 压差仍大，但已非充电末端 */
    };
    for (unsigned k = 0; k < sizeof(cases) / sizeof(cases[0]); k++) {
        Bms b = make_bms();
        BmsInputs in = nominal();
        in.charger_present = true;
        in.current_ma = 2000;
        in.cell_mv[1] = 3640;
        for (int i = 0; i < 4; i++) bms_tick(&b, &in);
        assert(b.state == ST_BALANCE && b.balance_on[0]);
        in.charger_present = cases[k].charger;
        in.current_ma = cases[k].current;
        for (int i = 0; i < CELLS; i++) in.cell_mv[i] = cases[k].vmax;
        in.cell_mv[1] -= cases[k].delta;
        bms_tick(&b, &in);
        assert(b.state == cases[k].expected);
        for (int i = 0; i < CELLS; i++) assert(!b.balance_on[i]);
    }
    puts("ok balance stops on lost activity or low voltage in the same tick");
}

static void test_full_reset_requires_present_charger(void) {
    Bms b = make_bms();
    BmsInputs in = nominal();
    in.charger_present = true;
    in.current_ma = 2000;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    for (int i = 0; i < CELLS; i++) in.cell_mv[i] = 4190;
    in.current_ma = 300;
    in.charger_present = false;       /* 拔枪后采样仍有残余正电流 */
    bms_tick(&b, &in);
    assert(b.state == ST_STANDBY && b.soc_pct == 50);
    puts("ok absent charger cannot trigger a full reset");
}

int main(void) {
    test_charge_activity_takes_priority_over_balance();
    test_balance_rechecks_activity_and_voltage_floor();
    test_full_reset_requires_present_charger();
    test_fault_escalates_to_scd();
    test_simultaneous_voltage_faults_recover_independently();
    test_ot_not_masked_by_ovp();
    test_debounce_continues_during_fault_and_recovery();
    test_debounce_saturates_and_scd_handles_min_current();
    test_init_goes_standby();
    test_charge_and_full_reset();
    test_ovp_debounce_and_fault_snapshot();
    test_any_state_can_enter_fault();
    test_ovp_recovery();
    test_uvp_recovery_requires_charger();
    test_scd_immediate_and_latched();
    test_balance_entry_and_exit();
    test_sleep_and_wakeup();
    test_first_snapshot_not_overwritten();
    test_scd_latch_survives_charger_current();
    test_zero_debounce_is_immediate_not_broken();
    test_full_reset_requires_positive_current();
    test_charge_zero_current_stays();
    test_fault_cut_direction_preserves_recovery();
    test_balance_exits_on_reversed_current();
    test_name_lookup_is_total();
    test_init_clamps_cell_count();
    puts("\nALL BMS TESTS PASSED");
    return 0;
}
