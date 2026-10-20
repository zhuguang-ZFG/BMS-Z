## 改动

<!-- 一句话：改了什么、为什么 -->

## 自检

- [ ] `powershell -NoProfile -File scripts/local-gates.ps1` 或 `bash scripts/local-gates.sh` 全绿（含 `pytest 擂台基线` 与 `hil_replay`）
- [ ] 新增外链已实测可达；反爬"假死"按 .lychee.toml 头部注释流程核实并记录证据
- [ ] 未改动既有小节标题（锚点是公共合同）；新增小节未与既有撞名
- [ ] 若新增 SVG：满足 `<title>` / `<animate` / `prefers-color-scheme: dark` 三约定，且根 README、docs/circuits/README.md、check_docs.py 的 MIN_SVGS 三处计数已同步
- [ ] 阈值/参数已标注"示例值，以 datasheet 为准"；厂商宣传口径写成"据厂商发布"
- [ ] 若为代码改动：按[代码交付单](https://github.com/zhuguang-ZFG/BMS-Z/blob/main/.github/ISSUE_TEMPLATE/06-code-delivery.md)附上命令、退出码与原始输出；测试没有被放宽、跳过或删除

## 代码改动（只改文档可跳过）

- **测试**：哪条先红、现在为什么绿
- **本机跑的**：命令 + 退出码 + 关键输出（原样粘贴，不要转述）
- **已知风险**：这次改动仍然证明不了什么
- **回滚**：改哪几个文件、按什么顺序退回
- **没有碰**：安全回路 / 阈值与寄存器 / 依赖 / 生成产物 / 凭据与 OTA 签名（有例外写清）
- **签字**：姓名 + 日期；阈值与安全相关改动需要第二个人

口径见 [AI 陪练卡 · 写代码的五个关卡](https://github.com/zhuguang-ZFG/BMS-Z/blob/main/docs/AI%E9%99%AA%E7%BB%83%E5%8D%A1.md#写代码的五个关卡)。
