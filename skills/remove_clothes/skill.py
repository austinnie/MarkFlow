# markflow/skills/remove_clothes/skill.py
"""
衣服移除 Skill - 使用本地 SD Inpaint 模型
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# 导入依赖
try:
    import torch
    import numpy as np
    from PIL import Image, ImageDraw
    import cv2
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"依赖未安装: {e}")


class ClothesRemover:
    """
    衣服移除技能 - 使用本地 SD Inpaint 模型
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化技能
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.name = "remove_clothes"
        self.version = "1.0.0"
        
        # 获取项目根目录
        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent  # skills/ -> MarkFlow/ -> SD_OpenVINO/
        
        # 模型配置
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.pipeline = None
        self.current_model = None
        self._yolo_model = None
        
        self._setup_logging()
        self._setup_config()
        
        logger.info(f"ClothesRemover 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


    def _setup_config(self):
        """设置配置默认值"""
        defaults = {
            'output_dir': str(self.skill_dir / 'output'),
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 25,
            'default_strength': 0.5,
            # 🔥 默认提示词（写在这里）
            'default_prompt': 'nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic',
            'default_negative': 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        Path(self.config['output_dir']).mkdir(parents=True, exist_ok=True)
    
    def _find_model(self, model_name: str) -> Optional[Path]:
        """查找模型文件"""
        if not model_name:
            model_name = self.config.get('default_model', 'sd-v1-5-inpainting-tiny.safetensors')
        
        logger.info(f"🔍 查找模型: '{model_name}'")
        logger.info(f"📁 模型目录: {self.models_dir}")
        
        # 1. 直接查找
        direct_path = self.models_dir / model_name
        if direct_path.exists():
            logger.info(f"  ✅ 找到: {direct_path}")
            return direct_path
        
        # 2. 提取文件名
        filename = os.path.basename(model_name)
        
        # 3. 在子目录中查找
        subdirs = ['sd-v1-5', 'sdxl']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                logger.info(f"  ✅ 找到: {sub_path}")
                return sub_path
        
        # 4. 遍历所有子目录
        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    logger.info(f"  ✅ 找到: {file_path}")
                    return file_path
        
        logger.error(f"❌ 未找到模型: '{model_name}'")
        return None
    
    def _get_yolo_model(self):
        """获取 YOLO 模型"""
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n-seg.pt")
                logger.info("  ✅ YOLO 加载成功")
            except ImportError:
                logger.warning("  ⚠️ ultralytics 未安装，将使用手动遮罩")
                self._yolo_model = False
            except Exception as e:
                logger.warning(f"  ⚠️ YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model
    
    def _load_model(self, model_name: str) -> bool:
        """加载 SD Inpaint 模型"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装，请运行: pip install diffusers transformers accelerate")
            return False
        
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型文件不存在: {model_name}")
            return False
        
        try:
            logger.info(f"📦 加载模型: {model_path}")
            
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.pipeline.to(self.device)
            
            if self.device == 'cuda':
                self.pipeline.enable_attention_slicing()
            elif self.device == 'cpu':
                self.pipeline.enable_attention_slicing()
            
            self.current_model = model_name
            logger.info(f"  ✅ 模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 模型加载失败: {e}")
            return False
        
    def _generate_mask(self, image: Image.Image) -> Image.Image:
        """生成衣服遮罩 - 只覆盖躯干衣服区域"""
        h, w = image.size[1], image.size[0]
        
        yolo = self._get_yolo_model()
        if yolo and yolo is not False:
            try:
                results = yolo(image, verbose=False)
                if len(results) > 0 and results[0].masks is not None:
                    masks = results[0].masks.data.cpu().numpy()
                    combined = np.zeros((h, w), dtype=np.uint8)
                    for m in masks:
                        m_resized = cv2.resize(m, (w, h))
                        combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)
                    
                    coords = np.where(combined > 0)
                    if len(coords[0]) > 0:
                        y_min, y_max = coords[0].min(), coords[0].max()
                        body_h = y_max - y_min
                        
                        # 🔥 只覆盖衣服区域：从脖子到腰部下方
                        neck = y_min + int(body_h * 0.18)
                        hip = y_min + int(body_h * 0.65)  # 从 0.70 改到 0.65，更精确
                        
                        x_min, x_max = coords[1].min(), coords[1].max()
                        body_w = x_max - x_min
                        left = x_min + int(body_w * 0.08)
                        right = x_max - int(body_w * 0.08)
                        
                        clothes = np.zeros_like(combined)
                        clothes[neck:hip, left:right] = combined[neck:hip, left:right]
                        
                        # 减少膨胀，让边缘更精确
                        kernel = np.ones((5, 5), np.uint8)
                        clothes = cv2.dilate(clothes, kernel, iterations=1)
                        clothes = cv2.GaussianBlur(clothes, (9, 9), 0)
                        
                        return Image.fromarray(clothes, mode="L")
            except Exception as e:
                logger.warning(f"  ⚠️ YOLO 分割失败: {e}")
        
        # 备用：手动绘制遮罩
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        cx, cy = w // 2, h // 2
        draw.ellipse((cx - w//4, cy - h//3, cx + w//4, cy + h//3), fill=255)
        return mask
    
    def _generate_mask_manual(self, image: Image.Image) -> Image.Image:
        """手动绘制遮罩（用鼠标在图片上画）"""
        import cv2
        
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 创建一个窗口，让用户用鼠标画遮罩
        mask = np.zeros(image.size[::-1], dtype=np.uint8)
        drawing = False
        
        def draw_circle(event, x, y, flags, param):
            nonlocal drawing
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing:
                    cv2.circle(mask, (x, y), 20, 255, -1)
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False
        
        cv2.namedWindow('Draw Mask')
        cv2.setMouseCallback('Draw Mask', draw_circle)
        
        while True:
            display = cv2.addWeighted(img_cv, 0.5, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), 0.5, 0)
            cv2.imshow('Draw Mask', display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord(' '):
                break
        
        cv2.destroyAllWindows()
        
        # 模糊遮罩
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        return Image.fromarray(mask, mode="L")
        
    def _load_model_from_path(self, model_path: str) -> bool:
        """直接从路径加载模型"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False
        
        try:
            logger.info(f"📦 从路径加载模型: {model_path}")
            
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.pipeline.to(self.device)
            
            if self.device == 'cuda' or self.device == 'cpu':
                self.pipeline.enable_attention_slicing()
            
            self.current_model = Path(model_path).name
            logger.info(f"  ✅ 模型加载成功: {self.current_model}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 模型加载失败: {e}")
            return False
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行衣服移除
        
        Args:
            **kwargs: 输入参数
                - image_path: 输入图片路径 (必填)
                - output_path: 输出图片路径 (可选)
                - model_name: 模型名称 (可选)
                - prompt: 生成提示词 (可选)
                - negative_prompt: 负面提示词 (可选)
                - strength: 重绘强度 (可选)
                - steps: 迭代步数 (可选)
                - seed: 随机种子 (可选)
                - output_dir: 输出目录 (可选)
                - save_mask: 是否保存遮罩 (可选)
        
        Returns:
            执行结果
        """
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            # 1. 获取参数
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}
            
            if not os.path.exists(image_path):
                return {"status": "error", "error": f"图片不存在: {image_path}"}
            
            output_path = kwargs.get('output_path')
            
            # 🔥 获取模型参数（支持多种传入方式）
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')
            
            # 2. 加载模型
            if model_path:
                # 优先使用完整路径
                if not os.path.exists(model_path):
                    return {"status": "error", "error": f"模型不存在: {model_path}"}
                if not self._load_model_from_path(model_path):
                    return {"status": "error", "error": f"无法加载模型: {model_path}"}
            else:
                # 使用模型名称
                model_name = model_name or self.config.get('default_model', 'sd-v1-5-inpainting-tiny.safetensors')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"无法加载模型: {model_name}"}
            
            # 3. 获取生成参数
            # 🔥 获取提示词：优先使用命令行传入的，否则使用默认
            prompt = kwargs.get('prompt')
            if prompt is None:
                prompt = self.config.get('default_prompt', 'nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic')
            
            negative_prompt = kwargs.get('negative_prompt')
            if negative_prompt is None:
                negative_prompt = self.config.get('default_negative', 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime')
                    
            strength = kwargs.get('strength', self.config.get('default_strength', 0.85))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            output_dir = kwargs.get('output_dir', self.config.get('output_dir'))
            save_mask = kwargs.get('save_mask', False)
            
            # 4. 加载图片并对齐尺寸
            image = Image.open(image_path).convert("RGB")
            original_size = image.size

            # 🔥 等比例放大到最小尺寸（保持宽高比）
            min_size = 512
            max_size = 1024

            need_resize = False
            new_size = original_size

            # 等比例缩放，确保短边 >= min_size
            if min(original_size) < min_size:
                ratio = min_size / min(original_size)
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                need_resize = True
            elif max(original_size) > max_size:
                ratio = max_size / max(original_size)
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                need_resize = True

            if need_resize:
                logger.info(f"  📐 等比例缩放: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                original_size = new_size

            # 🔥 确保宽高是 8 的倍数（SD 要求），用填充而不是拉伸
            width = (original_size[0] // 8) * 8
            height = (original_size[1] // 8) * 8

            if width != original_size[0] or height != original_size[1]:
                # 创建新画布，居中放置原图
                new_image = Image.new("RGB", (width, height), (0, 0, 0))
                x_offset = (width - original_size[0]) // 2
                y_offset = (height - original_size[1]) // 2
                new_image.paste(image, (x_offset, y_offset))
                image = new_image
                logger.info(f"  📐 填充对齐: {original_size[0]}x{original_size[1]} -> {width}x{height}")

            logger.info(f"📷 处理: {os.path.basename(image_path)} ({image.size[0]}x{image.size[1]})")
            logger.info(f"🎯 生成遮罩...")
            
            mask = self._generate_mask(image)
            
            if save_mask:
                mask_path = image_path.replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)
                logger.info(f"  📋 遮罩: {os.path.basename(mask_path)}")
            
            # 5. 设置随机种子
            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)
            
            logger.info(f"🎨 SD Inpaint 生成中...")
            logger.info(f"  提示词: {prompt[:50]}...")
            logger.info(f"  步数: {steps}")
            logger.info(f"  强度: {strength}")
            logger.info(f"  种子: {seed}")
            
            # 6. 执行 Inpaint（使用 image 的实际尺寸）
            current_size = image.size
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt if negative_prompt else None,
                image=image,
                mask_image=mask,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=7.5,
                generator=generator,
                width=current_size[0],
                height=current_size[1],
            ).images[0]
            
            # 7. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                filename = f"{Path(image_path).stem}_{timestamp}_nude.png"
                output_path = str(output_dir_path / filename)
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            result.save(output_path)
            
            generation_time = time.time() - start_time
            logger.info(f"  ✅ 保存: {os.path.basename(output_path)}")
            
            return {
                "status": "success",
                "output_path": output_path,
                "parameters": {
                    "image_path": image_path,
                    "model": self.current_model,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device
                },
                "model_used": self.current_model,
                "generation_time": f"{generation_time:.2f}s",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<ClothesRemover(name={self.name}, version={self.version})>"


# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="衣服移除工具")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出图片路径")
    parser.add_argument("--model", "-m", default="sd-v1-5-inpainting-tiny.safetensors", help="模型名称")
    parser.add_argument("--prompt", "-p", default="nude, naked body, beautiful skin, realistic body, masterpiece, best quality", help="生成提示词")
    parser.add_argument("--negative", "-n", default="clothes, fabric, ugly, deformed, bad anatomy, cropped", help="负面提示词")
    parser.add_argument("--strength", "-s", type=float, default=0.85, help="重绘强度")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")  # 默认 cpu
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    
    args = parser.parse_args()
    
    # 🔥 传递 device 参数
    skill = ClothesRemover(config={'device': args.device})
    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        model_name=args.model,
        prompt=args.prompt,
        negative_prompt=args.negative,
        strength=args.strength,
        steps=args.steps,
        seed=args.seed,
        save_mask=args.save_mask
    )
    
    if result['status'] == 'success':
        print(f"\n✅ 成功!")
        print(f"  📁 输出: {result['output_path']}")
        print(f"  ⏱️  耗时: {result['generation_time']}")
        print(f"  📋 参数:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n❌ 失败: {result.get('error', '未知错误')}")