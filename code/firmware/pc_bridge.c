/* PC 实验适配器：每行输入 4 路 mV、mA、0.1°C、充电器标志、SOC 百分数。
 * 只做输入校验和 JSON 输出，保护决策始终由 bms.c 执行。所有阈值为教学值。
 */
#include "bms.h"

#include <ctype.h>
#include <errno.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const BmsConfig CFG = {
    .ovp_mv = 4250, .ovp_release_mv = 4150, .ovp_debounce = 3,
    .uvp_mv = 2800, .uvp_release_mv = 3000, .uvp_debounce = 3,
    .ocd_ma = 10000, .ocd_debounce = 5, .scd_ma = 30000,
    .ot_c10 = 600, .balance_start_mv = 3600, .balance_delta_mv = 30,
    .full_mv = 4180, .full_cutoff_ma = 500, .sleep_idle_ticks = 10,
};

static bool parse_input(char *line, BmsInputs *in, uint8_t *soc) {
    long values[8];
    char *p = line;
    for (int i = 0; i < 8; ++i) {
        char *end;
        errno = 0;
        values[i] = strtol(p, &end, 10);
        if (end == p || errno == ERANGE) return false;
        if (*end && !isspace((unsigned char)*end)) return false;
        p = end;
    }
    while (isspace((unsigned char)*p)) ++p;
    if (*p) return false;
    for (int i = 0; i < 4; ++i) {
        if (values[i] < 0 || values[i] > 65535) return false;
        in->cell_mv[i] = (int32_t)values[i];
    }
    if (values[4] < INT32_MIN || values[4] > INT32_MAX ||
        values[5] < INT16_MIN || values[5] > INT16_MAX ||
        values[6] < 0 || values[6] > 1 || values[7] < 0 || values[7] > 100)
        return false;
    in->current_ma = (int32_t)values[4];
    in->temp_c10 = (int16_t)values[5];
    in->charger_present = values[6] != 0;
    *soc = (uint8_t)values[7];
    return true;
}

int main(void) {
    Bms b;
    char line[256];
    bms_init(&b, &CFG, 4, 70);
    while (fgets(line, sizeof(line), stdin)) {
        BmsInputs in = {0};
        uint8_t soc;
        if (!strchr(line, '\n') || !parse_input(line, &in, &soc)) {
            fputs("invalid input: expected eight bounded integers and newline\n", stderr);
            return 2;
        }
        b.soc_pct = soc;
        bms_tick(&b, &in);
        unsigned balance = 0;
        for (int i = 0; i < 4; ++i)
            if (b.balance_on[i]) balance |= 1u << i;
        printf("{\"tick\":%" PRIu32 ",\"state\":\"%s\",\"state_id\":%u,"
               "\"fault\":\"%s\",\"fault_mask\":%" PRIu32 ","
               "\"charge_on\":%u,\"discharge_on\":%u,\"balance_mask\":%u,"
               "\"soc_pct\":%u,\"snapshot_valid\":%u,\"snapshot_tick\":%" PRIu32 ","
               "\"snapshot_fault\":\"%s\",\"snapshot_current_ma\":%" PRId32 ","
               "\"snapshot_cell0_mv\":%" PRId32 "}\n",
               b.tick, bms_state_name(b.state), (unsigned)b.state,
               bms_fault_name(b.active_fault), b.fault_mask,
               (unsigned)b.charge_mos_on, (unsigned)b.discharge_mos_on, balance,
               (unsigned)b.soc_pct, (unsigned)b.snapshot_valid, b.snapshot.tick,
               bms_fault_name(b.snapshot.code), b.snapshot.current_ma,
               b.snapshot.cell_mv[0]);
        if (fflush(stdout) != 0) return 3;
    }
    return ferror(stdin) ? 2 : 0;
}
