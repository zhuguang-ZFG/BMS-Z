# 书内字体子集

《通往模拟电路之路》16K 印刷书使用的 OFL 字体子集。后续构建把它们以
data URI 内联进单文件 HTML，因此本目录不需要任何系统字体或网络字体。

## WOFF2 子集

| 文件 | 家族 | 字重 | 请求字符数 | 字节 | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `NotoSerifSC-Regular.woff2` | NotoSerifSC | 400 | 2201 | 375,120 | `33f77a596588e48d40f41b3bee165e8913bd46cefcfff26fc264686aacf37664` |
| `NotoSerifSC-Bold.woff2` | NotoSerifSC | 700 | 2201 | 386,928 | `e7d7bf04a27d71c4283b5dbf9509e7705a607e1552eb27b98e7460418af27ebd` |
| `NotoSansSC-Regular.woff2` | NotoSansSC | 400 | 2201 | 292,944 | `18fc5da5eac81f022f67115c364119cde459c60e711f6a8a52065b59720d16de` |
| `NotoSansSC-Bold.woff2` | NotoSansSC | 700 | 2201 | 299,980 | `c2e425b87ef4ea89f320b2d9a8970eeeb59950d770be9b60855488491ac09eed` |
| `JetBrainsMono-Regular.woff2` | JetBrainsMono | 400 | 95 | 15,844 | `94d9e25e7d4293923031470710ba1ff681e89421113fadd41555e8a4a4a066ce` |

## 印章字体

| 文件 | 家族 | 字重 | 请求字符数 | 字节 | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `BookSans-Stamp.ttf` | NotoSansSC | 700 | 1001 | 260,080 | `4d69137d7f094b6f6207796f8c5585214c5f25618e2e747a7a6e29d6c962761c` |

印章字体由 Noto Sans SC 在 wght=700 实例化后，子集到 ASCII、书名、
前置页/篇/单元/附录/后记标题、章名与页脚固定词，用于页眉/页脚印章。

## 源字体

源文件缓存在仓库外的 `build/fonts-src/`（`.gitignore` 已忽略），
重新生成时可凭 `sources.json` 中的 URL 与 SHA-256 校验。

| 家族 | 角色 | 文件 | URL | 字节 | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| NotoSerifSC | primary | `NotoSerifSC-VF.ttf` | <https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf> | 25,125,512 | `050080d9255a86808f2945bffac582b31ef32bc36411ce29563b4961670c66f9` |
| NotoSansSC | primary | `NotoSansSC-VF.ttf` | <https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf> | 17,772,300 | `a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da` |
| JetBrainsMono | primary | `JetBrainsMono-VF.ttf` | <https://raw.githubusercontent.com/google/fonts/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf> | 187,208 | `48715a42ec242c21e9f02692891e147d022299a52e48d5e413e1a942193ffeda` |
| NotoSerif | glyph-donor | `NotoSerif-VF.ttf` | <https://raw.githubusercontent.com/google/fonts/main/ofl/notoserif/NotoSerif%5Bwdth,wght%5D.ttf> | 1,887,192 | `4d8e6761424656867019081a1a01336f3cb086982682698714054fc33f782713` |
| NotoSans | glyph-donor | `NotoSans-VF.ttf` | <https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/NotoSans%5Bwdth,wght%5D.ttf> | 2,049,096 | `bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d` |
| NotoSansSymbols2 | glyph-donor | `NotoSansSymbols2-Regular.ttf` | <https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssymbols2/NotoSansSymbols2-Regular.ttf> | 1,233,128 | `7d5fb73b7ca67a6798101741f5d280a3d016a56a197afcd4199dbb57b4b82a21` |

## 缺字补充

Noto Serif SC 与 Noto Sans SC 的可变字体都不含书稿实际使用的 14 个
字符：上标 `U+2070 U+2075 U+2076 U+2077 U+2078 U+2079`、下标
`U+2080 U+2081 U+2082`、分数 `U+2153 U+2154`、组合上划线 `U+0305`、
实心左指三角 `U+25C4` 与叉号 `U+2717`。子集脚本从同为 OFL 的 Noto Serif /
Noto Sans（拉丁）复制前 12 个字符的真实轮廓，并从 Noto Sans Symbols 2 复制
`U+25C4` 与 `U+2717`，再写入子集的 cmap/hmtx/vmtx；没有删减覆盖测试的字符。

对勾 `U+2713` 原生存在于 Noto SC 中。`EMOJI_RE` 会剥掉 `✓✗`，而 Task 5
把 ✅/❌ 映射为 `✓/✗` 输出，因此 `required_text()` 在剥离 emoji 后显式
补入这两个字形，四个正文子集都必须覆盖它们。

## 许可

全部字体按 SIL Open Font License 1.1 发布，许可全文见同目录
`OFL-*.txt`；源字体版权与保留字体名以对应文件为准。

## 复现

```bash
python scripts/subset_fonts.py --download
python scripts/subset_fonts.py --build
python scripts/subset_fonts.py --check
```

`--build` 只读取 `build/fonts-src/`，不访问网络；`--check` 校验哈希、
许可文件与 `required_text()` 覆盖率。`build/fonts-src/` 中的源 TTF/OTF
与下载的许可文件不入仓。
