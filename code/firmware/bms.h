/* BMS 主状态机骨架 —— 阶段 3 §3.4 / 阶段 6 §6.2 的可运行版本。
 *
 * 设计对应教程三条工程纪律：
 *   1. 所有迁移集中在状态机一处（bms_tick 是唯一改 state 的地方）；
 *   2. 每个状态明确"进入/周期/退出"动作；
 *   3. 任意状态下保护触发都可直接进故障态——见 bms_eval_protections()。
 *
 * 纯 C99、无平台依赖：PC 上可编译可测，移植到 MCU 时只需提供
 * BmsInputs 的采样值并消费 MOS/均衡输出标志。
 *
 * 约定（与教程一致）：电流 > 0 充电，< 0 放电。电压 mV，电流 mA，温度 0.1°C。
 */
#ifndef BMS_H
#define BMS_H

#include <stdbool.h>
#include <stdint.h>

#define BMS_MAX_CELLS 16

/* 本骨架已实现：INIT/STANDBY/CHARGE/DISCHARGE/BALANCE/FAULT/SLEEP +
 * OVP/UVP/OCD/SCD/OT（去抖/快照/锁存）。未实现（扩展练习）：预充态、
 * 充电过流 OCC、欠温 UT、故障分级 WARN/LIMP 的实际动作。 */
typedef enum {
    ST_INIT = 0,
    ST_STANDBY,
    ST_CHARGE,
    ST_DISCHARGE,
    ST_BALANCE,
    ST_FAULT,
    ST_SLEEP,
    ST_COUNT
} BmsState;

typedef enum {
    FL_NONE = 0,   /* 正常 */
    FL_WARN,       /* 提示：上报但不动作（骨架未演示，预留枚举） */
    FL_LIMP,       /* 限功率（骨架未演示，预留枚举） */
    FL_TRIP        /* 断开——本骨架 enter_fault 一律用此级 */
} FaultLevel;

typedef enum {
    FC_NONE = 0,
    FC_OVP,        /* 过充 */
    FC_UVP,        /* 过放 */
    FC_OCD,        /* 放电过流 */
    FC_SCD,        /* 短路 */
    FC_OT          /* 过温 */
} FaultCode;

/* 每周期从采样层喂进来的输入 */
typedef struct {
    int32_t cell_mv[BMS_MAX_CELLS];
    int32_t current_ma;    /* >0 充电 */
    int16_t temp_c10;      /* 0.1°C */
    bool    charger_present;
} BmsInputs;

/* 保护配置：阈值 + 去抖次数 + 恢复阈值（教程的"保护三要素"） */
typedef struct {
    uint16_t ovp_mv;        uint16_t ovp_release_mv;  uint8_t ovp_debounce;
    uint16_t uvp_mv;        uint16_t uvp_release_mv;  uint8_t uvp_debounce;
    uint32_t ocd_ma;                              uint8_t ocd_debounce;
    uint32_t scd_ma;        /* 短路无去抖：硬件优先，软件骨架也立即动作 */
    int16_t  ot_c10;
    uint16_t balance_start_mv;   /* 均衡入口：充电末端最高串高于此值 */
    uint16_t balance_delta_mv;   /* 且与最低串压差超过此值 */
    uint16_t full_mv;            /* 满充判据：电压高位 */
    uint32_t full_cutoff_ma;     /* 且 CV 电流衰减到截止值以下 */
    uint32_t sleep_idle_ticks;   /* 待机多少拍无活动进休眠 */
} BmsConfig;

/* 故障快照：触发瞬间冻结现场（教程 6.2.2"快照是灵魂"） */
typedef struct {
    uint32_t tick;
    FaultCode code;
    int32_t  cell_mv[BMS_MAX_CELLS];
    int32_t  current_ma;
    int16_t  temp_c10;
    uint8_t  soc_pct;
} FaultSnapshot;

typedef struct {
    BmsConfig cfg;
    BmsState  state;
    uint8_t   cell_count;
    uint8_t   soc_pct;
    uint32_t  tick;

    /* 去抖计数器 */
    uint8_t cnt_ovp, cnt_uvp, cnt_ocd;

    FaultLevel level;
    FaultCode  active_fault;   /* 当前故障（FC_NONE = 无） */
    bool       fault_latched;  /* SCD 等锁存故障需明确条件才清除 */
    FaultSnapshot snapshot;
    bool       snapshot_valid;

    /* 输出（驱动层去执行） */
    bool charge_mos_on;
    bool discharge_mos_on;
    bool balance_on[BMS_MAX_CELLS];

    uint32_t idle_ticks;
} Bms;

void bms_init(Bms *bms, const BmsConfig *cfg, uint8_t cell_count, uint8_t soc_pct);
void bms_tick(Bms *bms, const BmsInputs *in);
const char *bms_state_name(BmsState s);
const char *bms_fault_name(FaultCode f);

#endif /* BMS_H */
