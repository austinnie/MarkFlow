# sd_image_generator

> 利用本地 Stable Diffusion 模型，根据文本描述生成高质量图片

## 描述

利用本地 Stable Diffusion 模型，根据文本描述生成高质量图片

## 核心功能

1. 文本生图 - 根据提示词生成高质量图片
2. 参数控制 - 支持宽度、高度、步数、引导强度等参数
3. 批量生成 - 支持一次生成多张图片
4. 模型切换 - 支持切换不同的 SD 模型
5. 随机种子 - 支持固定种子或随机种子

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `prompt` | string | 是 |  | 图片描述提示词 |
| `negative_prompt` | string | 否 |  | 负面提示词 |
| `model_name` | string | 否 | sd-v1-5-tiny.safetensors | 使用的模型文件名 |
| `width` | integer | 否 | 512 | 生成图片宽度，范围 256-1024 |
| `height` | integer | 否 | 512 | 生成图片高度，范围 256-1024 |
| `steps` | integer | 否 | 20 | 采样步数，范围 10-50 |
| `cfg_scale` | float | 否 | 7.0 | 提示词引导强度，范围 1.0-20.0 |
| `seed` | integer | 否 | -1 | 随机种子，-1 表示随机 |
| `output_dir` | string | 否 | ./generated_images | 输出目录 |
| `batch_size` | integer | 否 | 1 | 一次生成数量，范围 1-4 |
| `scheduler` | string | 否 | ddim | 采样调度器 |

## 输出

| 字段 | 说明 |
|------|------|
| `image_paths` | 生成的图片路径列表 |
| `parameters` | 使用的生成参数 |
| `model_used` | 使用的模型名称 |
| `generation_time` | 生成耗时(秒) |
| `generated_at` | 生成时间 |

## 使用方法

```bash
python -m markflow.cli.commands execute sd_image_generator [参数]
```

## 依赖安装

```bash
pip install diffusers
pip install torch
pip install transformers
pip install accelerate
pip install safetensors
pip install Pillow
```

---

*文档生成于 2026-08-28 18:51:14*