# image_toolbox

> 图片批量处理工具箱

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 20
- **函数数**: 1

## 技能描述

图片批量处理工具箱

## 依赖

```bash
pip install Pillow
pip install opencv-python
pip install numpy
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source_dir` | string | `` | 源图片目录路径 (必填) |
| `output_dir` | string | `` | 输出目录路径，默认 ./processed_images |
| `operations` | string | `` | 操作类型，多个操作用逗号分隔 (resize,compress,convert,watermark,crop,rotate,color,thumbnail,grid) |
| `target_format` | string | `` | 目标格式 (jpg/png/webp/bmp/tiff)，默认保持原格式 |
| `width` | integer | `` | 目标宽度 |
| `height` | integer | `` | 目标高度 |
| `quality` | integer | `` | 压缩质量 1-100，默认 85 |
| `watermark_text` | string | `` | 水印文字内容 |
| `watermark_position` | string | `` | 水印位置 (center/top-left/top-right/bottom-left/bottom-right)，默认 bottom-right |
| `watermark_opacity` | float | `` | 水印透明度 0-1，默认 0.7 |
| `crop_x` | integer | `` | 裁剪起始 X 坐标 |
| `crop_y` | integer | `` | 裁剪起始 Y 坐标 |
| `crop_width` | integer | `` | 裁剪宽度 |
| `crop_height` | integer | `` | 裁剪高度 |
| `rotate_angle` | integer | `` | 旋转角度 (90/180/270) |
| `flip_direction` | string | `` | 翻转方向 (horizontal/vertical) |
| `brightness` | float | `` | 亮度调整 (-1.0 到 1.0) |
| `contrast` | float | `` | 对比度调整 (-1.0 到 1.0) |
| `saturation` | float | `` | 饱和度调整 (-1.0 到 1.0) |
| `thumbnail_size` | integer | `` | 缩略图尺寸，默认 200 |
| `grid_cols` | integer | `` | 图册列数，默认 3 |
| `recursive` | boolean | `` | 是否递归处理子目录，默认 true |
| `pattern` | string | `` | 文件匹配模式，默认 *.jpg,*.jpeg,*.png,*.webp,*.bmp,*.tiff |
| `dry_run` | boolean | `` | 预览模式，只显示处理计划不实际处理，默认 false |

## 输出

| 字段 | 说明 |
|------|------|
| `processed_count` | 成功处理文件数 |
| `failed_count` | 失败文件数 |
| `output_dir` | 输出目录路径 |
| `size_reduction` | 文件大小变化百分比 |
| `processing_time` | 处理耗时 |

## 使用方法

```bash
python -m markflow.cli.commands execute image_toolbox [参数]
```

### 示例

```bash
# 批量压缩图片
python -m markflow.cli.commands execute image_toolbox source_dir="./images" operations="compress" quality=85

# 批量调整尺寸
python -m markflow.cli.commands execute image_toolbox source_dir="./images" operations="resize" width=800 height=600

# 批量添加水印
python -m markflow.cli.commands execute image_toolbox source_dir="./images" operations="watermark" watermark_text="2024 MarkFlow"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info image_toolbox
```

## 输出位置

生成的输出保存在 `skills/image_toolbox/output/` 目录下。

---

*文档自动生成于 2026-08-23 17:13:23*