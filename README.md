# MarkFlow

> 🚀 从 Markdown 到可执行技能的工作流引擎

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

MarkFlow 是一个轻量级的技能生成框架，让你用 **Markdown** 编写技能描述，自动生成可执行的 **Python** 代码。

## ✨ 特性

- 📝 **Markdown 驱动**：用自然语言编写技能描述，无需编写重复的代码框架
- 🚀 **自动生成代码**：从 Markdown 自动生成完整的 Python 可执行代码
- 🔌 **热加载支持**：动态加载和更新技能，开发无需重启
- 🎨 **内置模板**：基础、数据处理、API 客户端等多种模板开箱即用
- 💻 **CLI 工具**：便捷的命令行操作，一行命令完成构建和执行
- 📦 **模块化设计**：灵活扩展和集成，支持自定义模板
- 📊 **代码收集**：自动收集项目代码，生成统计报告
- 🖥️ **GUI 界面**：图形化操作界面，参数分组显示，一键执行

## 🎯 使用场景

| 场景 | 示例 |
|------|------|
| 🎨 AI 图片生成 | 使用 Stable Diffusion 模型生成图片 |
| 🖼️ 图片处理 | 批量压缩、格式转换、添加水印、图片查看管理 |
| 📊 数据处理 | CSV 清洗、数据统计分析、ETL 流水线 |
| 🌐 API 集成 | GitHub、OpenAI、天气 API 等客户端封装 |
| 🤖 自动化任务 | 定时任务、批量处理、报告生成 |
| 🔧 自定义工具 | 任意 Python 功能封装为可复用技能 |

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/austinnie/MarkFlow.git
cd MarkFlow
```

### 创建你的第一个技能

**1. 编写技能描述** `hello.md`

```markdown
# hello_world

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

就这么简单！🎉

## 📖 CLI 命令

```bash
python -m markflow.cli.commands --help
```

| 命令 | 说明 | 示例 |
|------|------|------|
| `build <file>` | 从 Markdown 文件构建技能 | `build weather.md` |
| `execute <skill>` | 执行技能 | `execute WeatherFetcher city=Beijing` |
| `list` | 列出所有已注册的技能 | `list` |
| `info <skill>` | 查看技能详情 | `info WeatherFetcher` |
| `generate -t <type> -n <name>` | 从模板生成技能 | `generate -t data -n data_cleaner` |
| `remove <skill>` | 删除技能 | `remove WeatherFetcher` |

**注意**：所有命令前都需要加上 `python -m markflow.cli.commands`

### 命令示例

```bash
# 构建技能
python -m markflow.cli.commands build examples/sd_image_generator.md

# 执行技能
python -m markflow.cli.commands execute SDImageGenerator prompt="beautiful sunset" model_name="sd-v1-5-tiny.safetensors"

# 列出所有技能
python -m markflow.cli.commands list

# 查看技能详情
python -m markflow.cli.commands info SDImageGenerator

# 从模板生成
python -m markflow.cli.commands generate -t data -n data_cleaner -d "数据清洗工具"

# 删除技能
python -m markflow.cli.commands remove data_cleaner
```

## 🎨 示例技能：SD 图片生成器

这是 MarkFlow 的第一个实战技能，使用本地 Stable Diffusion 模型生成图片。

### 安装依赖

```bash
pip install diffusers torch transformers accelerate safetensors Pillow
```

### 构建技能

```bash
python -m markflow.cli.commands build examples/sd_image_generator.md
```

### 执行技能生成图片

```bash
python -m markflow.cli.commands execute SDImageGenerator prompt="a beautiful sunset over mountains" model_name="sd-v1-5-tiny.safetensors"
```

执行过程会输出详细的日志，展示每一步的执行状态：

```
2026-08-21 19:52:03,871 - Sdimagegenerator - INFO - 执行技能: SDImageGenerator (v1.0.0)
2026-08-21 19:52:03,871 - Sdimagegenerator - INFO - 执行步骤: 验证输入参数
2026-08-21 19:52:03,879 - Sdimagegenerator - INFO - 执行步骤: 检查模型文件是否存在
2026-08-21 19:52:03,880 - Sdimagegenerator - INFO - 执行步骤: 加载选定的模型
...
✅ 执行成功!
```

生成的图片保存在 `generated_images/` 目录下。

### 技能描述文件

`sd_image_generator.md` 的内容如下：

```markdown
# SDImageGenerator

## 描述
使用本地 Stable Diffusion 模型生成图片的技能

## 输入
- prompt: string: 图片描述提示词 (必填)
- negative_prompt: string: 负面提示词 (可选)
- model_name: string: 模型文件名，默认 sd-v1-5-tiny.safetensors
- width: integer: 图片宽度，默认 512
- height: integer: 图片高度，默认 512
- steps: integer: 采样步数，默认 20
- cfg_scale: float: 引导强度，默认 7.0
- seed: integer: 随机种子，-1 表示随机
- batch_size: integer: 一次生成数量，默认 1

## 输出
- image_paths: 生成的图片路径列表
- parameters: 使用的生成参数
- generation_time: 生成耗时

## 步骤
1. 验证输入参数
2. 检查模型文件是否存在
3. 加载选定的模型
4. 设置随机种子
5. 执行图片生成
6. 保存生成的图片
7. 返回生成结果信息

## 依赖
- diffusers
- torch
- transformers
- accelerate
- safetensors
- Pillow
```

## 🎨 示例技能：AI 小说生成器

这是 MarkFlow 的第二个实战技能，使用本地 Ollama 大模型自动写小说，支持断点续写和连载。

### 安装依赖

```bash
# 首先安装 Ollama（如果未安装）
# 访问 https://ollama.ai 下载安装

# 下载推荐模型
ollama pull qwen2.5:7b
# 或轻量模型（速度快）
ollama pull qwen2.5:1.5b
```

### 构建技能

```bash
python -m markflow.cli.commands build examples/novel_writer_ollama.md
```

### 执行技能生成小说

```bash
# 首次生成 - 创建一部新小说
python -m markflow.cli.commands execute NovelWriterOllama genre="科幻" title="星际行者" outline="一个普通少年意外获得星际航行能力，在宇宙中探索未知文明" characters="主角阿星，16岁，好奇心强；AI助手小智，幽默风趣" chapter_count=3 model="qwen2.5:7b"
```

### 断点续写

```bash
python -m markflow.cli.commands execute NovelWriterOllama genre="科幻" title="星际行者" outline="一个普通少年意外获得星际航行能力" characters="主角阿星，16岁" chapter_count=5 model="qwen2.5:7b" continue_from="generated_novels/星际行者_20260821_xxx.txt"
```

### 连载模式

多次运行追加新章节：

```bash
# 第1次：写1-5章
python -m markflow.cli.commands execute NovelWriterOllama genre="科幻" title="星际行者" outline="..." characters="..." chapter_count=5 model="qwen2.5:7b"

# 第2次：续写6-10章
python -m markflow.cli.commands execute NovelWriterOllama genre="科幻" title="星际行者" outline="..." characters="..." chapter_count=10 model="qwen2.5:7b" continue_from="generated_novels/星际行者_xxx.txt"

# 第3次：续写11-15章
python -m markflow.cli.commands execute NovelWriterOllama genre="科幻" title="星际行者" outline="..." characters="..." chapter_count=15 model="qwen2.5:7b" continue_from="generated_novels/星际行者_xxx.txt"
```

## 🎨 示例技能：图片工具箱

这是 MarkFlow 的第三个实战技能，支持批量图片处理。

### 构建技能

```bash
python -m markflow.cli.commands build examples/image_toolbox.md
```

### 执行技能

```bash
# 批量压缩图片
python -m markflow.cli.commands execute ImageToolbox source_dir="./images" operations="compress" quality=85

# 批量调整尺寸 + 压缩
python -m markflow.cli.commands execute ImageToolbox source_dir="./images" operations="resize,compress" width=800 quality=80

# 批量添加水印
python -m markflow.cli.commands execute ImageToolbox source_dir="./images" operations="watermark" watermark_text="© 2024" output_dir="./watermarked"
```

## 🎨 示例技能：图片查看器

这是 MarkFlow 的第四个实战技能，替代 Windows 自带图片查看器。

### 构建技能

```bash
python -m markflow.cli.commands build examples/image_viewer.md
```

### 执行技能

```bash
# 浏览目录
python -m markflow.cli.commands execute ImageViewer action="browse" source_dir="./images"

# 查看图片信息
python -m markflow.cli.commands execute ImageViewer action="info" file="./images/photo.jpg"

# 用系统默认程序打开图片
python -m markflow.cli.commands execute ImageViewer action="view" file="./images/photo.jpg"

# 幻灯片播放
python -m markflow.cli.commands execute ImageViewer action="slideshow" source_dir="./images" slideshow_interval=5

# 批量导出
python -m markflow.cli.commands execute ImageViewer action="export" source_dir="./images" export_format="webp" export_quality=80
```

### 更多示例技能

**数据处理技能**：

```markdown
# data_cleaner

## 描述
CSV 数据清洗工具

## 输入
- source: string: 数据源路径
- output: string: 输出路径

## 输出
- cleaned_data: 清洗后的数据
- report: 清洗报告

## 步骤
1. 读取数据
2. 处理缺失值
3. 去除重复
4. 保存结果

## 依赖
- pandas
- numpy
```

**API 客户端**：

```markdown
# github_client

## 描述
GitHub API 客户端

## 输入
- repository: string: 仓库名称
- action: string: 操作类型 (info, stars, forks)

## 输出
- result: API 响应数据

## 步骤
1. 构建 API 请求
2. 发送 HTTP 请求
3. 解析响应
4. 返回数据

## 依赖
- requests
```

## 🏗️ 架构

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

### 核心模块说明

| 模块 | 职责 |
|------|------|
| **Parser** | 解析 Markdown，提取技能规格（名称、参数、步骤等） |
| **Generator** | 从规格生成完整的 Python 可执行代码 |
| **Registry** | 管理已注册的技能，支持动态加载 |
| **Executor** | 创建技能实例并执行 |
| **CLI** | 命令行交互接口 |
| **Templates** | 内置模板管理和自定义模板支持 |

## 🖥️ GUI 图形界面

MarkFlow 提供了图形化操作界面，让你无需记忆命令，点击即可完成技能操作。

### 启动 GUI

```bash
# 方式1：使用启动脚本
python markflow_gui.py

# 方式2：直接运行模块
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

### GUI 界面预览

```
┌─────────────────────────────────────────────────────────────────┐
│  🚀 MarkFlow 技能管理                    v0.1.0               │
│  [🔄刷新] [📂打开技能目录] [❓帮助]                          │
├────────────┬────────────────────────────────────────────────────┤
│ 📦 技能列表 │ 📋 技能信息                                      │
│ ────────── │ ───────────────────────────────────────────────── │
│ Sdimage... │ 📌 Sdimagegenerator                             │
│ NovelW...  │ 使用本地 Stable Diffusion 模型生成图片           │
│ DocGene..  │ 依赖: diffusers, torch, transformers            │
│ ImageTo..  │ ───────────────────────────────────────────────── │
│ ImageVi..  │ ⚙️ 参数配置                                      │
│            │ ┌──────────────────────────────────────────────┐ │
│            │ │ ▼ 📌 基础参数                               │ │
│            │ │   prompt *  [________________]              │ │
│            │ │   model_name [sd-v1-5-tiny.safetensors]    │ │
│            │ │ ▶ 📐 尺寸参数                              │ │
│            │ │ ▶ ⚙️ 生成参数                              │ │
│            │ └──────────────────────────────────────────────┘ │
│            │ [▶️ 执行技能]  [🗑️ 清空输出]                    │
│            │ ───────────────────────────────────────────────── │
│            │ 📋 执行日志                                      │
│            │ [23:45:01] 🚀 执行技能: Sdimagegenerator        │
│            │ [23:45:01] ✅ 执行成功!                         │
├────────────┴────────────────────────────────────────────────────┤
│  ✅ 就绪                                      📦 共 5 个技能 │
└────────────────────────────────────────────────────────────────┘
```

## 📂 项目结构

```
MarkFlow/
├── markflow/                    # 框架核心
│   ├── core/                    # 核心模块
│   │   ├── parser.py            # Markdown 解析器
│   │   ├── generator.py         # 代码生成器
│   │   ├── registry.py          # 技能注册中心
│   │   └── executor.py          # 技能执行器
│   ├── cli/                     # CLI 工具
│   │   └── commands.py
│   ├── gui/                     # 🖥️ GUI 图形界面
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── launcher.py
│   ├── templates/               # 模板管理
│   │   └── base.py
│   └── utils/                   # 工具函数
│       └── code_collect.py
├── examples/                    # 示例技能
│   ├── sd_image_generator.md    # SD 图片生成
│   ├── novel_writer_ollama.md   # AI 小说生成
│   ├── image_toolbox.md         # 图片工具箱
│   └── image_viewer.md          # 图片查看器
├── skills/                      # 生成的技能（自动创建）
├── collected_code/              # 代码收集输出（自动创建）
├── generated_images/            # 图片生成输出（自动创建）
├── generated_novels/            # 小说生成输出（自动创建）
├── markflow_gui.py              # 🖥️ GUI 启动脚本
└── README.md
```

## 🤝 贡献

欢迎贡献！我们非常欢迎各种形式的贡献。

### 贡献方式

1. **报告 Bug**：在 Issues 中详细描述问题
2. **提交代码**：通过 Pull Request 提交改进
3. **完善文档**：改进 README 或添加示例
4. **提出建议**：在 Issues 中讨论新功能

### 开发流程

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的修改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 📄 许可证

本项目采用 MIT 许可证

## 🌟 支持

如果这个项目对你有帮助，请给一个 Star ⭐️

---

**MarkFlow** - 让技能编写像写文档一样简单 ✨

Made with ❤️ by MarkFlow Team