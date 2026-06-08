# 🎬 AI小说转剧本工具

> 一款 AI 辅助剧本创作工具，能将小说文本自动转换为结构化 YAML 剧本，降低改编门槛，提升创作效率。

## ✨ 功能特色

- 📄 **智能章节检测**：自动识别"第X章"、Markdown标题等多种章节格式
- 📖 **AI剧本转换**：调用大模型将小说内容转换为标准剧本格式
- 📝 **结构化YAML输出**：符合行业标准的剧本YAML Schema，可读、可编辑、可验证
- 🤖 **实时进度反馈**：流式转换，实时显示每章转换进度
- 💾 **在线预览导出**：转换完成后可预览、复制、下载YAML文件
- 🧩 **多模型支持**：兼容OpenAI、DeepSeek、智谱AI等大模型API
- 📐 **规则引擎**：离线模式，纯正则转换，零成本免费使用
- ⚡ **批量处理**：支持大文件（1000+章节）高效转换

## 📐 架构设计

```
├── main.py                 # FastAPI 入口
├── backend/
│   ├── app.py              # API 路由
│   ├── config.py           # 内置模型配置
│   ├── parser/             # 小说解析模块
│   │   ├── txt_parser.py   # TXT 文件解析（自动编码检测）
│   │   ├── docx_parser.py  # DOCX 文件解析
│   │   └── chapter_detector.py  # 章节自动检测
│   ├── converter/          # AI 转换模块
│   │   ├── llm_client.py   # 大模型 API 封装
│   │   ├── prompt_builder.py    # Prompt 工程
│   │   ├── screenplay_converter.py  # 转换主逻辑
│   │   └── rule_converter.py    # 规则引擎（离线）
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
    ├── test_parser.py      # 解析器测试（7个）
    ├── test_converter.py   # 转换器测试（6个）
    └── test_schema.py      # Schema测试（6个）
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

- Python 3.10+（推荐 3.14）
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> 💡 国内用户可使用清华镜像加速：
> ```bash
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
> ```

### 3. 启动服务

```bash
python main.py
```

### 4. 打开浏览器

访问 http://127.0.0.1:8000

## 📋 使用流程

1. **上传小说文件** — 支持 `.txt` 和 `.docx` 格式
2. **选择转换方式** — 规则引擎（免费离线）或 AI 模型
3. **一键转换** — AI 自动生成结构化剧本
4. **预览导出** — 复制或下载 YAML 文件

## 🧪 运行测试

```bash
python -m pytest tests/ -v
```

测试覆盖：
- 解析器测试：7 个用例
- 转换器测试：6 个用例
- Schema测试：6 个用例
- **总计：19 个用例全部通过**

## 📄 License

MIT License
