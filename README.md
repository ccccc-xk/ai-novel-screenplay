# 🎬 AI小说转剧本工具

> 一款 AI 辅助剧本创作工具，能将小说文本自动转换为结构化 YAML 剧本，降低改编门槛，提升创作效率。

## ✨ 功能特色

- **智能章节检测**：自动识别"第X章"、Markdown标题等多种章节格式
- **AI剧本转换**：调用大模型将小说内容转换为标准剧本格式
- **结构化YAML输出**：符合行业标准的剧本YAML Schema，可读、可编辑、可验证
- **实时进度反馈**：流式转换，实时显示每章转换进度
- **在线预览导出**：转换完成后可预览、复制、下载YAML文件
- **多模型支持**：兼容OpenAI、DeepSeek、智谱AI等大模型API

## 📐 架构设计

```
├── main.py                 # FastAPI 入口
├── backend/
│   ├── app.py              # API 路由
│   ├── parser/             # 小说解析模块
│   │   ├── txt_parser.py   # TXT 文件解析（自动编码检测）
│   │   ├── docx_parser.py  # DOCX 文件解析
│   │   └── chapter_detector.py  # 章节自动检测
│   ├── converter/          # AI 转换模块
│   │   ├── llm_client.py   # 大模型 API 封装
│   │   ├── prompt_builder.py    # Prompt 工程
│   │   └── screenplay_converter.py  # 转换主逻辑
│   ├── schema/             # YAML Schema 定义
│   │   └── screenplay_schema.py
│   └── models/             # Pydantic 数据模型
│       └── models.py
├── frontend/               # 前端页面
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── docs/
│   └── yaml-schema.md      # YAML Schema 设计文档
├── examples/               # 示例文件
│   ├── sample_novel.txt    # 示例小说（3章）
│   └── sample_output.yaml  # 示例输出
└── tests/                  # 测试用例
```

## 🛠️ 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| **后端框架** | FastAPI | 高性能异步 Web 框架 |
| **AI 接口** | OpenAI Python SDK | 兼容多种大模型 API |
| **文件解析** | python-docx, chardet | 支持 TXT/DOCX，自动编码检测 |
| **数据验证** | Pydantic v2 | 类型安全的数据模型 |
| **YAML处理** | PyYAML | YAML 序列化/反序列化 |
| **前端** | 原生 HTML/CSS/JS | 零依赖，轻量高效 |
| **测试** | pytest | 单元测试框架 |

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- 一个大模型 API Key（OpenAI / DeepSeek / 智谱AI 等）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

服务启动后访问 http://localhost:8000

### 4. 使用流程

1. **上传小说文件**：支持 .txt 和 .docx 格式，系统自动检测章节结构
2. **配置 API**：输入 API Key、选择模型
3. **开始转换**：AI 逐章分析并转换为剧本格式
4. **预览导出**：在线查看 YAML 剧本，复制或下载

## 📝 YAML Schema 说明

详细的 Schema 设计文档请参阅 [docs/yaml-schema.md](docs/yaml-schema.md)

### 核心结构概览

```yaml
metadata:           # 元数据
  title: 剧本标题
  author: 原作者
  genre: 类型题材
  characters: [角色列表]
  synopsis: 故事梗概

scenes:             # 场景列表
  - scene_number: 1
    scene_heading: "INT/EXT. 地点 - 时间"
    location: 地点
    scene_type: INT/EXT
    time_of_day: DAY/NIGHT
    characters: [出场角色]
    lines:          # 场景内容
      - line_type: action     # 动作描写
      - line_type: dialogue   # 对白
      - line_type: transition # 转场
```

## 📖 示例

项目提供了完整的示例文件：

- [examples/sample_novel.txt](examples/sample_novel.txt) — 3章示例小说《命运的相遇》
- [examples/sample_output.yaml](examples/sample_output.yaml) — 对应的YAML剧本输出

## 🧪 测试

```bash
pytest tests/ -v
```

## 📄 License

MIT License
