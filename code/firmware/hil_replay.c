/* 故障注入与 DTC 快照回放。只调用现有 bms_tick，不改保护逻辑。
 *
 * 构建运行：
 *   gcc -std=c99 -Wall -Wextra -Werror -o hil_replay bms.c hil_replay.c && ./hil_replay
 *
 * 阈值与 test_bms.c 的教学配置相同，是锂电示例，不是钠离子窗口。
 * 骨架没有开线检测。0 mV 会被现有状态机记成欠压，这是误诊演示，不是开线 DTC。
 */
#include "bms.h"

#include <stdio.h>

#define CELLS 4

static const BmsConfig CFG = {
    .ovp_mv = 4250,        .ovp_release_mv = 4150,  .ovp_debounce = 3,
    .uvp_mv = 2800,        .uvp_release_mv = 3000,  .uvp_debounce = 3,
    .ocd_ma = 10000,                                .ocd_debounce = 5,
    .scd_ma = 30000,
    .ot_c10 = 600,
    .balance_start_mv = 3600,
    .balance_delta_mv = 30,
    .full_mv = 4180,
    .full_cutoff_ma = 500,
    .sleep_idle_ticks = 10,
};

static int g_fails;

static BmsInputs nominal(void) {
    BmsInputs in = {0};
    int i;
    for (i = 0; i < CELLS; i++) in.cell_mv[i] = 3700;
    in.current_ma = 0;
    in.temp_c10 = 250;
    in.charger_present = false;
    return in;
}

static void expect(int cond, const char *msg) {
    if (cond) {
        printf("ok %s\n", msg);
    } else {
        printf("FAIL %s\n", msg);
        g_fails++;
    }
}

static void show(const char *tag, const Bms *b, const BmsInputs *in) {
    if (b->snapshot_valid) {
        printf("%s tick=%lu state=%s fault=%s snap=%s cell2=%ld I=%ld\n",
               tag,
               (unsigned long)b->tick,
               bms_state_name(b->state),
               bms_fault_name(b->active_fault),
               bms_fault_name(b->snapshot.code),
               (long)b->snapshot.cell_mv[2],
               (long)b->snapshot.current_ma);
    } else {
        printf("%s tick=%lu state=%s fault=%s snap=- live_cell2=%ld live_I=%ld\n",
               tag,
               (unsigned long)b->tick,
               bms_state_name(b->state),
               bms_fault_name(b->active_fault),
               (long)in->cell_mv[2],
               (long)in->current_ma);
    }
}

static void reach_charge(Bms *b, BmsInputs *in) {
    in->charger_present = true;
    in->current_ma = 2000;
    bms_tick(b, in);
    bms_tick(b, in);
}

static void case_ovp_then_scd(void) {
    Bms b;
    BmsInputs in = nominal();

    puts("--- 案例 A：过充去抖后冻结第一现场，随后短路不得覆盖 ---");
    bms_init(&b, &CFG, CELLS, 50);
    reach_charge(&b, &in);
    expect(b.state == ST_CHARGE, "两拍后进入充电");

    in.cell_mv[2] = 4300;
    bms_tick(&b, &in);
    bms_tick(&b, &in);
    show("去抖未满", &b, &in);
    expect(b.state != ST_FAULT, "超限两拍仍未动作");

    bms_tick(&b, &in);
    show("过充冻结", &b, &in);
    expect(b.state == ST_FAULT && b.snapshot.code == FC_OVP, "第三拍记过充快照");
    expect(b.snapshot.cell_mv[2] == 4300 && b.snapshot.current_ma == 2000,
           "快照保住 4300 mV 与 2000 mA");

    in.cell_mv[2] = 3700;
    in.current_ma = -40000;
    bms_tick(&b, &in);
    show("短路之后", &b, &in);
    expect(b.active_fault == FC_SCD, "显示主故障升级为短路");
    expect(b.snapshot_valid && b.snapshot.code == FC_OVP, "第一现场仍是过充");
    expect(b.snapshot.cell_mv[2] == 4300 && b.snapshot.current_ma == 2000,
           "回放读到的仍是过充那一帧");
}

static void case_zero_reads_as_uvp(void) {
    Bms b;
    BmsInputs in = nominal();
    int i;

    puts("--- 案例 B：脚本把一串打成 0 mV，骨架会记成欠压 ---");
    bms_init(&b, &CFG, CELLS, 50);
    reach_charge(&b, &in);
    in.cell_mv[0] = 0;
    for (i = 0; i < CFG.uvp_debounce; i++) bms_tick(&b, &in);
    show("零压读数", &b, &in);
    expect(b.state == ST_FAULT && b.snapshot.code == FC_UVP, "0 mV 被记成欠压");
    expect(b.snapshot.cell_mv[0] == 0 && b.snapshot.cell_mv[1] == 3700,
           "快照留下 0 mV 和其余串的 3700 mV");
    puts("说明：本骨架没有开线标志。真实验台要另注入断线，并核对开线 DTC，不能只看这条欠压。");
}

int main(void) {
    case_ovp_then_scd();
    case_zero_reads_as_uvp();
    if (g_fails) {
        printf("\n%d check(s) failed\n", g_fails);
        return 1;
    }
    puts("\nHIL REPLAY PASSED");
    return 0;
}
