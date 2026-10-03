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
    assert(b.charge_mos_on == false);
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

int main(void) {
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
    puts("\nALL BMS TESTS PASSED");
    return 0;
}
