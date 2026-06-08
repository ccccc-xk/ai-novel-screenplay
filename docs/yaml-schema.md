# 剧本 YAML Schema 设计文档

## 1. 概述

本文档定义了 AI 小说转剧本工具所使用的 YAML Schema 规范。该 Schema 旨在以结构化、可读、可扩展的方式表示影视剧本的完整内容，包括元数据、场景划分、角色对白、动作描写和转场指示等要素。

### 设计目标

- **完整性**：覆盖剧本的所有核心要素，不遗漏关键信息
- **可读性**：YAML 格式天然具备人类可读性，作者可以直接阅读和编辑
- **可验证性**：可通过 Pydantic 模型进行自动数据验证
- **可扩展性**：预留扩展字段，适应不同剧本风格的需求
- **标准化**：遵循国际通行的剧本格式惯例（场景标题行使用 INT/EXT 标记）

## 2. Schema 顶层结构

```yaml
metadata:    # 剧本元数据（必填）
scenes:      # 场景列表（必填）
```

整个 Schema 由两个顶层字段组成：`metadata` 和 `scenes`。这种二层扁平结构避免了过度嵌套，便于解析和编辑。

### 为什么选择扁平结构？

- 降低解析复杂度，减少出错概率
- 作者在手动编辑时不易迷失层级
- 与主流剧本格式（Final Draft .fdx、Fountain）的信息层级对齐

## 3. metadata（元数据）

```yaml
metadata:
  title: "剧本标题"           # 必填
  author: "原作者"            # 可选
  adapter: "改编者"           # 可选
  genre: "类型/题材"          # 可选，如：都市情感、悬疑推理
  version: "1.0"              # 版本号
  created_at: "2026-06-08"    # 创建时间
  source_chapters: 3          # 来源章节数
  total_scenes: 6             # 总场景数
  characters:                 # 主要角色列表
    - "林晓"
    - "苏然"
  synopsis: "一句话梗概"      # 故事梗概
```

### 设计原因

| 字段 | 必要性 | 说明 |
|------|--------|------|
| `title` | 必填 | 剧本的核心标识，也是唯一必填的元数据字段 |
| `author` | 可选 | 保留原作者署名权 |
| `adapter` | 可选 | 记录改编者信息 |
| `genre` | 可选 | 便于分类和检索 |
| `version` | 可选 | 剧本经过多次修改时需要版本管理 |
| `created_at` | 可选 | 记录生成时间，便于追溯 |
| `source_chapters` | 可选 | 记录原始小说的章节数，建立溯源关系 |
| `total_scenes` | 可选 | 快速了解剧本规模 |
| `characters` | 可选 | 角色总览，便于导演和制片快速了解演员需求 |
| `synopsis` | 可选 | 一句话梗概，是剧本的"电梯演讲" |

## 4. scenes（场景列表）

每个场景是剧本的基本叙事单元，对应一个连续的时间和空间。

```yaml
scenes:
  - scene_number: 1                          # 必填，场景编号
    scene_heading: "INT. 咖啡厅 - DAY"       # 必填，场景标题行
    location: "咖啡厅"                        # 必填，地点
    scene_type: "INT"                         # 内景/外景
    time_of_day: "DAY"                        # 时间
    characters: ["林晓", "苏然"]              # 出场角色
    summary: "林晓和苏然在咖啡厅见面"         # 场景摘要
    lines:                                    # 必填，场景内容
      - line_type: action
        action:
          content: "动作描写内容"
      - line_type: dialogue
        dialogue:
          character: "角色名"
          parenthetical: "表演提示"
          content: "对白内容"
```

### 4.1 scene_heading（场景标题行）

采用国际标准格式：`INT/EXT. 地点 - 时间`

**为什么使用这个格式？**
- 这是好莱坞和全球影视行业的通用标准
- Final Draft、Highland、Fountain 等主流编剧软件均采用此格式
- 便于制片部门快速统计内/外景和日/夜戏的工作量

### 4.2 scene_type（场景类型）

枚举值：
- `INT` — 内景（Interior）
- `EXT` — 外景（Exterior）
- `INT/EXT` — 内外景（如车内场景，镜头在车内外切换）

**为什么单独提取？**
虽然 `scene_heading` 中已包含此信息，但单独提取为字段便于程序化处理（如按场景类型筛选、统计）。

### 4.3 time_of_day（时间）

枚举值：`DAY`、`NIGHT`、`MORNING`、`EVENING`、`DAWN`、`DUSK`、`UNKNOWN`

**为什么提供6个时间选项？**
- 日/夜是最基本的拍摄分类
- 晨/昏/暮等细分对特定类型（如恐怖片、爱情片）很重要
- `UNKNOWN` 兜底处理无法判断的情况

### 4.4 characters（出场角色）

该场景中出现的角色名列表。

**为什么在场景级别记录？**
- 制片需要按场景统计每个演员的出场次数，用于排期和成本估算
- 与 metadata.characters（全剧角色总览）形成层级关系

### 4.5 summary（场景摘要）

一句话概括场景核心内容。

**为什么需要摘要？**
- 帮助作者快速浏览剧本结构而不必逐行阅读
- 便于在长剧本中定位特定场景
- AI 转换时生成的摘要可作为人工审核的参考

## 5. lines（场景内容行）

`lines` 是场景的核心内容，是一个多态数组，每个元素通过 `line_type` 字段区分类型。

### 5.1 action（动作/描写）

```yaml
- line_type: action
  action:
    content: "描写内容"
    character: "相关角色"   # 可选
```

**设计说明：**
- `content` 是必填字段，承载具体的动作或场景描写
- `character` 可选标注动作主体，便于后续按角色提取戏份
- 去除了小说中的心理描写和叙述性评论，只保留可视化的动作

### 5.2 dialogue（对白）

```yaml
- line_type: dialogue
  dialogue:
    character: "角色名"           # 必填
    parenthetical: "表演提示"     # 可选
    content: "对白内容"           # 必填
```

**设计说明：**
- `character` 必填，是对白的归属标识
- `parenthetical`（括号提示）是剧本特有的元素，用简短词语指导演员表演方式，如"低声地"、"愤怒"、"笑着"
- 对白与动作分离，便于后续格式化输出为标准剧本样式

### 5.3 transition（转场）

```yaml
- line_type: transition
  transition:
    type: "CUT_TO"        # 转场类型
    target: "转场目标"     # 可选
```

**常见转场类型：**
- `CUT_TO` — 直接切换
- `FADE_IN` — 淡入
- `FADE_OUT` — 淡出
- `DISSOLVE` — 叠化
- `SMASH_CUT` — 硬切

**为什么单独设为一种行类型？**
转场是导演和剪辑师的核心工作语言，与动作和对白性质不同，需要独立标记。

## 6. 行类型的多态设计

```yaml
lines:
  - line_type: action        # 类型标识
    action: { ... }          # 对应数据
  - line_type: dialogue
    dialogue: { ... }
  - line_type: transition
    transition: { ... }
```

### 为什么使用 `line_type` + 可选字段的多态模式，而非联合类型？

**方案对比：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| **当前方案**（line_type + 可选字段） | YAML 可读性好，验证简单 | 字段冗余（每行只有一个有效字段） |
| 联合类型（只保留一种字段） | 更紧凑 | YAML 解析时需要判断字段名，增加复杂度 |
| type/data 嵌套 | 类型安全 | 嵌套过深，YAML 可读性差 |

选择当前方案的原因：
1. **YAML 可读性优先** — 作者可能直接编辑 YAML 文件，扁平结构更友好
2. **验证简单** — Pydantic 可以通过 `line_type` 字段轻松验证对应数据
3. **行业惯例** — 与 Fountain 格式和 Final Draft XML 的逻辑一致

## 7. 完整示例

```yaml
metadata:
  title: 命运的相遇
  author: ""
  adapter: ""
  genre: 都市情感
  version: '1.0'
  created_at: '2026-06-08T15:00:00'
  source_chapters: 3
  total_scenes: 6
  characters:
    - 林晓
    - 苏然
  synopsis: 广告设计师林晓与产品经理苏然从意外相遇到渐生情愫的都市爱情故事

scenes:
  - scene_number: 1
    scene_heading: "EXT. 城市街道 - DUSK"
    location: 城市街道
    scene_type: EXT
    time_of_day: DUSK
    characters:
      - 林晓
    summary: 傍晚时分，林晓下班走出公司
    lines:
      - line_type: action
        action:
          content: "深秋的傍晚，夕阳将整座城市染成金黄色。林晓推开公司大门，疲惫地走向地铁站。"

  - scene_number: 2
    scene_heading: "INT. 地铁站 - NIGHT"
    location: 地铁站
    scene_type: INT
    time_of_day: NIGHT
    characters:
      - 林晓
      - 苏然
    summary: 苏然匆忙中撞到林晓，摔坏了她的手机
    lines:
      - line_type: action
        action:
          content: "地铁站里人来人往。林晓低头看手机，被匆忙的身影撞了一下。手机摔在地上。"
      - line_type: dialogue
        dialogue:
          character: 苏然
          parenthetical: 慌忙停下
          content: 对不起对不起！
      - line_type: dialogue
        dialogue:
          character: 林晓
          parenthetical: 尽量平静
          content: 你知道这块屏幕多少钱吗？
```

## 8. 与行业标准的关系

| 标准/格式 | 关系 |
|-----------|------|
| **Fountain** | 本 Schema 的对白格式与 Fountain 语法对齐 |
| **Final Draft (.fdx)** | 场景标题行、转场类型等均遵循 Final Draft 惯例 |
| **中国国家标准** | 参考了中国影视剧本的常见格式，如角色名+冒号+对白 |
| **YAML 1.2** | 严格遵循 YAML 1.2 规范，确保跨平台兼容 |

## 9. 版本演进

当前 Schema 版本为 1.0，未来可能的扩展方向：

- **v1.1**：增加 `voiceover`（画外音）和 `montage`（蒙太奇）支持
- **v1.2**：增加 `subtext`（潜台词）字段，用于 AI 分析角色深层动机
- **v2.0**：支持多线叙事结构，增加 `timeline` 和 `subplot` 字段
