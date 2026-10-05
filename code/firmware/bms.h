/* BMS 主状态机骨架 —— 阶段 3 §3.4 / 阶段 6 §6.2 的可运行版本。
 *
 * 设计对应教程三条工程纪律：
 *   1. 所有迁移集中在状态机一处（bms_tick 是唯一改 state 的地方）；
 *   2. 每个状态明确"进入/周期/退出"动作；
 *   3. 任意状态下保护触发都可直接进故障态——见 bms.c 的 eval_protections()。
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
 * OVP/UVP/OCD/SCD/OT（去抖/快照/锁存/方向性断口——OVP 断充留放、UVP/OCD
 * 断放留充、SCD/OT 双断；多故障合并断口，见 bms.c 的 enter_fault()）。未实现（扩展练习）：
 * 预充态、充电过流 OCC、欠温 UT、故障分级 WARN/LIMP 的实际动作、快照的
 * 读取与清除接口（见 FaultSnapshot 注释：本骨架的快照是"上电以来第一次故障"）。 */
/*
 * 预充态扩展练习的设计问题（只给问题不给答案，答完再动手）：
 *   a. 进入条件：什么状态下允许进预充？母线电压采样从哪来（BmsInputs
 *      需要加哪个字段）？
 *   b. 完成判据：教程 §6.1.2 的"母线电压 ≥ 电池电压 90–95%"，你的阈值
 *      取多少、为什么？用 t ≈ 3RC 估算预充时间，超时阈值取它的几倍？
 *   c. 失败路径：超时母线电压上不来 → 外部短路/后端故障（§6.1.2），
 *      进 FAULT 时快照字段够不够描述"预充失败"这个原因？
 *   d. 时序闭环：合主继电器 K1 与断预充 K2 的先后与间隔——先合 K1 还是
 *      先断 K2？（提示：想想两个继电器同时断开的瞬间母线靠什么供电。）
 *   e. 测试：test_bms.c 里补哪些用例？（正常预充通过 / 超时失败 / 预充
 *      途中 OVP 触发——第三条对应"任意状态可直接进故障态"纪律。） */
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

/* 独立记录尚未恢复的各项保护；FaultCode 仅用于显示主故障与第一现场。 */
typedef enum {
    FM_NONE = 0,
    FM_OVP = 1u << 0,
    FM_UVP = 1u << 1,
    FM_OCD = 1u << 2,
    FM_SCD = 1u << 3,
    FM_OT  = 1u << 4
} FaultMask;

/* 每周期从采样层喂进来的输入 */
typedef struct {
    int32_t cell_mv[BMS_MAX_CELLS];
    int32_t current_ma;    /* >0 充电 */
    int16_t temp_c10;      /* 0.1°C */
    bool    charger_present;
} BmsInputs;

/* 保护配置：阈值 + 去抖次数 + 恢复阈值（教程的"保护三要素"）
 *
 * 去抖次数语义：连续超限 cnt 达到该值才动作；**配 0 表示首次超限即动作**
 * （与短路的"无去抖"一致），不是"永不动作"。 */
typedef struct {
    uint16_t ovp_mv;        uint16_t ovp_release_mv;  uint8_t ovp_debounce;
    uint16_t uvp_mv;        uint16_t uvp_release_mv;  uint8_t uvp_debounce;
    uint32_t ocd_ma;                              uint8_t ocd_debounce;
    uint32_t scd_ma;        /* 短路无去抖：硬件优先，软件骨架也立即动作 */
    int16_t  ot_c10;
    uint16_t balance_start_mv;   /* 均衡电压下限：进入和保持均须最高串达到此值 */
    uint16_t balance_delta_mv;   /* 且与最低串压差超过此值 */
    uint16_t full_mv;            /* 满充判据：电压高位 */
    uint32_t full_cutoff_ma;     /* 且 CV 电流衰减到截止值以下 */
    uint32_t sleep_idle_ticks;   /* 待机多少拍无活动进休眠 */
} BmsConfig;

/* 故障快照：触发瞬间冻结现场（教程 6.2.2"快照是灵魂"）。
 *
 * 语义注意：snapshot_valid 一旦置位就不再清除，"第一现场不被后续故障覆盖"
 * 因此实际含义是**上电以来第一次故障**，而不是"每次故障事件的第一现场"。
 * 量产固件要的是后者——故障恢复或主机读走后清掉，下一次故障重新冻结；
 * 且通常保留多份（NVM 里滚动存最近几条），因为现场可能几天后才被调取。
 * 本骨架刻意不做读写接口：快照的存储介质与生命周期属于产品定义。 */
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
    uint32_t   fault_mask;     /* FaultMask 位集合，逐项满足恢复条件才清除 */
    FaultCode  active_fault;   /* 显示优先级 SCD > OT > OVP > UVP > OCD；无故障为 NONE */
    bool       fault_latched;  /* 从 FM_SCD 派生，只在双向零电流窗口内解锁 */
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
