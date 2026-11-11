"""待渲染手绘资产：出图授权已给（操作者 2026-11-11「使用出图函数出图」），
等待 BMS_IMAGE_API_KEY 注入后接入 ASSETS 并渲染。

本模块故意不挂进 handdrawn_assets.ASSETS：check() 会对 ASSETS 中无记录的键报
missing record，未渲染前先入册会把免网完整性门禁打红。渲染流程：
1. 操作者在环境注入 BMS_IMAGE_API_KEY；
2. 把下面三个 Asset 并入 handdrawn_assets.ASSETS（移除本文件）；
3. python code/engineering/illustration/make_handdrawn.py --only d16-silent-band
   依次渲染三幅（--only d19-clock-degradation / d20-epoch-snapshot）；
4. make_handdrawn.py --check 复核记录与画布；
5. 复制/登记进工程册单元资产与 figures.json（targets 已直接指向单元资产目录）。
"""

from __future__ import annotations

from handdrawn_assets import ISOLATION_ZH, STYLE_ZH, ZERO_DIGITS_ZH, Asset

PENDING: tuple[Asset, ...] = (
    Asset(
        key="d16-silent-band",
        target="bms-book/engineering/assets/d16-thermal/D16-F2-silent-band.webp",
        canvas=(1536, 896),
        prompt=(
            STYLE_ZH
            + "画面要求：暖象牙纸底。左侧剖开的一组电池芯，芯体表面贴着一支长温度计；"
            "右侧同组电池的外壳贴着另一支温度计，两支温度计的液柱顶端高度明显不同，"
            "芯侧高、壳侧低。两支温度计之间画一条横向的空档带，带内不放任何标记，"
            "只有大片留白，暗示这段区间什么都不会发生。一只原创成年工程师的极简几何"
            "人物站在空档带前，一只手摊开指向带内，表情困惑；另一只小人蹲在壳侧"
            "温度计旁，仰头看着还差一截的液柱。"
            + ZERO_DIGITS_ZH
            + ISOLATION_ZH
        ),
    ),
    Asset(
        key="d19-clock-degradation",
        target="bms-book/engineering/assets/d19-bus/D19-F2-clock-degradation.webp",
        canvas=(1536, 896),
        prompt=(
            STYLE_ZH
            + "画面要求：暖象牙纸底。一条从左到右的时间纸带，右端并排放着最后一枚"
            "小小的信封，信封之后纸带继续延伸出很长一段空白，空白处不再出现任何信封"
            "或字节。纸带上方立着一座大座钟，指针独自前进，刻度只有一条醒目的刻线；"
            "指针越过刻线的瞬间，刻线旁的一盏圆灯由绿转琥珀。一只原创成年工程师的"
            "极简几何人物看着座钟而不是信箱，表情凝重；空白纸带上用极淡的虚线画出"
            "节拍间隔，表示时钟在数拍。"
            + ZERO_DIGITS_ZH
            + ISOLATION_ZH
        ),
    ),
    Asset(
        key="d20-epoch-snapshot",
        target="bms-book/engineering/assets/d20-firmware/D20-F2-epoch-snapshot.webp",
        canvas=(1536, 896),
        prompt=(
            STYLE_ZH
            + "画面要求：暖象牙纸底。一排五个相同的空白方块横贯画面，前两个方块画在"
            "一张颜色略旧的纸页上，后三个方块画在一张新纸页上，两张纸页中间有一道"
            "明显的接缝，一只小手正按在接缝处。纸页右下角一枚圆形印章只盖在最后一个"
            "方块旁，表示发布时刻。一只原创成年工程师的极简几何人物站在排前，双手"
            "各拿一半读数，表情迟疑，身体微微后仰；另一枚小放大镜悬在印章上方。"
            + ZERO_DIGITS_ZH
            + ISOLATION_ZH
        ),
    ),
)
