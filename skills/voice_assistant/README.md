# 语音助手 (VoiceAssistant)

> 文字转语音（TTS）和语音转文字（STT）工具

## 📋 基本信息

| 属性 | 值 |
|------|-----|
| 技能名称 | `VoiceAssistant` |
| 版本 | 1.0.0 |
| 类型 | AI 生成 |
| 难度 | ⭐⭐ |
| 实用性 | ⭐⭐⭐⭐ |
| 趣味性 | ⭐⭐⭐⭐⭐ |
| 依赖 | edge-tts, openai-whisper, mutagen, ffmpeg |

## 🎯 功能说明

- **文字转语音 (TTS)**：将文本转换为语音，支持多种语音类型
- **语音转文字 (STT)**：将音频文件转换为文本
- **文章朗读**：支持从文件读取长文本并自动分段朗读
- **语音列表**：查看所有可用的语音类型
- **音频合并**：长文本自动分段生成后合并为一个完整音频文件

## 📝 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `action` | string | ✅ | - | 操作类型：`tts` / `stt` / `list_voices` |
| `text` | string | ⚠️ | - | 要合成的文本（与 `text_file` 二选一） |
| `text_file` | string | ⚠️ | - | 文本文件路径（与 `text` 二选一） |
| `voice` | string | ❌ | zh-CN-XiaoxiaoNeural | 语音类型 |
| `speed` | float | ❌ | 1.0 | 语速（0.5-2.0） |
| `output_file` | string | ❌ | 自动生成 | 输出文件路径 |
| `language` | string | ❌ | zh-CN | 识别语言（STT 使用） |
| `chunk_size` | integer | ❌ | 500 | 每段最大字数 |
| `auto_split` | boolean | ❌ | true | 是否自动按句子分割 |

## 📤 输出说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `audio_path` | string | 生成的音频文件路径 |
| `audio_paths` | list | 分段音频文件路径列表（长文本时） |
| `duration` | float | 音频时长（秒） |
| `transcript` | string | 语音识别结果文本 |
| `voices` | list | 可用语音列表 |

## 🚀 快速开始

### 安装依赖

```bash
# 安装 Python 依赖
pip install edge-tts openai-whisper mutagen

# 安装 ffmpeg（用于音频合并）
# Windows
winget install FFmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### 构建技能

```bash
python -m markflow.cli.commands build examples/voice_assistant.md
```

### 文字转语音

```bash
python -m markflow.cli.commands execute VoiceAssistant action="tts" text="你好，欢迎使用语音助手"
```

### 指定语音和语速

```bash
python -m markflow.cli.commands execute VoiceAssistant action="tts" text="今天天气真好" voice="zh-CN-YunxiNeural" speed=1.2
```

### 朗读文章（从文件读取）

```bash
python -m markflow.cli.commands execute VoiceAssistant action="tts" text_file="./article.txt"
```

### 整篇朗读（不分段）

```bash
python -m markflow.cli.commands execute VoiceAssistant action="tts" text_file="./article.txt" chunk_size=10000
```

### 列出可用语音

```bash
python -m markflow.cli.commands execute VoiceAssistant action="list_voices"
```

## 📊 可用语音

| 语音名称 | 语言 | 性别 |
|---------|------|------|
| zh-CN-XiaoxiaoNeural | 中文(简体) | 女 |
| zh-CN-XiaoyiNeural | 中文(简体) | 女 |
| zh-CN-YunjianNeural | 中文(简体) | 男 |
| zh-CN-YunxiNeural | 中文(简体) | 男 |
| zh-CN-YunxiaNeural | 中文(简体) | 男 |
| en-US-JennyNeural | 英语(美国) | 女 |
| en-US-GuyNeural | 英语(美国) | 男 |
| en-US-AriaNeural | 英语(美国) | 女 |
| ja-JP-NanamiNeural | 日语 | 女 |
| ko-KR-SunHiNeural | 韩语 | 女 |

## ⚠️ 注意事项

- TTS 需要网络连接（edge-tts 调用 Azure 服务）
- STT 使用本地 Whisper 模型，首次运行会下载模型
- 音频输出保存在 `audio_output/` 目录
- ffmpeg 用于合并分段音频，建议安装以获得完整功能

## 📂 文件位置

| 文件 | 路径 |
|------|------|
| 技能描述 | `examples/voice_assistant.md` |
| 技能代码 | `skills/VoiceAssistant.py` |
| 元数据 | `skills/VoiceAssistant.meta.json` |

---

**更新日期**: 2026-08-22