# markflow/skills/remove_clothes/skill.py
"""
衣服移除 Skill - 使用本地 SD Inpaint 模型
"""

import os
import torch
import numpy as np
from PIL import Image, ImageDraw
import cv2
from typing import Optional
from pathlib import Path


class ClothesRemover:
    """衣服移除器"""
    
    def __init__(self, device: str = "cpu", model_path: str = None):
        self.device = device
        self._yolo_model = None
        self._sd_pipe = None
        
        # 获取项目根目录（向上5级到 SD_OpenVINO）
        # MarkFlow/markflow/skills/remove_clothes/skill.py
        # 向上5级: SD_OpenVINO/
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        
        # 默认模型路径: SD_OpenVINO/models/sd-v1-5/sd-v1-5-inpainting-tiny.safetensors
        self.default_model_path = self.project_root / "models" / "sd-v1-5" / "sd-v1-5-inpainting-tiny.safetensors"
        
        # 如果指定了模型路径，使用指定的
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = self.default_model_path
        
        print("👕 衣服移除器已初始化")
        print(f"   📂 项目根目录: {self.project_root}")
        print(f"   📦 模型路径: {self.model_path}")
        print(f"   ✅ 模型存在: {self.model_path.exists()}")
    
    def _get_yolo_model(self):
        if self._yolo_model is None:
            try:
                from ultralytics import YOLO
                self._yolo_model = YOLO("yolov8n-seg.pt")
                print("   ✅ YOLO 加载成功")
            except ImportError:
                print("   ⚠️ ultralytics 未安装，将使用手动遮罩")
                self._yolo_model = False
            except Exception as e:
                print(f"   ⚠️ YOLO 加载失败: {e}")
                self._yolo_model = False
        return self._yolo_model
    
    def _load_sd_model(self):
        """加载本地 SD Inpaint 模型"""
        if self._sd_pipe is None:
            try:
                from diffusers import StableDiffusionInpaintPipeline
                
                # 检查模型是否存在
                if not self.model_path.exists():
                    print(f"   ❌ 模型不存在: {self.model_path}")
                    print(f"\n   📥 请下载模型并放到:")
                    print(f"      {self.model_path}")
                    print(f"\n   🔗 下载地址:")
                    print(f"      https://huggingface.co/runwayml/stable-diffusion-inpainting")
                    print(f"\n   💡 或使用 HuggingFace 在线模型:")
                    print(f"      python scripts/generate_images.py --remove-clothes --input image.jpg --model runwayml/stable-diffusion-inpainting")
                    self._sd_pipe = False
                    return self._sd_pipe
                
                print(f"   📦 加载模型: {self.model_path.name}")
                self._sd_pipe = StableDiffusionInpaintPipeline.from_single_file(
                    str(self.model_path),
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    requires_safety_checker=False,
                )
                self._sd_pipe.to(self.device)
                if self.device == "cpu":
                    self._sd_pipe.enable_attention_slicing()
                print("   ✅ SD Inpaint 模型加载成功")
                
            except ImportError:
                print("   ❌ 未安装 diffusers")
                print("   💡 安装: pip install diffusers transformers accelerate")
                self._sd_pipe = False
            except Exception as e:
                print(f"   ❌ SD 模型加载失败: {e}")
                self._sd_pipe = False
        return self._sd_pipe
    
    def _generate_mask(self, image: Image.Image) -> Image.Image:
        """生成衣服遮罩"""
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
                        neck = y_min + int(body_h * 0.18)
                        hip = y_min + int(body_h * 0.70)
                        
                        x_min, x_max = coords[1].min(), coords[1].max()
                        body_w = x_max - x_min
                        left = x_min + int(body_w * 0.10)
                        right = x_max - int(body_w * 0.10)
                        
                        clothes = np.zeros_like(combined)
                        clothes[neck:hip, left:right] = combined[neck:hip, left:right]
                        clothes = cv2.GaussianBlur(clothes, (9, 9), 0)
                        return Image.fromarray(clothes, mode="L")
            except Exception as e:
                print(f"   ⚠️ YOLO 失败: {e}")
        
        # 备用：手动绘制遮罩
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        cx, cy = w // 2, h // 2
        draw.ellipse((cx - w//4, cy - h//3, cx + w//4, cy + h//3), fill=255)
        return mask
    
    def remove_clothes(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        prompt: str = "nude, naked body, beautiful skin, realistic body, masterpiece, best quality",
        negative_prompt: str = "clothes, fabric, ugly, deformed, bad anatomy, cropped",
        strength: float = 0.85,
        steps: int = 30,
        seed: Optional[int] = None,
        save_mask: bool = False
    ) -> str:
        """去除衣服 - 保持原始尺寸（不缩放）"""
        sd = self._load_sd_model()
        if sd is None or sd is False:
            raise RuntimeError("SD 模型不可用，请检查模型路径")
        
        # 加载图片
        image = Image.open(image_path).convert("RGB")
        original_size = image.size
        
        print(f"   📷 处理: {os.path.basename(image_path)} ({original_size[0]}x{original_size[1]})")
        
        print("   🎯 生成遮罩...")
        mask = self._generate_mask(image)
        
        if save_mask:
            mask_path = image_path.replace('.png', '_mask.png').replace('.jpg', '_mask.png')
            mask.save(mask_path)
            print(f"   📋 遮罩: {os.path.basename(mask_path)}")
        
        print(f"   🎨 SD Inpaint 生成中...")
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        result = sd(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            mask_image=mask,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=7.5,
            generator=generator,
            width=original_size[0],
            height=original_size[1],
        ).images[0]
        
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_nude{ext}"
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
        result.save(output_path)
        print(f"   ✅ 保存: {os.path.basename(output_path)}")
        return output_path


def execute(**kwargs) -> bool:
    """
    执行衣服移除
    
    参数:
        input_path: 输入图片路径
        output_path: 输出图片路径（可选）
        model_path: SD Inpaint 模型路径（可选）
        prompt: 生成提示词
        negative_prompt: 负面提示词
        strength: 重绘强度 (0.0-1.0)
        steps: 迭代步数
        seed: 随机种子
        device: 设备 (cpu/cuda)
        save_mask: 是否保存遮罩
    """
    input_path = kwargs.get('input_path')
    output_path = kwargs.get('output_path')
    model_path = kwargs.get('model_path')
    prompt = kwargs.get('prompt', "nude, naked body, beautiful skin, realistic body, masterpiece, best quality")
    negative_prompt = kwargs.get('negative_prompt', "clothes, fabric, ugly, deformed, bad anatomy, cropped")
    strength = kwargs.get('strength', 0.85)
    steps = kwargs.get('steps', 30)
    seed = kwargs.get('seed', None)
    device = kwargs.get('device', 'cpu')
    save_mask = kwargs.get('save_mask', False)
    
    if not input_path or not os.path.exists(input_path):
        print(f"❌ 图片不存在: {input_path}")
        return False
    
    try:
        remover = ClothesRemover(device=device, model_path=model_path)
        result = remover.remove_clothes(
            input_path, output_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            steps=steps,
            seed=seed,
            save_mask=save_mask
        )
        print(f"\n✅ 完成: {result}")
        return True
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False