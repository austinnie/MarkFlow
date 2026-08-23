# image_viewer

## 描述
功能完整的图片查看器和管理器，替代 Windows 自带图片查看器

## 目的


## 输入
- **action**: 操作类型 (browse/view/info/edit/manage/slideshow/search/export/print)
- **source_dir**: 图片目录路径
- **file**: 单个图片文件路径
- **view_mode**: 查看模式 (grid/list/single)，默认 grid
- **sort_by**: 排序方式 (name/date/size/type)，默认 name
- **sort_order**: 排序顺序 (asc/desc)，默认 asc
- **filter**: 过滤条件 (all/images/videos/starred)，默认 all
- **thumbnail_size**: 缩略图大小，默认 200
- **slideshow_interval**: 幻灯片间隔(秒)，默认 3
- **fullscreen**: 是否全屏，默认 false
- **tags**: 标签列表，逗号分隔
- **star**: 星标 0-5
- **rename_pattern**: 重命名模式
- **export_format**: 导出格式 (jpg/png/webp)
- **export_quality**: 导出质量 1-100，默认 85
- **export_size**: 导出尺寸，如 800x600

## 输出
- **files**: 文件列表
- **current_file**: 当前查看的文件
- **file_info**: 文件详细信息
- **thumbnails**: 缩略图列表
- **stats**: 统计信息
- **export_path**: 导出路径
- **message**: 操作结果消息

## 步骤
无

## 依赖
- Pillow
- tkinter
- pyexiv2
- watchdog

## 版本
1.0.0
