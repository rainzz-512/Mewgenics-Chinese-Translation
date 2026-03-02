# 《Mewgenics》中文汉化补丁  
# Mewgenics Chinese Translation Patch

## 中文说明

本项目提供 **《Mewgenics》中文汉化补丁**，目前已覆盖游戏大部分文本，包括：

- NPC 对话  
- 物品与技能说明  
- UI 界面文本  
- 主要游戏内容文本  

本补丁采用 **AI 辅助翻译 + 游戏内测试校对** 的方式制作，后续版本将持续优化翻译质量与术语统一。  
欢迎提交反馈和修正建议。

### v0.6 更新内容
- 根据官方 Patch Notes 1.0.20738，本地化 CSV 已由原先约 20 个拆分文件合并为单一文件 `data/text/combined.csv`
- 本仓库已同步调整结构：`data/text` 目录仅保留 `combined.csv` 作为当前维护入口
- 旧拆分 CSV 已迁移到仓库根目录下的 `_archived_csv`，用于回溯与比对，不再作为当前版本主编辑目标
- 修复了个别文本翻译与措辞问题，提升局部语句准确性与可读性
- 新增了一批中文猫名（含公猫、母猫与中性）

### v0.5 更新内容
- 针对《以撒的结合》等联动物品，手工调整对应术语与原游戏一致（如 `Guppy` 统一译为“嗝屁猫”；以撒联动道具优先沿用以撒社区常见译法，如神性套装三个部件译为“肉体”“思想”“灵魂”）  
- 对 `events` 与 `npc_dialog` 进行了大幅文本更新与本地化优化，显著提升语句自然度与上下文连贯性  
- 针对跨文件术语一致性问题进行了集中优化，提升翻译质量与上下文连贯性  
- 结合模型推理与人工校对，修复并优化了多处关键词在不同语境下的译法  
- 新增包含中文猫名的文档：`catnames_male_en.txt`、`catnames_female_en.txt`、`catnames_neutral_en.txt`  
- 如需在游戏中启用中文猫名，请将以上 3 个 `txt` 文件放入 `data` 文件夹（与 `text` 文件夹同级）

### v0.4 更新内容
- 对 `events` 与 `npc_dialog` 进行了整体验证与本地化润色，提升语句自然度与上下文一致性  
- 统一游戏内关键词翻译，并修复一小部分错翻与漏翻  
- 更新能力与被动描述中的术语，统一为“装备槽”以提高翻译一致性

### v0.3 更新内容
- 修复并优化残留的部分文本挤压、缩小显示问题  
- 补充部分未翻译与翻译不完整的文本  
- 统一部分关键词翻译（如 `Thorns` 统一为“荆棘”、`Bruise` 统一为“挫伤”）

### v0.2 更新内容
- 修复 `[img:...]` 标签解析错误导致的 parse error 与可能的游戏崩溃问题  
- 优化技能与物品描述文本排版，解决文本过长导致卡面字体过小、显示拥挤的问题  
- 恢复 `en` 列原版英文文本，修复语言无法正常切换的问题  
- 多项文本细节与排版优化

### 中文猫名征集（RFC）
- 欢迎提交中文猫名建议，后续将评估并择优加入补丁  
- 名字风格不限，可严肃、可搞怪、可古风、可现代  
- 已新增空白模板：`Mewgenics_CN_patch/catnames_community_template.csv`  
- 填写方式：第一列“男猫名字”、第二列“女猫”、第三列“中性”；每个单元格填写一个名字，可留空，不要改表头与列顺序  
- 当前已提供中文猫名文档：`catnames_male_en.txt`、`catnames_female_en.txt`、`catnames_neutral_en.txt`  
- 若要在游戏中生效，请将上述 3 个 `txt` 文件放入 `data` 文件夹（与 `text` 文件夹同级）  
- 为避免争议与审核风险，以下类型不纳入：  
   - 现实人物姓名（公众人物、创作者、主播等）  
   - 违法违规、仇恨歧视、政治敏感、成人低俗内容  
   - 明显侵权的商标/品牌名或受版权保护角色名  
   - 恶意引战、攻击性、侮辱性词汇

### 致谢
- 感谢 [infinityedge01](https://github.com/infinityedge01)、[elmagnificogi](https://github.com/elmagnificogi)、[Supuritto](https://github.com/Supuritto)、[TeddyHuang-00](https://github.com/TeddyHuang-00)、[Xsakura1314](https://github.com/Xsakura1314)、[Claude-yuliu](https://github.com/Claude-yuliu)、[tuwary](https://github.com/tuwary)、[MnFeN](https://github.com/MnFeN)、[mewcodex](https://github.com/mewcodex) 在补丁开发期间提供贡献与支持  
- 感谢 [DR9K69AI79](https://github.com/DR9K69AI79) 提供字体更改支持

### 安装方法
1. 在 **Releases** 页面下载最新补丁  
2. 将补丁中的 `data` 文件夹解压到游戏目录（与 `resources.gpak` 同级）  
3. 覆盖同名文件  
4. 启动游戏并在设置中选择中文即可

### 可选：自定义中文字体

游戏默认使用 Noto Sans CJK TC（思源黑体）作为字体的 fallback 选项。如果你希望更换为其他字体，有两种方式：

**方式一：使用预制字体（仓耳渔阳体）**
1. 将补丁中的 `swfs` 文件夹复制到游戏目录（与 `resources.gpak` 同级）  
2. 重启游戏即可看到效果

> [仓耳渔阳体](https://tsanger.cn/product/199)为免费商用字体。效果预览见下方截图。

**方式二：DIY 替换为任意字体**
1. 安装 [JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler)  
2. 在 JPEXS FFDec 安装目录下运行以下命令（以补丁自带的 `swfs/unicodefont.swf` 为基础）：
   ```
   ffdec-cli.exe -replace unicodefont.swf unicodefont_custom.swf 1 你的字体.ttf
   ```
3. 将生成的 `unicodefont_custom.swf` 重命名为 `unicodefont.swf`，放入游戏目录的 `swfs/` 文件夹

> 注意：字体文件放在游戏根目录的 `swfs/` 文件夹下（不是 `data/swfs/`）。

**恢复默认字体：** 删除游戏目录下的 `swfs/` 文件夹即可。

**效果预览：**

| | 默认字体（思源黑体） | 自定义字体（仓耳渔阳体） |
|:---:|:---:|:---:|
| 主菜单 | ![默认-主菜单](screenshots/font_default_main_menu.png) | ![仓耳渔阳体-主菜单](screenshots/font_canger_yuyang_main_menu.png) |
| 游戏设置 | ![默认-游戏设置](screenshots/font_default_settings_game.png) | ![仓耳渔阳体-游戏设置](screenshots/font_canger_yuyang_settings_game.png) |

### 注意
- 当前为早期版本，可能仍存在少量未翻译文本  
- 若游戏更新导致文本失效，请等待补丁更新  

---

## English

This project provides a **Chinese translation patch for Mewgenics**, covering most in-game texts including:

- NPC dialogues  
- Items and abilities  
- UI texts  
- General gameplay text  

The translation is created using **AI-assisted translation and in-game testing**, and future updates will continue to improve translation quality and terminology consistency.  
Feedback and correction suggestions are welcome.

### v0.6 Changes
- Synced with official Patch Notes 1.0.20738: localization CSVs were merged from ~20 split files into a single `data/text/combined.csv`
- Repository structure has been updated accordingly: `data/text` now keeps only `combined.csv` as the active maintenance target
- Legacy split CSV files were moved to `_archived_csv` at repository root for reference/diffing, and are no longer the primary editing target for current versions
- Fixed a small number of translation issues and wording inconsistencies to improve local text accuracy and readability
- Added more Chinese cat names (male/female/neutral)

### v0.5 Changes
- Manually aligned crossover item terminology (especially for *The Binding of Isaac* references) with established in-game naming conventions (e.g., `Guppy` -> “嗝屁猫”; Isaac crossover terms follow Isaac-localization conventions, including “肉体 / 思想 / 灵魂” for the Godhead set components)  
- Performed major text updates and localization optimization for `events` and `npc_dialog`, significantly improving fluency and contextual coherence  
- Improved cross-file terminology consistency to enhance translation quality and context coherence  
- Combined model-assisted refinement with manual review to fix and polish term usage across different contexts  
- Added documents containing Chinese cat names: `catnames_male_en.txt`, `catnames_female_en.txt`, `catnames_neutral_en.txt`  
- To use Chinese cat names in-game, place the 3 `txt` files into the `data` folder (same level as the `text` folder)

### v0.4 Changes
- Performed full localization polish for `events` and `npc_dialog`, improving fluency and contextual consistency  
- Unified in-game keyword translations and fixed a small subset of mistranslations/missing lines  
- Updated terminology in ability/passive descriptions, standardizing to "装备槽" for consistency

### v0.3 Changes
- Fixed and optimized remaining cases of compressed/shrunk text display  
- Added some previously untranslated or partially translated text  
- Standardized terminology for key terms (e.g., `Thorns` as "荆棘", `Bruise` as "挫伤")

### v0.2 Changes
- Fixed parse errors caused by incorrect `[img:...]` tag parsing that could lead to crashes  
- Improved line wrapping for ability and item descriptions to prevent cramped UI text  
- Restored original English text in the `en` column, fixing language switching issues  
- Minor text formatting and localization improvements

### Chinese Cat Name RFC
- We welcome community suggestions for Chinese cat names and will evaluate them for inclusion in future patch updates  
- Any naming style is welcome (serious, playful, classical, modern, etc.)  
- Added blank template: `Mewgenics_CN_patch/catnames_community_template.csv`  
- How to fill: column 1 = male names, column 2 = female names, column 3 = neutral names; one name per cell, empty cells are allowed, and please keep the header and column order unchanged  
- Current Chinese cat-name docs: `catnames_male_en.txt`, `catnames_female_en.txt`, `catnames_neutral_en.txt`  
- To make them work in-game, place the 3 `txt` files into the `data` folder (same level as the `text` folder)  
- To avoid moderation and legal issues, the following categories are excluded:  
   - Real-person names (public figures, creators, streamers, etc.)  
   - Illegal, hateful, discriminatory, political-sensitive, explicit/sexual content  
   - Clearly infringing trademark/brand names or copyrighted character names  
   - Provocative, abusive, or harassment-oriented naming

### Acknowledgements
- Thanks to [infinityedge01](https://github.com/infinityedge01), [elmagnificogi](https://github.com/elmagnificogi), [Supuritto](https://github.com/Supuritto), [TeddyHuang-00](https://github.com/TeddyHuang-00), [Xsakura1314](https://github.com/Xsakura1314), [Claude-yuliu](https://github.com/Claude-yuliu), [tuwary](https://github.com/tuwary), [MnFeN](https://github.com/MnFeN), and [mewcodex](https://github.com/mewcodex) for contributions and support during patch development  
- Thanks to [DR9K69AI79](https://github.com/DR9K69AI79) for font modification support

### Installation
1. Download the latest patch from **Releases**  
2. Extract the `data` folder into the game directory (the same location as `resources.gpak`)  
3. Overwrite files if prompted  
4. Launch the game and select Chinese in the settings

### Optional: Custom Chinese Font

The game uses Noto Sans CJK TC as the fallback font option for Chinese text. You can replace it with a custom font:

**Option 1: Use the bundled font (CangEr YuYang)**
1. Copy the `swfs` folder from the patch into the game directory (same location as `resources.gpak`)  
2. Restart the game

> CangEr YuYang is a free commercial-use font ([official page](https://tsanger.cn/product/199)). See screenshots below for preview.

**Option 2: DIY with any font**
1. Install [JPEXS FFDec](https://github.com/jindrapetrik/jpexs-decompiler)  
2. Run the following command in the JPEXS FFDec installation directory (using the bundled `swfs/unicodefont.swf` as base):
   ```
   ffdec-cli.exe -replace unicodefont.swf unicodefont_custom.swf 1 your_font.ttf
   ```
3. Rename the output to `unicodefont.swf` and place it in the `swfs/` folder in the game directory

> Note: The font file goes in the `swfs/` folder at game root (NOT `data/swfs/`).

**Restore default font:** Simply delete the `swfs/` folder in the game directory.

**Preview:**

| | Default Font (Noto Sans CJK) | Custom Font (CangEr YuYang) |
|:---:|:---:|:---:|
| Main Menu | ![Default-Menu](screenshots/font_default_main_menu.png) | ![CangEr-Menu](screenshots/font_canger_yuyang_main_menu.png) |
| Settings | ![Default-Settings](screenshots/font_default_settings_game.png) | ![CangEr-Settings](screenshots/font_canger_yuyang_settings_game.png) |

### Notes
- This is an early release; some lines may remain untranslated  
- If a game update breaks the patch, please wait for a new version
