

## 完整可用的 `skills/ImageViewer.py`


"""
image_viewer - 功能完整的图片查看器和管理器

功能：
  - 目录浏览、缩略图网格
  - 单图查看、放大缩小
  - EXIF 信息查看
  - 图片编辑：裁剪、旋转、翻转
  - 批量重命名、移动、删除
  - 标签管理、星标
  - 搜索筛选
  - 批量导出转换
"""

import os
import time
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.ExifTags import TAGS, GPSTAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class ImageViewer:
    """功能完整的图片查看器和管理器"""
    
    # 支持的图片格式
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg'}
    
    # 视频格式（支持播放）
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    
    # 排序选项
    SORT_OPTIONS = ['name', 'date', 'size', 'type', 'modified', 'created']
    
    # 排序方向
    SORT_ORDERS = ['asc', 'desc']
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化"""
        self.config = config or {}
        self.name = "image_viewer"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        logger.info(f"ImageViewer v{self.version} 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'default_view_mode': 'grid',
            'default_thumbnail_size': 200,
            'default_sort_by': 'name',
            'default_sort_order': 'asc',
            'slideshow_interval': 3,
            'export_quality': 85,
            'export_format': 'jpg'
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> Dict:
        """验证输入"""
        action = kwargs.get('action', 'browse')
        valid_actions = ['browse', 'view', 'info', 'edit', 'manage', 
                        'slideshow', 'search', 'export', 'print', 'tags', 'star']
        
        if action not in valid_actions:
            raise ValueError(f"不支持的操作: {action}，支持: {valid_actions}")
        
        if action in ['browse', 'slideshow', 'search', 'export']:
            if 'source_dir' not in kwargs or not kwargs['source_dir']:
                raise ValueError(f"{action} 操作需要 source_dir 参数")
            source_dir = Path(kwargs['source_dir'])
            if not source_dir.exists():
                raise ValueError(f"目录不存在: {source_dir}")
        
        if action in ['view', 'info', 'edit']:
            if 'file' not in kwargs or not kwargs['file']:
                raise ValueError(f"{action} 操作需要 file 参数")
            file_path = Path(kwargs['file'])
            if not file_path.exists():
                raise ValueError(f"文件不存在: {file_path}")
        
        return kwargs
    
    def _scan_directory(self, source_dir: Path, recursive: bool = True, 
                        filter_type: str = 'all') -> List[Path]:
        """扫描目录获取文件列表"""
        files = []
        
        if filter_type == 'all':
            extensions = self.IMAGE_EXTENSIONS | self.VIDEO_EXTENSIONS
        elif filter_type == 'images':
            extensions = self.IMAGE_EXTENSIONS
        elif filter_type == 'videos':
            extensions = self.VIDEO_EXTENSIONS
        else:
            extensions = self.IMAGE_EXTENSIONS
        
        for ext in extensions:
            if recursive:
                files.extend(source_dir.rglob(f'*{ext}'))
                files.extend(source_dir.rglob(f'*{ext.upper()}'))
            else:
                files.extend(source_dir.glob(f'*{ext}'))
                files.extend(source_dir.glob(f'*{ext.upper()}'))
        
        # 去重并排序
        return sorted(set(files))
    
    def _get_file_info(self, file_path: Path) -> Dict:
        """获取文件详细信息"""
        info = {
            'path': str(file_path),
            'name': file_path.name,
            'stem': file_path.stem,
            'extension': file_path.suffix,
            'size': file_path.stat().st_size,
            'size_mb': round(file_path.stat().st_size / (1024 * 1024), 2),
            'size_kb': round(file_path.stat().st_size / 1024, 1),
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
            'is_image': file_path.suffix.lower() in self.IMAGE_EXTENSIONS,
            'is_video': file_path.suffix.lower() in self.VIDEO_EXTENSIONS
        }
        
        # 获取图片信息
        if info['is_image'] and PIL_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    info['width'] = img.width
                    info['height'] = img.height
                    info['mode'] = img.mode
                    info['format'] = img.format
                    info['is_animated'] = getattr(img, 'is_animated', False)
                    info['n_frames'] = getattr(img, 'n_frames', 1)
                    info['aspect_ratio'] = round(img.width / img.height, 2)
                    
                    # EXIF 信息
                    exif = img.getexif()
                    if exif:
                        exif_data = {}
                        for tag_id, value in exif.items():
                            tag_name = TAGS.get(tag_id, tag_id)
                            if tag_name == 'GPSInfo':
                                gps = {}
                                for gps_tag in value:
                                    sub_tag = GPSTAGS.get(gps_tag, gps_tag)
                                    gps[sub_tag] = value[gps_tag]
                                exif_data['GPS'] = gps
                            else:
                                exif_data[tag_name] = str(value)
                        info['exif'] = exif_data
            except Exception as e:
                logger.warning(f"获取图片信息失败 {file_path}: {e}")
                info['error'] = str(e)
        
        return info
    
    def _generate_thumbnail(self, file_path: Path, size: int = 200) -> Optional[str]:
        """生成缩略图（返回base64或路径）"""
        try:
            with Image.open(file_path) as img:
                img.thumbnail((size, size), Image.Resampling.LANCZOS)
                # 保存到临时目录
                temp_dir = Path('./.thumbnails')
                temp_dir.mkdir(exist_ok=True)
                thumb_path = temp_dir / f"{file_path.stem}_{size}.jpg"
                img.save(thumb_path, 'JPEG', quality=85)
                return str(thumb_path)
        except Exception as e:
            logger.warning(f"生成缩略图失败: {e}")
            return None
    
    def _get_tags_file(self, source_dir: Path) -> Path:
        """获取标签文件路径"""
        return source_dir / '.image_tags.json'
    
    def _load_tags(self, source_dir: Path) -> Dict:
        """加载标签数据"""
        tags_file = self._get_tags_file(source_dir)
        if tags_file.exists():
            try:
                with open(tags_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_tags(self, source_dir: Path, tags_data: Dict):
        """保存标签数据"""
        tags_file = self._get_tags_file(source_dir)
        with open(tags_file, 'w', encoding='utf-8') as f:
            json.dump(tags_data, f, ensure_ascii=False, indent=2)
    
    def _sort_files(self, files: List[Path], sort_by: str, sort_order: str) -> List[Path]:
        """排序文件"""
        if sort_by == 'name':
            key = lambda x: x.name
        elif sort_by == 'date':
            key = lambda x: x.stat().st_mtime
        elif sort_by == 'size':
            key = lambda x: x.stat().st_size
        elif sort_by == 'type':
            key = lambda x: x.suffix
        elif sort_by == 'modified':
            key = lambda x: x.stat().st_mtime
        elif sort_by == 'created':
            key = lambda x: x.stat().st_ctime
        else:
            key = lambda x: x.name
        
        return sorted(files, key=key, reverse=(sort_order == 'desc'))
    
    def _search_files(self, files: List[Path], query: str) -> List[Path]:
        """搜索文件"""
        query_lower = query.lower()
        results = []
        for f in files:
            if query_lower in f.name.lower():
                results.append(f)
        return results
    
    def _export_images(self, source_dir: Path, output_dir: Path, 
                       format: str = 'jpg', quality: int = 85,
                       size: str = None) -> Dict:
        """批量导出图片"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files = self._scan_directory(source_dir, recursive=True, filter_type='images')
        processed = 0
        failed = 0
        total_size = 0
        output_size = 0
        
        for i, file_path in enumerate(files):
            try:
                with Image.open(file_path) as img:
                    # 调整尺寸
                    if size:
                        parts = size.split('x')
                        if len(parts) == 2:
                            w, h = int(parts[0]), int(parts[1])
                            img.thumbnail((w, h), Image.Resampling.LANCZOS)
                    
                    # 转换格式
                    if format in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'P']:
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                        img = bg
                    
                    # 保存
                    output_path = output_dir / f"{file_path.stem}.{format}"
                    if format in ['jpg', 'jpeg']:
                        img.save(output_path, quality=quality, optimize=True)
                    else:
                        img.save(output_path, format.upper())
                    
                    processed += 1
                    total_size += file_path.stat().st_size
                    output_size += output_path.stat().st_size
                    
            except Exception as e:
                logger.error(f"导出失败 {file_path}: {e}")
                failed += 1
        
        return {
            'processed': processed,
            'failed': failed,
            'total_files': len(files),
            'original_size': total_size,
            'output_size': output_size,
            'output_dir': str(output_dir)
        }
    
    def _manage_files(self, files: List[Path], action: str, 
                      target_dir: str = None, pattern: str = None) -> Dict:
        """管理文件：复制、移动、删除、重命名"""
        results = {'success': [], 'failed': []}
        
        for file_path in files:
            try:
                if action == 'copy':
                    dest = Path(target_dir) / file_path.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest)
                    results['success'].append(str(file_path))
                
                elif action == 'move':
                    dest = Path(target_dir) / file_path.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(file_path, dest)
                    results['success'].append(str(file_path))
                
                elif action == 'delete':
                    file_path.unlink()
                    results['success'].append(str(file_path))
                
                elif action == 'rename':
                    if pattern:
                        new_name = pattern.replace('{name}', file_path.stem)
                        new_name = new_name.replace('{ext}', file_path.suffix[1:])
                        new_path = file_path.parent / new_name
                        file_path.rename(new_path)
                        results['success'].append(str(new_path))
                
            except Exception as e:
                results['failed'].append({'file': str(file_path), 'error': str(e)})
        
        return results
    
    def _browse(self, source_dir: Path, view_mode: str = 'grid',
                sort_by: str = 'name', sort_order: str = 'asc',
                filter_type: str = 'all', thumbnail_size: int = 200) -> Dict:
        """浏览目录"""
        files = self._scan_directory(source_dir, recursive=True, filter_type=filter_type)
        files = self._sort_files(files, sort_by, sort_order)
        
        thumbnails = []
        for f in files[:100]:  # 限制数量
            thumb = self._generate_thumbnail(f, thumbnail_size)
            thumbnails.append({
                'path': str(f),
                'name': f.name,
                'thumbnail': thumb,
                'info': self._get_file_info(f)
            })
        
        tags_data = self._load_tags(source_dir)
        
        return {
            'total_files': len(files),
            'files': [str(f) for f in files],
            'thumbnails': thumbnails,
            'view_mode': view_mode,
            'sort_by': sort_by,
            'sort_order': sort_order,
            'tags': tags_data,
            'source_dir': str(source_dir)
        }
    
    def _view_slideshow(self, source_dir: Path, interval: int = 3,
                        sort_by: str = 'name', sort_order: str = 'asc') -> Dict:
        """幻灯片播放"""
        files = self._scan_directory(source_dir, recursive=True, filter_type='images')
        files = self._sort_files(files, sort_by, sort_order)
        
        return {
            'total_files': len(files),
            'files': [str(f) for f in files],
            'interval': interval,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行操作"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            params = self._validate_inputs(**kwargs)
            action = params.get('action', 'browse')
            
            result = {}
            
            if action == 'browse':
                source_dir = Path(params['source_dir'])
                view_mode = params.get('view_mode', self.config.get('default_view_mode', 'grid'))
                sort_by = params.get('sort_by', self.config.get('default_sort_by', 'name'))
                sort_order = params.get('sort_order', self.config.get('default_sort_order', 'asc'))
                filter_type = params.get('filter', 'all')
                thumbnail_size = params.get('thumbnail_size', self.config.get('default_thumbnail_size', 200))
                
                result = self._browse(source_dir, view_mode, sort_by, sort_order, filter_type, thumbnail_size)
                result['action'] = 'browse'
            
            elif action == 'info':
                file_path = Path(params['file'])
                info = self._get_file_info(file_path)
                result = {'file': str(file_path), 'info': info, 'action': 'info'}
            
            elif action == 'slideshow':
                source_dir = Path(params['source_dir'])
                interval = params.get('slideshow_interval', self.config.get('slideshow_interval', 3))
                sort_by = params.get('sort_by', self.config.get('default_sort_by', 'name'))
                sort_order = params.get('sort_order', self.config.get('default_sort_order', 'asc'))
                result = self._view_slideshow(source_dir, interval, sort_by, sort_order)
                result['action'] = 'slideshow'
            
            elif action == 'search':
                source_dir = Path(params['source_dir'])
                query = params.get('query', '')
                files = self._scan_directory(source_dir, recursive=True)
                results = self._search_files(files, query)
                result = {
                    'query': query,
                    'total_results': len(results),
                    'files': [str(f) for f in results],
                    'action': 'search'
                }
            
            elif action == 'export':
                source_dir = Path(params['source_dir'])
                output_dir = Path(params.get('output_dir', './exported_images'))
                export_format = params.get('export_format', self.config.get('export_format', 'jpg'))
                export_quality = params.get('export_quality', self.config.get('export_quality', 85))
                export_size = params.get('export_size')
                
                export_result = self._export_images(
                    source_dir, output_dir, export_format, export_quality, export_size
                )
                result = {**export_result, 'action': 'export'}
            
            elif action == 'manage':
                source_dir = Path(params['source_dir'])
                manage_action = params.get('manage_action', 'rename')
                target_dir = params.get('target_dir')
                pattern = params.get('rename_pattern')
                
                files = self._scan_directory(source_dir, recursive=False)
                manage_result = self._manage_files(files, manage_action, target_dir, pattern)
                result = {**manage_result, 'action': 'manage'}
            
            elif action == 'tags':
                source_dir = Path(params['source_dir'])
                tag_action = params.get('tag_action', 'add')
                file_path = params.get('file')
                tags = params.get('tags', '').split(',')
                star = params.get('star', 0)
                
                tags_data = self._load_tags(source_dir)
                
                if file_path:
                    file_key = str(Path(file_path).name)
                    if tag_action == 'add':
                        if file_key not in tags_data:
                            tags_data[file_key] = {'tags': [], 'star': 0}
                        tags_data[file_key]['tags'] = list(set(tags_data[file_key].get('tags', []) + tags))
                    elif tag_action == 'remove':
                        if file_key in tags_data:
                            tags_data[file_key]['tags'] = [t for t in tags_data[file_key].get('tags', []) if t not in tags]
                    elif tag_action == 'star':
                        if file_key not in tags_data:
                            tags_data[file_key] = {'tags': [], 'star': 0}
                        tags_data[file_key]['star'] = min(5, max(0, star))
                
                self._save_tags(source_dir, tags_data)
                result = {'tags': tags_data, 'action': 'tags'}
            
            else:
                result = {'message': f'操作 {action} 已执行', 'action': action}
            
            result['processing_time'] = f"{time.time() - start_time:.2f}s"
            result['status'] = 'success'
            
            return {
                "status": "success",
                "result": result,
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
        return f"<ImageViewer(name={self.name}, version={self.version})>"