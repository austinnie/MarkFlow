# MarkFlow

> 🚀 从 Markdown 到可执行技能的工作流引擎

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

MarkFlow 是一个轻量级的技能生成框架，让你用 **Markdown** 编写技能描述，自动生成可执行的 **Python** 代码。

## ✨ 核心特性

- 📝 **Markdown 驱动**：用自然语言编写技能描述，无需编写重复的代码框架
- 🚀 **自动生成代码**：从 Markdown 自动生成完整的 Python 可执行代码
- 🔌 **热加载支持**：动态加载和更新技能，开发无需重启
- 🎨 **内置模板**：基础、数据处理、API 客户端等多种模板开箱即用
- 💻 **CLI 工具**：便捷的命令行操作，一行命令完成构建和执行
- 🖥️ **GUI 界面**：图形化操作界面，参数分组显示，一键执行
- 📦 **模块化设计**：每个技能独立目录，输出隔离，易于管理

## 📦 已安装技能

共 **10** 个技能：

| 技能 | 描述 | 版本 |
|------|------|------|
| `code_reviewer` | AI 代码审查，发现问题和安全风险 | 1.0.0 |
| `doc_generator` | 代码文档自动生成器，从 Python 代码自动生成 API 文档 | 1.0.0 |
| `image_toolbox` | 图片批量处理工具箱 | 1.0.0 |
| `image_viewer` | 功能完整的图片查看器和管理器，替代 Windows 自带图片查看器 | 1.0.0 |
| `language_learner` | AI 驱动的多语言学习助手，支持单词、语法、句子学习，集成语音发音 | 1.0.0 |
| `music_player` | AI 智能歌单生成和音乐管理 | 1.0.0 |
| `news_aggregator` | RSS 新闻抓取 + AI 摘要生成 | 1.0.0 |
| `novel_writer` | 使用本地 Ollama 大模型自动写小说 | 1.0.0 |
| `voice_assistant` | 语音合成（TTS）和语音识别（STT）助手 | 1.0.0 |

## 🎯 代表性技能

### 📖 AI 小说生成器

使用本地 Ollama 大模型自动写小说

```bash
python -m markflow.cli.commands execute novel_writer genre="科幻" title="星际行者" outline="探索宇宙" chapter_count=3
```

📖 [详细文档](skills/novel_writer/README.md)

### 🎙️ 语音助手

语音合成（TTS）和语音识别（STT）助手

```bash
python -m markflow.cli.commands execute voice_assistant action="tts" text="你好，欢迎使用 MarkFlow"
```

📖 [详细文档](skills/voice_assistant/README.md)

### 🖼️ 图片工具箱

图片批量处理工具箱

```bash
python -m markflow.cli.commands execute image_toolbox source_dir="./images" operations="compress" quality=85
```

📖 [详细文档](skills/image_toolbox/README.md)

### 👁️ 图片查看器

功能完整的图片查看器和管理器，替代 Windows 自带图片查看器

```bash
python -m markflow.cli.commands execute image_viewer action="browse" source_dir="./images"
```

📖 [详细文档](skills/image_viewer/README.md)

## 🏗️ 框架架构

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Markdown   │───▶│   Parser    │───▶│  Generator  │───▶│   Skill     │
│  描述文件    │    │  解析器     │    │  代码生成器  │    │  可执行代码  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   User      │◀───│  Executor   │◀───│  Registry   │◀───│   Skill     │
│   用户执行   │    │  执行器     │    │  注册中心   │    │  实例化     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 核心模块

| 模块 | 职责 |
|------|------|
| **Executor** | 创建技能实例并执行 |
| **Generator** | 从规格生成完整的 Python 可执行代码 |
| **Parser** | 解析 Markdown，提取技能规格（名称、参数、步骤等） |
| **Registry** | 管理已注册的技能，支持动态加载 |
| **CLI** | 命令行交互接口 |
| **GUI** | 图形化操作界面 |

## 📂 项目结构

```
MarkFlow/
├── markflow/                         # 框架核心
│   ├── core/                         # 核心模块
│   │   ├── parser.py                 # Markdown 解析器
│   │   ├── generator.py              # 代码生成器
│   │   ├── registry.py               # 技能注册中心
│   │   └── executor.py               # 技能执行器
│   ├── cli/                          # CLI 工具
│   │   └── commands.py
│   ├── gui/                          # GUI 图形界面
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── launcher.py
│   ├── templates/                    # 模板管理
│   │   ├── base.py                   # 模板管理器
│   │   └── skills/                   # 技能定义模板
│   └── utils/                        # 工具函数
│       └── code_collect.py           # 代码收集/打包
├── scripts/                          # 工具脚本
│   ├── novel_generator.py            # 小说生成
│   ├── novel_scheduler.py            # 小说定时任务
│   ├── generate_skill_readme.py      # 技能 README 生成
│   └── markflow_gui.py               # GUI 启动
├── skills/                           # 已安装的技能
│   ├── code_reviewer/                 # 代码审查助手
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── doc_generator/                 # doc_generator
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── image_toolbox/                 # ImageToolbox
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── image_viewer/                 # image_viewer
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── language_learner/                 # 语言学习助手
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── music_player/                 # 音乐播放器
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── news_aggregator/                 # 新闻聚合器
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── novel_writer/                 # novel_writer_ollama
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
│   ├── voice_assistant/                 # voice_assistant
│   │   ├── skill.py              # 可执行代码
│   │   ├── meta.json             # 元数据
│   │   ├── skill.md              # 技能文档
│   │   └── output/               # 输出目录
├── collected_code/                   # 代码快照输出
└── README.md                         # 项目文档
```

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/austinnie/MarkFlow.git
cd MarkFlow
```

### 创建你的第一个技能

**1. 编写技能描述** `hello.md`

```markdown
# HelloWorld

## 描述
一个简单的问候技能

## 输入
- name: string: 要问候的名字

## 输出
- greeting: 问候语

## 步骤
1. 获取名字
2. 生成问候语
3. 返回结果
```

**2. 构建技能**

```bash
python -m markflow.cli.commands build hello.md
```

**3. 执行技能**

```bash
python -m markflow.cli.commands execute HelloWorld name=MarkFlow
```

输出：

```json
{
  "status": "success",
  "result": {
    "greeting": "Hello, MarkFlow!"
  }
}
```

## 📖 CLI 命令

```bash
python -m markflow.cli.commands --help
```

| 命令 | 说明 | 示例 |
|------|------|------|
| `build <file>` | 从 Markdown 文件构建技能 | `build weather.md` |
| `execute <skill>` | 执行技能 | `execute sd_image_generator prompt="test"` |
| `list` | 列出所有已注册的技能 | `list` |
| `info <skill>` | 查看技能详情 | `info sd_image_generator` |
| `generate -t <type> -n <name>` | 从模板生成技能 | `generate -t data -n data_cleaner` |
| `remove <skill>` | 删除技能 | `remove sd_image_generator` |

## 🖥️ GUI 图形界面

```bash
python scripts/markflow_gui.py
```

或

```bash
python -m markflow.gui
```

### GUI 功能

| 功能 | 说明 |
|------|------|
| 技能列表 | 左侧显示所有已安装技能 |
| 参数配置 | 选择技能后自动生成参数输入框 |
| 分组折叠 | 参数按功能分组，可折叠/展开 |
| 一键执行 | 填写参数后点击执行按钮 |
| 日志输出 | 彩色日志显示执行过程和结果 |

## 🤝 贡献

欢迎贡献！

### 贡献方式

1. **报告 Bug**：在 Issues 中详细描述问题
2. **提交代码**：通过 Pull Request 提交改进
3. **完善文档**：改进 README 或添加示例
4. **提出建议**：在 Issues 中讨论新功能

### 开发流程

1. Fork 本仓库
2. 创建你的特性分支
3. 提交你的修改
4. 推送到分支
5. 开启一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证

## 🌟 支持

如果这个项目对你有帮助，请给一个 Star ⭐️

---

*文档自动生成于 2026-08-24 17:05:31*

Made with ❤️ by MarkFlow Team