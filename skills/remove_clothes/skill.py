# markflow/skills/remove_clothes/skill.py
"""
衣服移除 Skill - 使用本地 SD Inpaint 模型
支持手动绘制遮罩 + ControlNet 姿态控制
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
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    from diffusers import StableDiffusionInpaintPipeline, ControlNetModel
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"依赖未安装: {e}")

# ControlNet 依赖
try:
    from controlnet_aux import OpenPoseDetector
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False
    logger.warning("ControlNet 未安装，将使用普通 Inpaint")


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
        self.project_root = self.skill_dir.parent.parent.parent
        
        # 模型配置
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.pipeline = None
        self.current_model = None
        self._yolo_model = None
        self._openpose = None
        
        self._setup_logging()
        self._setup_config()
        
        logger.info(f"ClothesRemover 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  ControlNet: {'✅ 可用' if CONTROLNET_AVAILABLE else '❌ 不可用'}")
    
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
            'use_controlnet': True,
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
        
        logger.info(f"查找模型: '{model_name}'")
        logger.info(f"模型目录: {self.models_dir}")
        
        # 1. 直接查找
        direct_path = self.models_dir / model_name
        if direct_path.exists():
            logger.info(f"  找到: {direct_path}")
            return direct_path
        
        # 2. 提取文件名
        filename = os.path.basename(model_name)
        
        # 3. 在子目录中查找
        subdirs = ['sd-v1-5', 'sdxl']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                logger.info(f"  找到: {sub_path}")
                return sub_path
        
        # 4. 遍历所有子目录
        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    logger.info(f"  找到: {file_path}")
                    return file_path
        
        logger.error(f"未找到模型: '{model_name}'")
        return None
    
    def _get_yolo_model(self):
        """获取 YOLO 模型"""
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n-seg.pt")
                logger.info("  YOLO 加载成功")
            except ImportError:
                logger.warning("  ultralytics 未安装，将使用手动遮罩")
                self._yolo_model = False
            except Exception as e:
                logger.warning(f"  YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model
    
    def _load_model(self, model_name: str) -> bool:
        """加载 SD Inpaint 模型 + ControlNet"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False
        
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"模型文件不存在: {model_name}")
            return False
        
        try:
            logger.info(f"加载模型: {model_path}")
            
            # 加载 ControlNet（如果启用）
            use_controlnet = self.config.get('use_controlnet', True)
            controlnet = None
            if use_controlnet and CONTROLNET_AVAILABLE:
                try:
                    logger.info("  加载 ControlNet (OpenPose)...")
                    controlnet = ControlNetModel.from_pretrained(
                        "lllyasviel/control_v11p_sd15_openpose",
                        torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                    )
                    # 加载 OpenPose 检测器
                    from controlnet_aux import OpenPoseDetector
                    self._openpose = OpenPoseDetector.from_pretrained("lllyasviel/ControlNet")
                    logger.info("  ControlNet 加载成功")
                except Exception as e:
                    logger.warning(f"  ControlNet 加载失败: {e}")
                    controlnet = None
            
            # 加载 pipeline
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                controlnet=controlnet,
            )
            self.pipeline.to(self.device)
            
            if self.device == 'cuda' or self.device == 'cpu':
                self.pipeline.enable_attention_slicing()
            
            self.current_model = model_name
            logger.info(f"  模型加载成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"  模型加载失败: {e}")
            return False
        
    def _generate_mask_auto(self, image: Image.Image) -> Optional[Image.Image]:
        """自动生成遮罩（使用 YOLO）"""
        h, w = image.size[1], image.size[0]
        
        yolo = self._get_yolo_model()
        if not yolo or yolo is False:
            return None
        
        try:
            results = yolo(image, verbose=False)
            if len(results) == 0 or results[0].masks is None:
                return None
            
            masks = results[0].masks.data.cpu().numpy()
            combined = np.zeros((h, w), dtype=np.uint8)
            for m in masks:
                m_resized = cv2.resize(m, (w, h))
                combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)
            
            coords = np.where(combined > 0)
            if len(coords[0]) == 0:
                return None
            
            y_min, y_max = coords[0].min(), coords[0].max()
            body_h = y_max - y_min
            
            neck = y_min + int(body_h * 0.18)
            hip = y_min + int(body_h * 0.65)
            
            x_min, x_max = coords[1].min(), coords[1].max()
            body_w = x_max - x_min
            left = x_min + int(body_w * 0.08)
            right = x_max - int(body_w * 0.08)
            
            clothes = np.zeros_like(combined)
            clothes[neck:hip, left:right] = combined[neck:hip, left:right]
            
            kernel = np.ones((5, 5), np.uint8)
            clothes = cv2.dilate(clothes, kernel, iterations=1)
            clothes = cv2.GaussianBlur(clothes, (9, 9), 0)
            
            if np.sum(clothes > 0) < 100:
                return None
            
            return Image.fromarray(clothes, mode="L")
        except Exception as e:
            logger.warning(f"  YOLO 分割失败: {e}")
            return None
    
    def _generate_mask_manual(self, image: Image.Image) -> Image.Image:
        """手动绘制遮罩（用鼠标在图片上画）"""
        import cv2
        
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]
        
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30
        
        print("\n" + "="*50)
        print("手动绘制遮罩模式")
        print("="*50)
        print("  按住鼠标左键绘制遮罩（白色区域）")
        print("  滚轮调节画笔大小")
        print("  按 R 键重置遮罩")
        print("  按 Q 或 空格键 完成绘制")
        print("="*50 + "\n")
        
        def draw_callback(event, x, y, flags, param):
            nonlocal drawing, brush_size
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                cv2.circle(mask, (x, y), brush_size, 255, -1)
                cv2.circle(overlay, (x, y), brush_size, (0, 255, 0), -1)
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing:
                    cv2.circle(mask, (x, y), brush_size, 255, -1)
                    cv2.circle(overlay, (x, y), brush_size, (0, 255, 0), -1)
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False
            elif event == cv2.EVENT_MOUSEWHEEL:
                delta = flags
                if delta > 0:
                    brush_size = min(100, brush_size + 5)
                else:
                    brush_size = max(5, brush_size - 5)
                print(f"   画笔大小: {brush_size}")
        
        cv2.namedWindow('Draw Mask')
        cv2.setMouseCallback('Draw Mask', draw_callback)
        
        while True:
            display = img_cv.copy()
            mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)
            
            cv2.putText(mask_overlay, f"Brush: {brush_size}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(mask_overlay, "Draw clothes, press Q to finish", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            cv2.imshow('Draw Mask', mask_overlay)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q') or key == 32:
                break
            elif key == ord('r'):
                mask = np.zeros((h, w), dtype=np.uint8)
                overlay = np.zeros((h, w, 3), dtype=np.uint8)
                print("  遮罩已重置")
        
        cv2.destroyAllWindows()
        
        if np.sum(mask > 0) < 100:
            print("  遮罩区域太小，使用椭圆默认遮罩")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w//4, h//3), 0, 0, 360, 255, -1)
        
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        print(f"  遮罩完成，覆盖 {np.sum(mask > 0)} 像素")
        return Image.fromarray(mask, mode="L")
    
    def _generate_mask(self, image: Image.Image, use_manual: bool = False) -> Image.Image:
        """生成衣服遮罩"""
        if use_manual:
            return self._generate_mask_manual(image)
        
        mask = self._generate_mask_auto(image)
        if mask is not None:
            logger.info("  使用 YOLO 自动遮罩")
            return mask
        
        logger.info("  自动遮罩失败，切换到手动绘制")
        return self._generate_mask_manual(image)
    
    def _generate_pose_image(self, image: Image.Image) -> Optional[Image.Image]:
        """生成 OpenPose 姿态图"""
        if self._openpose is None:
            return None
        
        try:
            pose = self._openpose(image)
            return pose
        except Exception as e:
            logger.warning(f"  姿态图生成失败: {e}")
            return None
        
    def _load_model_from_path(self, model_path: str) -> bool:
        """直接从路径加载模型"""
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False
        
        try:
            logger.info(f"从路径加载模型: {model_path}")
            
            use_controlnet = self.config.get('use_controlnet', True)
            controlnet = None
            if use_controlnet and CONTROLNET_AVAILABLE:
                try:
                    logger.info("  加载 ControlNet...")
                    controlnet = ControlNetModel.from_pretrained(
                        "lllyasviel/control_v11p_sd15_openpose",
                        torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                    )
                    from controlnet_aux import OpenPoseDetector
                    self._openpose = OpenPoseDetector.from_pretrained("lllyasviel/ControlNet")
                    logger.info("  ControlNet 加载成功")
                except Exception as e:
                    logger.warning(f"  ControlNet 加载失败: {e}")
                    controlnet = None
            
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                controlnet=controlnet,
            )
            self.pipeline.to(self.device)
            
            if self.device == 'cuda' or self.device == 'cpu':
                self.pipeline.enable_attention_slicing()
            
            self.current_model = Path(model_path).name
            logger.info(f"  模型加载成功: {self.current_model}")
            return True
            
        except Exception as e:
            logger.error(f"  模型加载失败: {e}")
            return False
    
    def _resize_image(self, image: Image.Image) -> tuple:
        """等比例缩放图片到合适尺寸"""
        original_size = image.size
        
        min_size = 512
        max_size = 1024
        
        need_resize = False
        new_size = original_size
        
        if min(original_size) < min_size:
            ratio = min_size / min(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            need_resize = True
        elif max(original_size) > max_size:
            ratio = max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            need_resize = True
        
        if need_resize:
            logger.info(f"  等比例缩放: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            original_size = new_size
        
        # 确保是 8 的倍数
        width = (original_size[0] // 8) * 8
        height = (original_size[1] // 8) * 8
        if width != original_size[0] or height != original_size[1]:
            new_image = Image.new("RGB", (width, height), (0, 0, 0))
            x_offset = (width - original_size[0]) // 2
            y_offset = (height - original_size[1]) // 2
            new_image.paste(image, (x_offset, y_offset))
            image = new_image
            logger.info(f"  填充对齐: {original_size[0]}x{original_size[1]} -> {width}x{height}")
            original_size = (width, height)
        
        return image, original_size
        
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
                - manual_mask: 是否手动绘制遮罩 (可选)
        
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
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')
            manual_mask = kwargs.get('manual_mask', False)
            
            # 2. 加载模型
            if model_path:
                if not os.path.exists(model_path):
                    return {"status": "error", "error": f"模型不存在: {model_path}"}
                if not self._load_model_from_path(model_path):
                    return {"status": "error", "error": f"无法加载模型: {model_path}"}
            else:
                model_name = model_name or self.config.get('default_model', 'sd-v1-5-inpainting-tiny.safetensors')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"无法加载模型: {model_name}"}
            
            # 3. 获取生成参数
            prompt = kwargs.get('prompt')
            if prompt is None:
                prompt = self.config.get('default_prompt', 'nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic')
            
            negative_prompt = kwargs.get('negative_prompt')
            if negative_prompt is None:
                negative_prompt = self.config.get('default_negative', 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime')
            
            strength = kwargs.get('strength', self.config.get('default_strength', 0.5))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            output_dir = kwargs.get('output_dir', self.config.get('output_dir'))
            save_mask = kwargs.get('save_mask', False)
            
            # 4. 加载并缩放图片
            image = Image.open(image_path).convert("RGB")
            image, original_size = self._resize_image(image)
            
            logger.info(f"处理: {os.path.basename(image_path)} ({image.size[0]}x{image.size[1]})")
            
            # 5. 生成遮罩
            logger.info("生成遮罩...")
            mask = self._generate_mask(image, use_manual=manual_mask)
            
            if save_mask:
                mask_path = image_path.replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)
                logger.info(f"  遮罩: {os.path.basename(mask_path)}")
            
            # 6. 生成姿态图（如果使用 ControlNet）
            control_image = None
            use_controlnet = self.config.get('use_controlnet', True)
            if use_controlnet and self._openpose is not None:
                logger.info("生成姿态图...")
                control_image = self._generate_pose_image(image)
                if control_image is not None:
                    logger.info("  姿态图生成完成")
            
            # 7. 设置随机种子
            if seed == -1:
                seed = random.randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)
            
            logger.info("SD Inpaint 生成中...")
            logger.info(f"  提示词: {prompt[:50]}...")
            logger.info(f"  步数: {steps}")
            logger.info(f"  强度: {strength}")
            logger.info(f"  种子: {seed}")
            if control_image is not None:
                logger.info("  ControlNet: 已启用")
            
            # 8. 执行 Inpaint
            current_size = image.size
            if control_image is not None:
                result = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt if negative_prompt else None,
                    image=image,
                    mask_image=mask,
                    control_image=control_image,
                    strength=strength,
                    num_inference_steps=steps,
                    guidance_scale=7.5,
                    generator=generator,
                    width=current_size[0],
                    height=current_size[1],
                ).images[0]
            else:
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
            
            # 9. 保存结果
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir_path = Path(output_dir)
                output_dir_path.mkdir(parents=True, exist_ok=True)
                filename = f"{Path(image_path).stem}_{timestamp}_nude.png"
                output_path = str(output_dir_path / filename)
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            result.save(output_path)
            
            generation_time = time.time() - start_time
            logger.info(f"  保存: {os.path.basename(output_path)}")
            
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
                    "device": self.device,
                    "controlnet": control_image is not None,
                    "manual_mask": manual_mask
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
    parser.add_argument("--model", "-m", default="zenityXmix.inpainting.safetensors", help="模型名称")
    parser.add_argument("--prompt", "-p", default="nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic", help="生成提示词")
    parser.add_argument("--negative", "-n", default="clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime", help="负面提示词")
    parser.add_argument("--strength", "-s", type=float, default=0.5, help="重绘强度")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="设备")
    parser.add_argument("--save-mask", action="store_true", help="保存遮罩")
    parser.add_argument("--manual-mask", action="store_true", help="手动绘制遮罩")
    parser.add_argument("--no-controlnet", action="store_true", help="禁用 ControlNet")
    
    args = parser.parse_args()
    
    skill = ClothesRemover(config={'device': args.device, 'use_controlnet': not args.no_controlnet})
    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        model_name=args.model,
        prompt=args.prompt,
        negative_prompt=args.negative,
        strength=args.strength,
        steps=args.steps,
        seed=args.seed,
        save_mask=args.save_mask,
        manual_mask=args.manual_mask
    )
    
    if result['status'] == 'success':
        print(f"\n成功!")
        print(f"  输出: {result['output_path']}")
        print(f"  耗时: {result['generation_time']}")
        print(f"  参数:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n失败: {result.get('error', '未知错误')}")