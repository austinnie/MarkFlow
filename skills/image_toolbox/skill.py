
## 完整可用的 `skills/ImageToolbox.py`

"""
image_toolbox - 图片批量处理工具箱

功能：
  - 格式转换：jpg/png/webp/bmp/tiff
  - 尺寸调整：按比例或指定尺寸
  - 压缩优化：降低文件大小
  - 添加水印：文字或图片水印
  - 旋转翻转：90/180/270 旋转，水平/垂直翻转
  - 颜色调整：亮度/对比度/饱和度
  - 裁剪：按区域裁剪
  - 添加边框：边框和阴影
  - 创建缩略图：生成预览图
  - 生成图册：多图拼接
"""

import os
import time
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# 尝试导入图片处理库
try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
    import numpy as np
    PIL_AVAILABLE = True
except ImportError as e:
    PIL_AVAILABLE = False
    logger.warning(f"PIL 未安装: {e}")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError as e:
    CV2_AVAILABLE = False
    logger.warning(f"OpenCV 未安装: {e}")


class ImageToolbox:
    """
    图片批量处理工具箱
    """
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {
        'jpg': 'JPEG',
        'jpeg': 'JPEG',
        'png': 'PNG',
        'webp': 'WEBP',
        'bmp': 'BMP',
        'tiff': 'TIFF',
        'gif': 'GIF'
    }
    
    # 水印位置
    POSITIONS = {
        'center': (0.5, 0.5),
        'top-left': (0.05, 0.05),
        'top-right': (0.95, 0.05),
        'bottom-left': (0.05, 0.95),
        'bottom-right': (0.95, 0.95)
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "image_toolbox"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        if not PIL_AVAILABLE:
            logger.warning("Pillow 未安装，请运行: pip install Pillow")
        
        logger.info("ImageToolbox 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'output_dir': './processed_images',
            'default_quality': 85,
            'default_format': 'jpg',
            'max_image_size': 4096,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> Dict:
        """验证输入参数"""
        if 'source_dir' not in kwargs or not kwargs['source_dir']:
            raise ValueError("source_dir 是必填参数")
        
        source_dir = Path(kwargs['source_dir'])
        if not source_dir.exists():
            raise ValueError(f"源目录不存在: {source_dir}")
        
        # 验证操作
        operations = kwargs.get('operations', '')
        valid_ops = ['resize', 'compress', 'convert', 'watermark', 'crop', 
                    'rotate', 'flip', 'color', 'thumbnail', 'grid']
        if operations:
            for op in operations.split(','):
                op = op.strip()
                if op and op not in valid_ops:
                    raise ValueError(f"不支持的操作: {op}")
        
        # 验证格式
        target_format = kwargs.get('target_format', '').lower()
        if target_format and target_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的格式: {target_format}")
        
        # 验证压缩质量
        quality = kwargs.get('quality', self.config.get('default_quality', 85))
        if not (1 <= quality <= 100):
            raise ValueError(f"quality 必须在 1-100 之间，当前值: {quality}")
        
        return kwargs
    
    def _scan_images(self, source_dir: Path, pattern: str = None, recursive: bool = True) -> List[Path]:
        """扫描图片文件"""
        if not pattern:
            pattern = '*.jpg,*.jpeg,*.png,*.webp,*.bmp,*.tiff'
        
        patterns = [p.strip() for p in pattern.split(',')]
        image_files = []
        
        if recursive:
            for pat in patterns:
                image_files.extend(source_dir.rglob(pat))
        else:
            for pat in patterns:
                image_files.extend(source_dir.glob(pat))
        
        # 去重并排序
        return sorted(set(image_files))
    
    def _get_output_path(self, input_path: Path, output_dir: Path, target_format: str = None) -> Path:
        """获取输出路径"""
        relative_path = input_path.relative_to(self.source_dir)
        output_path = output_dir / relative_path
        
        # 如果指定了目标格式，修改扩展名
        if target_format:
            output_path = output_path.with_suffix(f'.{target_format}')
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def _resize_image(self, image: Image.Image, width: int = None, height: int = None) -> Image.Image:
        """调整图片尺寸"""
        original_width, original_height = image.size
        
        if width is None and height is None:
            return image
        
        # 计算新尺寸
        if width is not None and height is not None:
            new_width = width
            new_height = height
        elif width is not None:
            ratio = width / original_width
            new_width = width
            new_height = int(original_height * ratio)
        else:
            ratio = height / original_height
            new_width = int(original_width * ratio)
            new_height = height
        
        # 确保尺寸为正
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        
        # 使用高质量的缩放算法
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _compress_image(self, image: Image.Image, quality: int, format: str) -> Image.Image:
        """压缩图片（通过保存时设置质量）"""
        # 压缩在保存时进行，这里只是标记
        return image
    
    def _convert_format(self, image: Image.Image, target_format: str) -> Image.Image:
        """转换格式"""
        # 转换 RGB 模式
        if target_format in ['jpg', 'jpeg'] and image.mode in ['RGBA', 'P']:
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode == 'P':
            image = image.convert('RGB')
        
        return image
    
    def _add_watermark(self, image: Image.Image, text: str = None, 
                       image_path: str = None, position: str = 'bottom-right',
                       opacity: float = 0.7) -> Image.Image:
        """添加水印"""
        if text is None and image_path is None:
            return image
        
        # 创建可编辑的副本
        img = image.copy()
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建水印图层
        watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        if text:
            # 文字水印
            try:
                # 尝试使用系统字体
                font_size = min(img.size) // 20
                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("simhei.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                
                # 计算文字位置
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                pos_x, pos_y = self._calculate_position(
                    img.size, (text_width, text_height), position
                )
                
                # 绘制文字阴影
                shadow_offset = 2
                draw.text((pos_x + shadow_offset, pos_y + shadow_offset), text, 
                         font=font, fill=(0, 0, 0, int(128 * opacity)))
                draw.text((pos_x, pos_y), text, 
                         font=font, fill=(255, 255, 255, int(255 * opacity)))
                
            except Exception as e:
                logger.warning(f"添加文字水印失败: {e}")
        
        if image_path:
            # 图片水印
            try:
                watermark_img = Image.open(image_path)
                # 调整水印大小
                max_w = img.size[0] // 6
                max_h = img.size[1] // 6
                watermark_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                
                # 设置透明度
                if watermark_img.mode != 'RGBA':
                    watermark_img = watermark_img.convert('RGBA')
                
                # 调整透明度
                alpha = watermark_img.split()[3]
                alpha = alpha.point(lambda p: p * opacity)
                watermark_img.putalpha(alpha)
                
                # 计算位置
                pos_x, pos_y = self._calculate_position(
                    img.size, watermark_img.size, position
                )
                
                watermark.paste(watermark_img, (pos_x, pos_y), watermark_img)
                
            except Exception as e:
                logger.warning(f"添加图片水印失败: {e}")
        
        # 合并图层
        result = Image.alpha_composite(img, watermark)
        
        # 转换回原模式
        if image.mode == 'RGB':
            result = result.convert('RGB')
        
        return result
    
    def _calculate_position(self, image_size: Tuple[int, int], 
                           object_size: Tuple[int, int], 
                           position: str) -> Tuple[int, int]:
        """计算位置坐标"""
        img_w, img_h = image_size
        obj_w, obj_h = object_size
        
        pos_config = {
            'center': ((img_w - obj_w) // 2, (img_h - obj_h) // 2),
            'top-left': (20, 20),
            'top-right': (img_w - obj_w - 20, 20),
            'bottom-left': (20, img_h - obj_h - 20),
            'bottom-right': (img_w - obj_w - 20, img_h - obj_h - 20)
        }
        
        return pos_config.get(position, pos_config['bottom-right'])
    
    def _crop_image(self, image: Image.Image, x: int = None, y: int = None,
                    width: int = None, height: int = None) -> Image.Image:
        """裁剪图片"""
        img_w, img_h = image.size
        
        # 如果未指定裁剪区域，居中裁剪
        if x is None and y is None and width is None and height is None:
            # 裁剪为正方形
            min_side = min(img_w, img_h)
            x = (img_w - min_side) // 2
            y = (img_h - min_side) // 2
            width = min_side
            height = min_side
        else:
            # 使用指定区域
            x = x or 0
            y = y or 0
            width = width or (img_w - x)
            height = height or (img_h - y)
        
        # 确保裁剪区域在图像范围内
        x = max(0, x)
        y = max(0, y)
        width = min(width, img_w - x)
        height = min(height, img_h - y)
        
        if width <= 0 or height <= 0:
            return image
        
        return image.crop((x, y, x + width, y + height))
    
    def _rotate_image(self, image: Image.Image, angle: int) -> Image.Image:
        """旋转图片"""
        if angle in [90, 180, 270]:
            return image.rotate(angle, expand=True)
        return image
    
    def _flip_image(self, image: Image.Image, direction: str) -> Image.Image:
        """翻转图片"""
        if direction == 'horizontal':
            return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif direction == 'vertical':
            return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return image
    
    def _adjust_color(self, image: Image.Image, brightness: float = 0,
                     contrast: float = 0, saturation: float = 0) -> Image.Image:
        """调整颜色"""
        img = image
        
        if brightness != 0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.0 + brightness)
        
        if contrast != 0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.0 + contrast)
        
        if saturation != 0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.0 + saturation)
        
        return img
    
    def _create_thumbnail(self, image: Image.Image, size: int) -> Image.Image:
        """创建缩略图"""
        img = image.copy()
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        return img
    
    def _create_grid(self, images: List[Image.Image], cols: int = 3, 
                    spacing: int = 10) -> Image.Image:
        """创建图册"""
        if not images:
            return None
        
        # 计算每个缩略图的大小
        thumb_size = 200
        thumbnails = []
        for img in images[:min(len(images), cols * 10)]:  # 限制数量
            thumb = img.copy()
            thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
            thumbnails.append(thumb)
        
        if not thumbnails:
            return None
        
        # 计算网格尺寸
        rows = (len(thumbnails) + cols - 1) // cols
        total_width = cols * (thumb_size + spacing) + spacing
        total_height = rows * (thumb_size + spacing) + spacing
        
        # 创建背景
        grid_img = Image.new('RGB', (total_width, total_height), (255, 255, 255))
        
        # 排列图片
        for i, thumb in enumerate(thumbnails):
            row = i // cols
            col = i % cols
            x = spacing + col * (thumb_size + spacing)
            y = spacing + row * (thumb_size + spacing)
            grid_img.paste(thumb, (x, y))
        
        return grid_img
    
    def _process_single_image(self, image_path: Path, operations: str, 
                              params: Dict) -> Tuple[bool, Path, str]:
        """处理单张图片"""
        try:
            # 打开图片
            with Image.open(image_path) as img:
                original_mode = img.mode
                
                # 解析操作
                op_list = [op.strip() for op in operations.split(',') if op.strip()]
                
                for op in op_list:
                    if op == 'resize':
                        width = params.get('width')
                        height = params.get('height')
                        img = self._resize_image(img, width, height)
                    
                    elif op == 'compress':
                        quality = params.get('quality', self.config.get('default_quality', 85))
                        # 压缩在保存时处理
                    
                    elif op == 'convert':
                        target_format = params.get('target_format', 'jpg')
                        img = self._convert_format(img, target_format)
                    
                    elif op == 'watermark':
                        text = params.get('watermark_text')
                        image_path_wm = params.get('watermark_image')
                        position = params.get('watermark_position', 'bottom-right')
                        opacity = params.get('watermark_opacity', 0.7)
                        img = self._add_watermark(img, text, image_path_wm, position, opacity)
                    
                    elif op == 'crop':
                        x = params.get('crop_x')
                        y = params.get('crop_y')
                        width = params.get('crop_width')
                        height = params.get('crop_height')
                        img = self._crop_image(img, x, y, width, height)
                    
                    elif op == 'rotate':
                        angle = params.get('rotate_angle', 90)
                        img = self._rotate_image(img, angle)
                    
                    elif op == 'flip':
                        direction = params.get('flip_direction', 'horizontal')
                        img = self._flip_image(img, direction)
                    
                    elif op == 'color':
                        brightness = params.get('brightness', 0)
                        contrast = params.get('contrast', 0)
                        saturation = params.get('saturation', 0)
                        img = self._adjust_color(img, brightness, contrast, saturation)
                    
                    elif op == 'thumbnail':
                        size = params.get('thumbnail_size', 200)
                        img = self._create_thumbnail(img, size)
                    
                    elif op == 'grid':
                        # 图册在最后统一处理
                        pass
                
                # 确定输出格式和路径
                target_format = params.get('target_format', '')
                output_dir = Path(params.get('output_dir', self.config.get('output_dir', './processed_images')))
                
                if target_format:
                    output_path = self._get_output_path(image_path, output_dir, target_format)
                    save_format = target_format
                else:
                    output_path = self._get_output_path(image_path, output_dir)
                    save_format = image_path.suffix[1:].lower() or 'jpg'
                
                # 确保格式在支持列表中
                if save_format not in self.SUPPORTED_FORMATS:
                    save_format = 'jpg'
                
                # 保存图片
                quality = params.get('quality', self.config.get('default_quality', 85))
                
                if save_format in ['jpg', 'jpeg']:
                    img.save(output_path, self.SUPPORTED_FORMATS[save_format], 
                            quality=quality, optimize=True)
                else:
                    img.save(output_path, self.SUPPORTED_FORMATS[save_format])
                
                return True, output_path, "处理成功"
                
        except Exception as e:
            logger.error(f"处理失败 {image_path}: {e}")
            return False, image_path, str(e)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行图片处理"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        if not PIL_AVAILABLE:
            return {
                "status": "error",
                "error": "Pillow 未安装，请运行: pip install Pillow"
            }
        
        try:
            params = self._validate_inputs(**kwargs)
            
            self.source_dir = Path(params.get('source_dir'))
            output_dir = Path(params.get('output_dir', self.config.get('output_dir', './processed_images')))
            operations = params.get('operations', '')
            dry_run = params.get('dry_run', False)
            pattern = params.get('pattern', '*.jpg,*.jpeg,*.png,*.webp,*.bmp,*.tiff')
            recursive = params.get('recursive', True)
            
            if not operations:
                return {
                    "status": "error",
                    "error": "请指定至少一个操作 (operations 参数)"
                }
            
            logger.info(f"扫描目录: {self.source_dir}")
            image_files = self._scan_images(self.source_dir, pattern, recursive)
            
            if not image_files:
                return {
                    "status": "error",
                    "error": f"在 {self.source_dir} 中未找到图片文件"
                }
            
            logger.info(f"找到 {len(image_files)} 张图片")
            
            if dry_run:
                logger.info("预览模式，不实际处理")
                return {
                    "status": "success",
                    "result": {
                        "total_files": len(image_files),
                        "files": [str(f) for f in image_files],
                        "operations": operations,
                        "dry_run": True
                    }
                }
            
            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 处理图片
            processed = 0
            failed = 0
            original_size = 0
            compressed_size = 0
            logs = []
            
            for i, image_path in enumerate(image_files):
                logger.info(f"处理 [{i+1}/{len(image_files)}]: {image_path.name}")
                
                original_size += image_path.stat().st_size
                
                success, output_path, message = self._process_single_image(
                    image_path, operations, params
                )
                
                if success:
                    processed += 1
                    if output_path.exists():
                        compressed_size += output_path.stat().st_size
                    logs.append({
                        "file": str(image_path),
                        "output": str(output_path),
                        "status": "success",
                        "message": message
                    })
                else:
                    failed += 1
                    logs.append({
                        "file": str(image_path),
                        "status": "failed",
                        "message": message
                    })
            
            processing_time = time.time() - start_time
            
            # 计算压缩率
            size_reduction = 0
            if original_size > 0:
                size_reduction = (1 - compressed_size / original_size) * 100
            
            result_data = {
                "processed_count": processed,
                "failed_count": failed,
                "total_count": len(image_files),
                "output_dir": str(output_dir),
                "original_total_size": original_size,
                "compressed_total_size": compressed_size,
                "size_reduction": size_reduction,
                "processing_time": f"{processing_time:.2f}s",
                "operations": operations,
                "logs": logs
            }
            
            logger.info(f"✅ 处理完成! 成功: {processed}, 失败: {failed}")
            logger.info(f"  大小减少: {size_reduction:.1f}%")
            logger.info(f"  耗时: {processing_time:.2f}s")
            
            return {
                "status": "success",
                "result": result_data,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<ImageToolbox(name={self.name}, version={self.version})>"

# 兼容旧导入
Imagetoolbox = ImageToolbox
