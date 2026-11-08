# 原创工程手绘管线

此目录读取 `bms-book/ILLUSTRATION-PROMPTS.md` 的场景合同，使用用户授权的 OpenAI 兼容生图通道。不是程序绘图冒充 AI 出图，也不是 AI 图冒充仪器记录。

## 当前状态

- **2026-11-08 用户决定停用生图 API（太慢）**，不再提交新任务。已接入的三张（第 1、7 章首与 S2 概念章首）保留；其余 27 张不再等生图，继续用仓库自绘矢量，封面与阶段页维持原有效图。
- 另一平台以 `auto` 请求返回 `unsupported_model`，未产出图片；失败请求的临时记录已删除，不把失败调用记成资产。
- 拒绝候选与六张已付费待审候选仍保留在清单中，只能人工审阅；没有用户明确要求时不再重试付费生成。旧 `PAUSE` 保留。

## 使用

密钥只从 `BMS_IMAGE_API_KEY` 环境变量读取，不放进脚本、命令示例、日志或清单。`BMS_IMAGE_BASE_URL` 可指定经授权的 HTTPS 网关。Pillow 是仓库已有出版依赖，HTTP 客户端只用标准库。

```text
python code/engineering/illustration/make_handdrawn.py --only s2-hero
python code/engineering/illustration/make_handdrawn.py --all --jobs 3
python code/engineering/illustration/make_handdrawn.py --check
python code/engineering/illustration/make_style_trials.py
```

`--check` 不联网。完整清单缺图或候选被拒绝就返回非零，不能用一次子集核对替代整批验收。匹配的已付费资产复用；已有记录不匹配必须先审阅，再显式 `--replace`，绝不自动再次付费。

## 安全与身份

- 默认 TLS 验证，禁止 HTTP origin、含用户信息的端点和带凭据跳转。不读取返回的图片 URL，只解码 base64 PNG。
- 一个发布进程持有 `.publisher.lock`；互斥合并最新清单，临时文件名唯一。逐图 `.record.json` 先于全局清单落盘，保留付费结果。
- `PAUSE` 阻止新请求；已在途结果可落盘，队列只保有有限在途任务。401/403 会设置暂停，不自动重试或换账号。
- 原 PNG、实际提示词、参考图及 WebP 都有 SHA-256。模型非确定，身份可核对不代表像素可重现。WebP 等比留白，不裁掉电路或拉伸波形。
- 实际风格是项目原创暖纸/蓝墨工程手绘，没有冒用 canonical ID。参考图来自仓库自绘书封；不继续提交被服务端拒绝的作者风格复现请求。

## 正确性与审查

精确拓扑、曲线、轴、单位由代码生成；AI 图只表达概念。三类代表试版（S1 信号链、S2 RC、S3 预充）由 `make_style_trials.py` 生成，不能据此勾选 S1/S3 实验或正文完成。浏览器图像、窄屏等价说明和独立领域审读各自记证据。

`test_handdraw_pipeline.py` 是本轮新增的六条安全/付费产物回归，须独立审阅，不属于上一轮固定测试基线。来源总表在 `bms-book/illustrations/handdraw/manifest.json`；全部生成完成前保持不完整状态。
