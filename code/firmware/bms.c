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

/* 断口方向按故障定：只切断"继续导通会阻碍本故障恢复"的那一路
 * （教程 circuits/01 §2.2 真值表与 §4 自测答案 3：两路全断的电池插上
 * 充电器也充不进电，直接锁死；阶段 1 §1.4 五大保护与 §1.9 答案 3：
 * OVP 断充电、UVP 断放电、OCP 断对应方向）。
 *   OVP 断充电——恢复靠放电把电压拉到回差以下，放电路径必须还在；
 *   UVP/OCD 断放电——恢复靠充电抬电压（UVP）或放电电流先归零（OCD），
 *     充电路径必须还在；
 *   SCD/OT 两路全断——短路可能已伤及内部，且 SCD 的恢复条件是外部卸载、
 *     不依赖任何通路保持导通（保护 IC 对短路只断放电，见 circuits/01 §2.2；
 *     本骨架双断是保守选择）；过温时任何方向的电流都在继续加热。
 * 多故障的禁止条件取并集：OVP + UVP 必须双断，不能为恢复一项而违反另一项。
 * active_fault 只选显示主因，不能拿它代替 fault_mask 决定断口。 */
static void enter_fault(Bms *b, const BmsInputs *in) {
    uint32_t mask = b->fault_mask;
    if (mask & FM_SCD)      b->active_fault = FC_SCD;
    else if (mask & FM_OT)  b->active_fault = FC_OT;
    else if (mask & FM_OVP) b->active_fault = FC_OVP;
    else if (mask & FM_UVP) b->active_fault = FC_UVP;
    else                   b->active_fault = FC_OCD;
    b->level = FL_TRIP;
    if (!b->snapshot_valid)          /* 只保留第一现场，不被后续故障覆盖 */
        take_snapshot(b, in, b->active_fault);
    b->charge_mos_on = !(mask & (FM_OVP | FM_SCD | FM_OT));
    b->discharge_mos_on = !(mask & (FM_UVP | FM_OCD | FM_SCD | FM_OT));
    memset(b->balance_on, 0, sizeof(b->balance_on));
}

/* 每项保护独立计时；饱和后保持 UINT8_MAX，不能在第 256 拍清零。
 * 配 0 表示首次超限即动作，正常输入仍须返回 false。 */
static bool debounced(bool exceeded, uint8_t *count, uint8_t threshold) {
    if (!exceeded) {
        *count = 0;
        return false;
    }
    if (*count < UINT8_MAX) ++*count;
    return *count >= threshold;
}

/* 已确认的故障一直保留到自己的恢复条件成立；其他故障的变化不能清除此位。 */
static void update_fault(Bms *b, FaultMask mask, bool trip, bool release) {
    if (trip) b->fault_mask |= (uint32_t)mask;
    else if (release) b->fault_mask &= ~(uint32_t)mask;
}

/* 每拍评估全部保护，包括故障态；不得命中一项就 return，后续项也须计时和恢复。 */
static void eval_protections(Bms *b, const BmsInputs *in) {
    const BmsConfig *c = &b->cfg;
    int32_t vmax = cell_max(b, in);
    int32_t vmin = cell_min(b, in);
    int64_t dis_ma = -(int64_t)in->current_ma;   /* 先扩位再取负，INT32_MIN 也不溢出 */

    /* SCD 无去抖且锁存；这里只演示软件兜底，μs 级切断仍由硬件完成。
     * 卸载窗口必须双向：充电器仍在灌流不代表已卸载，不能因此解锁。 */
    update_fault(b, FM_SCD, dis_ma > c->scd_ma,
                 in->current_ma > -100 && in->current_ma < 100);
    update_fault(b, FM_OVP, debounced(vmax > c->ovp_mv, &b->cnt_ovp, c->ovp_debounce),
                 vmax < c->ovp_release_mv);
    update_fault(b, FM_UVP, debounced(vmin < c->uvp_mv, &b->cnt_uvp, c->uvp_debounce),
                 in->charger_present && vmin > c->uvp_release_mv);
    update_fault(b, FM_OCD, debounced(dis_ma > c->ocd_ma, &b->cnt_ocd, c->ocd_debounce),
                 dis_ma < c->ocd_ma / 2);
    update_fault(b, FM_OT, in->temp_c10 > c->ot_c10,
                 in->temp_c10 < c->ot_c10 - 50);  /* 5°C 回差 */
    b->fault_latched = (b->fault_mask & FM_SCD) != 0;
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

    /* 1. 保护永远最先评估：记录全部未恢复故障，再合并断口并决定迁移。 */
    eval_protections(b, in);
    if (b->fault_mask != FM_NONE) {
        enter_fault(b, in);
        b->state = ST_FAULT;
        return;
    }
    if (b->state == ST_FAULT) {
        b->active_fault = FC_NONE;
        b->level = FL_NONE;
        /* 保留其他正在去抖的计数，不能因旧故障恢复而从头重数。 */
        b->state = ST_STANDBY;
        return;                            /* 一拍只迁移一次，下拍再决策和合闸 */
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
        /* 活动条件优先：压差再大，也不能把放电／拔枪／零电流引进均衡。 */
        if (in->current_ma < 0) {
            b->state = ST_DISCHARGE;
        } else if (!in->charger_present) {
            b->state = ST_STANDBY;
        } else if (in->current_ma == 0) {
            break;                        /* 等待恢复充电，不均衡也不校准满充 */
        } else if (vmax >= c->balance_start_mv && (vmax - vmin) >= c->balance_delta_mv) {
            b->state = ST_BALANCE;         /* 充电末端 + 压差够大 → 均衡 */
        } else if (vmax >= c->full_mv && in->current_ma > 0
                   && in->current_ma < (int32_t)c->full_cutoff_ma) {
            /* 满充校准：CV 截止 → SOC=100%。电流必须 > 0——负电流（负载把
             * 充电器顶成放电）同样满足 `< cutoff`，不挡会把放电误判成满充 */
            b->soc_pct = 100;
            b->state = ST_STANDBY;
        }
        break;

    case ST_BALANCE:
        /* 每拍重查充电条件，先关旧输出；退出优先于压差收敛，避免迁回错误状态。 */
        memset(b->balance_on, 0, sizeof(b->balance_on));
        if (in->current_ma < 0) {
            b->state = ST_DISCHARGE;
        } else if (!in->charger_present) {
            b->state = ST_STANDBY;
        } else if (in->current_ma == 0 || vmax < c->balance_start_mv
                   || (vmax - vmin) < c->balance_delta_mv / 2) {
            b->state = ST_CHARGE;
        } else {
            /* 被动均衡：仅在仍满足充电条件时给高于最低串 delta 的串开放电。
             * 量产需分时轮询，并在采样前关均衡等稳定（教程 3.2/详解③）。 */
            for (uint8_t i = 0; i < b->cell_count; i++)
                b->balance_on[i] = (in->cell_mv[i] - vmin) >= c->balance_delta_mv;
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
    /* 越界值必须落到 "?"——这是函数的契约。判据写成无符号比较，因为枚举的
     * 底层类型是实现定义的：GCC 对全非负枚举取 unsigned（-1 转成大正数，
     * 恰好落在界外，看着"没 bug"），MSVC 取 int（`s < ST_COUNT` 对 -1 为真，
     * 直接读 names[-1]）。本骨架按标准 C99 写、目标 MSVC 也可编译（CI 只
     * 自动验证 gcc，见 code/README.md），所以不能靠编译器选类型来兜底。 */
    unsigned i = (unsigned)s;
    return (i < (unsigned)ST_COUNT) ? names[i] : "?";
}

const char *bms_fault_name(FaultCode f) {
    static const char *names[] = {"NONE", "OVP", "UVP", "OCD", "SCD", "OT"};
    unsigned i = (unsigned)f;            /* 同上：-1 在 int 枚举下会读 names[-1] */
    return (i <= (unsigned)FC_OT) ? names[i] : "?";
}
