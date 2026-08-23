# ImageToolbox

## 描述
图片批量处理工具箱

## 目的


## 输入
- **source_dir**: 源图片目录路径 (必填)
- **output_dir**: 输出目录路径，默认 ./processed_images
- **operations**: 操作类型，多个操作用逗号分隔 (resize,compress,convert,watermark,crop,rotate,color,thumbnail,grid)
- **target_format**: 目标格式 (jpg/png/webp/bmp/tiff)，默认保持原格式
- **width**: 目标宽度
- **height**: 目标高度
- **quality**: 压缩质量 1-100，默认 85
- **watermark_text**: 水印文字内容
- **watermark_position**: 水印位置 (center/top-left/top-right/bottom-left/bottom-right)，默认 bottom-right
- **watermark_opacity**: 水印透明度 0-1，默认 0.7
- **crop_x**: 裁剪起始 X 坐标
- **crop_y**: 裁剪起始 Y 坐标
- **crop_width**: 裁剪宽度
- **crop_height**: 裁剪高度
- **rotate_angle**: 旋转角度 (90/180/270)
- **flip_direction**: 翻转方向 (horizontal/vertical)
- **brightness**: 亮度调整 (-1.0 到 1.0)
- **contrast**: 对比度调整 (-1.0 到 1.0)
- **saturation**: 饱和度调整 (-1.0 到 1.0)
- **thumbnail_size**: 缩略图尺寸，默认 200
- **grid_cols**: 图册列数，默认 3
- **recursive**: 是否递归处理子目录，默认 true
- **pattern**: 文件匹配模式，默认 *.jpg,*.jpeg,*.png,*.webp,*.bmp,*.tiff
- **dry_run**: 预览模式，只显示处理计划不实际处理，默认 false

## 输出
- **processed_count**: 成功处理文件数
- **failed_count**: 失败文件数
- **output_dir**: 输出目录路径
- **size_reduction**: 文件大小变化百分比
- **processing_time**: 处理耗时

## 步骤
无

## 依赖
- Pillow
- opencv-python
- numpy

## 版本
1.0.0
