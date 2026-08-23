# image_viewer

> 功能完整的图片查看器和管理器，替代 Windows 自带图片查看器

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 18
- **函数数**: 1

## 技能描述

功能完整的图片查看器和管理器，替代 Windows 自带图片查看器

## 依赖

```bash
pip install Pillow
pip install tkinter
pip install pyexiv2
pip install watchdog
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | string | `` | 操作类型 (browse/view/info/edit/manage/slideshow/search/export/print) |
| `source_dir` | string | `` | 图片目录路径 |
| `file` | string | `` | 单个图片文件路径 |
| `view_mode` | string | `` | 查看模式 (grid/list/single)，默认 grid |
| `sort_by` | string | `` | 排序方式 (name/date/size/type)，默认 name |
| `sort_order` | string | `` | 排序顺序 (asc/desc)，默认 asc |
| `filter` | string | `` | 过滤条件 (all/images/videos/starred)，默认 all |
| `thumbnail_size` | integer | `` | 缩略图大小，默认 200 |
| `slideshow_interval` | integer | `` | 幻灯片间隔(秒)，默认 3 |
| `fullscreen` | boolean | `` | 是否全屏，默认 false |
| `tags` | string | `` | 标签列表，逗号分隔 |
| `star` | integer | `` | 星标 0-5 |
| `rename_pattern` | string | `` | 重命名模式 |
| `export_format` | string | `` | 导出格式 (jpg/png/webp) |
| `export_quality` | integer | `` | 导出质量 1-100，默认 85 |
| `export_size` | string | `` | 导出尺寸，如 800x600 |

## 输出

| 字段 | 说明 |
|------|------|
| `files` | 文件列表 |
| `current_file` | 当前查看的文件 |
| `file_info` | 文件详细信息 |
| `thumbnails` | 缩略图列表 |
| `stats` | 统计信息 |
| `export_path` | 导出路径 |
| `message` | 操作结果消息 |

## 使用方法

```bash
python -m markflow.cli.commands execute image_viewer [参数]
```

### 示例

```bash
# 浏览图片目录
python -m markflow.cli.commands execute image_viewer action="browse" source_dir="./images"

# 幻灯片播放
python -m markflow.cli.commands execute image_viewer action="slideshow" source_dir="./images" slideshow_interval=5
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info image_viewer
```

## 输出位置

生成的输出保存在 `skills/image_viewer/output/` 目录下。

---

*文档自动生成于 2026-08-23 17:13:23*