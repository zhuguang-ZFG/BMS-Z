#include "bms.h"

#include <string.h>

static int32_t cell_max(const Bms *b, const BmsInputs *in) {
    int32_t m = in->cell_mv[0];
    for (uint8_t i = 1; i < b->cell_count; i++)
        if (in->cell_mv[i] > m) m = in->cell_mv[i];
    return m;
}

static int32_t cell_min(const Bms *b, const BmsInputs *in) {
    int32_t m = in->cell_mv[0];
    for (uint8_t i = 1; i < b->cell_count; i++)
        if (in->cell_mv[i] < m) m = in->cell_mv[i];
    return m;
}

static void take_snapshot(Bms *b, const BmsInputs *in, FaultCode code) {
    b->snapshot.tick = b->tick;
    b->snapshot.code = code;
    b->snapshot.current_ma = in->current_ma;
    b->snapshot.temp_c10 = in->temp_c10;
    b->snapshot.soc_pct = b->soc_pct;
    memcpy(b->snapshot.cell_mv, in->cell_mv, sizeof(in->cell_mv));
    b->snapshot_valid = true;
}

static void enter_fault(Bms *b, const BmsInputs *in, FaultCode code, bool latch) {
    b->active_fault = code;
    b->level = FL_TRIP;
    b->fault_latched = latch;
    if (!b->snapshot_valid)          /* 只保留第一现场，不被后续故障覆盖 */
        take_snapshot(b, in, code);
    b->state = ST_FAULT;             /* 纪律 3：任意状态直达故障态 */
    b->charge_mos_on = false;
    b->discharge_mos_on = false;
    memset(b->balance_on, 0, sizeof(b->balance_on));
}

/* 保护评估：与状态机解耦，每拍最先跑——任何状态下都能把人拉进故障态 */
static void eval_protections(Bms *b, const BmsInputs *in) {
    const BmsConfig *c = &b->cfg;
    int32_t vmax = cell_max(b, in);
    int32_t vmin = cell_min(b, in);
    int32_t dis_ma = -in->current_ma;    /* 放电电流幅值 */

    /* 短路：无去抖，立即断开且锁存（教程：SCD 是 μs 级硬件的活，软件这是兜底） */
    if (dis_ma > (int32_t)c->scd_ma) {
        enter_fault(b, in, FC_SCD, true);
        return;
    }
    /* 过充。去抖判据必须带 cnt > 0：否则 debounce 配 0 时"0 >= 0"恒真，
     * 每拍都先误判进故障、再被同一拍的 fault_cleared 立刻放行——状态看着是
     * STANDBY，MOS 却永远合不上（静默失效）。带 cnt > 0 后 debounce=0 的
     * 语义变成"首次超限即动作"，与短路分支一致。 */
    b->cnt_ovp = (vmax > c->ovp_mv && b->cnt_ovp < 255) ? b->cnt_ovp + 1 : 0;
    if (b->cnt_ovp > 0 && b->cnt_ovp >= c->ovp_debounce) { enter_fault(b, in, FC_OVP, false); return; }
    /* 过放 */
    b->cnt_uvp = (vmin < c->uvp_mv && b->cnt_uvp < 255) ? b->cnt_uvp + 1 : 0;
    if (b->cnt_uvp > 0 && b->cnt_uvp >= c->uvp_debounce) { enter_fault(b, in, FC_UVP, false); return; }
    /* 放电过流 */
    b->cnt_ocd = (dis_ma > (int32_t)c->ocd_ma && b->cnt_ocd < 255) ? b->cnt_ocd + 1 : 0;
    if (b->cnt_ocd > 0 && b->cnt_ocd >= c->ocd_debounce) { enter_fault(b, in, FC_OCD, false); return; }
    /* 过温：无去抖示例（量产按 FTTI 推导周期与确认时间） */
    if (in->temp_c10 > c->ot_c10) { enter_fault(b, in, FC_OT, false); return; }
}

/* 故障恢复：每类故障各写各的恢复条件（教程"保护三要素"之三） */
static bool fault_cleared(Bms *b, const BmsInputs *in) {
    int32_t vmax = cell_max(b, in);
    int32_t vmin = cell_min(b, in);
    int32_t dis_ma = -in->current_ma;

    switch (b->active_fault) {
    case FC_OVP:
        /* 电压回到恢复阈值以下（放电把电压拉下来了） */
        return vmax < b->cfg.ovp_release_mv;
    case FC_UVP:
        /* 恢复的前提是有能量进来：插充电器且电压被抬回恢复值 */
        return in->charger_present && vmin > b->cfg.uvp_release_mv;
    case FC_OCD:
        return dis_ma < (int32_t)(b->cfg.ocd_ma / 2);
    case FC_SCD:
        /* 锁存故障：必须先确认外部已卸载（电流归零），再清除。
         * 判据必须取双向窗口：短路是放电事件（current_ma 为负），若只写
         * `-current_ma < 100`，则任何充电电流（含充电器仍在灌流）都会让
         * 条件成立、把锁存放掉——等于"插上充电器就解除短路锁存"。
         * 这里不调 abs()：避免依赖 <stdlib.h>，也避开 INT32_MIN 取负溢出。 */
        if (in->current_ma > -100 && in->current_ma < 100) b->fault_latched = false;
        return !b->fault_latched;
    case FC_OT:
        return in->temp_c10 < b->cfg.ot_c10 - 50;   /* 5°C 回差 */
    default:
        return true;
    }
}

void bms_init(Bms *bms, const BmsConfig *cfg, uint8_t cell_count, uint8_t soc_pct) {
    memset(bms, 0, sizeof(*bms));
    bms->cfg = *cfg;
    bms->cell_count = (cell_count > BMS_MAX_CELLS) ? BMS_MAX_CELLS : cell_count;
    bms->soc_pct = soc_pct;
    bms->state = ST_INIT;
}

void bms_tick(Bms *b, const BmsInputs *in) {
    const BmsConfig *c = &b->cfg;
    int32_t vmax = cell_max(b, in);
    int32_t vmin = cell_min(b, in);

    b->tick++;

    /* 1. 保护永远最先评估（已处故障态时也需要刷新恢复条件） */
    if (b->state != ST_FAULT)
        eval_protections(b, in);
    if (b->state == ST_FAULT) {
        if (fault_cleared(b, in)) {
            b->active_fault = FC_NONE;
            b->level = FL_NONE;
            b->cnt_ovp = b->cnt_uvp = b->cnt_ocd = 0;
            b->state = ST_STANDBY;         /* 恢复回待机，重新决策 */
            return;                        /* 纪律：一拍只做一次迁移，下拍再决策 */
        } else {
            return;                        /* 故障未清除，保持断开 */
        }
    }

    /* 2. 状态机：所有正常迁移只发生在这里 */
    switch (b->state) {
    case ST_INIT:
        /* 自检占位：真实固件在这里做 ADC 自检 / 开线检测 / 参数 CRC */
        b->state = ST_STANDBY;
        break;

    case ST_STANDBY:
        b->charge_mos_on = true;
        b->discharge_mos_on = true;
        if (in->charger_present && in->current_ma > 0) {
            b->state = ST_CHARGE;
        } else if (in->current_ma < 0) {
            b->state = ST_DISCHARGE;
        } else if (++b->idle_ticks >= c->sleep_idle_ticks) {
            /* 进入动作与迁移同拍：休眠断开充放（勿等到下一拍才执行） */
            b->charge_mos_on = false;
            b->discharge_mos_on = false;
            b->state = ST_SLEEP;
        }
        break;

    case ST_CHARGE:
        b->idle_ticks = 0;
        if (vmax >= c->balance_start_mv && (vmax - vmin) >= c->balance_delta_mv) {
            b->state = ST_BALANCE;         /* 充电末端 + 压差够大 → 均衡 */
        } else if (vmax >= c->full_mv && in->current_ma > 0
                   && in->current_ma < (int32_t)c->full_cutoff_ma) {
            /* 满充校准：CV 截止 → SOC=100%。电流必须 > 0——负电流（负载把
             * 充电器顶成放电）同样满足 `< cutoff`，不挡会把放电误判成满充 */
            b->soc_pct = 100;
            b->state = ST_STANDBY;
        } else if (in->current_ma < 0) {
            b->state = ST_DISCHARGE;     /* 充电器挂着但净电流已反向：别停在 CHARGE */
        } else if (!in->charger_present) {
            b->state = ST_STANDBY;
        }
        break;

    case ST_BALANCE:
        /* 被动均衡：给高于最低串 delta 的所有串开放电开关。
         * 量产注意：多串要分时轮询 + 采样前关均衡等稳定（教程 3.2/详解③）。 */
        for (uint8_t i = 0; i < b->cell_count; i++)
            b->balance_on[i] = (in->cell_mv[i] - vmin) >= c->balance_delta_mv;
        if ((vmax - vmin) < c->balance_delta_mv / 2) {
            memset(b->balance_on, 0, sizeof(b->balance_on));
            b->state = ST_CHARGE;
        } else if (!in->charger_present) {
            memset(b->balance_on, 0, sizeof(b->balance_on));
            b->state = ST_STANDBY;
        }
        break;

    case ST_DISCHARGE:
        b->idle_ticks = 0;
        if (in->current_ma > 0)
            b->state = in->charger_present ? ST_CHARGE : ST_STANDBY;
        else if (in->current_ma == 0)
            b->state = ST_STANDBY;
        break;

    case ST_SLEEP:
        /* 教学示例：休眠断开充放路径；量产按产品定（有的只断充、保留放电唤醒） */
        b->charge_mos_on = false;
        b->discharge_mos_on = false;
        if (in->charger_present || in->current_ma != 0) {
            b->idle_ticks = 0;
            b->state = ST_STANDBY;
        }
        break;

    case ST_FAULT:
    case ST_COUNT:
        break;                             /* FAULT 已在上面处理 */
    }
}

const char *bms_state_name(BmsState s) {
    static const char *names[] = {
        "INIT", "STANDBY", "CHARGE", "DISCHARGE", "BALANCE", "FAULT", "SLEEP"
    };
    return (s < ST_COUNT) ? names[s] : "?";
}

const char *bms_fault_name(FaultCode f) {
    static const char *names[] = {"NONE", "OVP", "UVP", "OCD", "SCD", "OT"};
    return (f <= FC_OT) ? names[f] : "?";
}
