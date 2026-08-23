#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SD 图片批量生成器 - 安全优雅版
用法：
  python generate_images.py           # 生成所有方案
  python generate_images.py --list    # 列出所有方案
  python generate_images.py --id 1    # 只生成第 1 组
  python generate_images.py --ids 1,3,5  # 生成指定的组
"""

import sys
import subprocess
import argparse
import time
from datetime import datetime
from pathlib import Path


class SDImageGenerator:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        # ✅ 改为指向技能的输出目录
        self.output_dir = self.base_dir / "skills" / "sd_image_generator" / "output" / "images"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ✅ 所有方案配置 - 安全优雅版
        self.schemes = [
            {
                "id": 1,
                "name": "优雅亚洲女性肖像",
                "prompt": "elegant Asian woman, beautiful face, soft smile, natural makeup, studio photography, professional portrait, soft natural lighting, high quality, sharp focus, graceful pose, elegant outfit, refined, sophisticated, 8k, photorealistic",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural body, oversaturated, distorted face",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 2,
                "name": "自然光唯美女性",
                "prompt": "beautiful woman, natural sunlight, soft glowing skin, gentle expression, flowing hair, elegant dress, serene atmosphere, nature background, golden hour, warm tones, professional photography, high quality, sharp focus, graceful, photorealistic",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, harsh lighting",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 3,
                "name": "都市时尚女性",
                "prompt": "stylish woman, urban fashion, elegant outfit, confident pose, city background, modern style, natural lighting, high quality, sharp focus, beautiful face, graceful, professional photography, 8k, photorealistic, sophisticated",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural body, oversaturated",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 4,
                "name": "优雅晚装女性",
                "prompt": "elegant woman in evening gown, sophisticated, refined, soft lighting, beautiful face, graceful pose, luxurious fabric, elegant jewelry, formal setting, professional photography, high quality, sharp focus, photorealistic, 8k, stunning",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, revealing, exposed",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 5,
                "name": "清新自然女性",
                "prompt": "fresh natural woman, minimal makeup, natural beauty, soft smile, casual outfit, outdoor setting, soft sunlight, gentle breeze, peaceful atmosphere, high quality, sharp focus, photorealistic, 8k, beautiful, elegant",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural body, oversaturated, heavy makeup",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 6,
                "name": "光影艺术肖像",
                "prompt": "artistic portrait, beautiful woman, dramatic lighting, chiaroscuro, elegant expression, refined features, soft shadows, high contrast, professional photography, high quality, sharp focus, photorealistic, 8k, masterpiece, graceful",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, revealing, exposed",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.0,
                "seed": -1
            },
            {
                "id": 7,
                "name": "复古优雅女性",
                "prompt": "vintage elegance, beautiful woman, retro style, classic outfit, timeless beauty, soft lighting, warm tones, old Hollywood glamour, graceful pose, professional photography, high quality, sharp focus, photorealistic, 8k, stunning",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, modern, casual",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 8,
                "name": "梦幻唯美女性",
                "prompt": "dreamy ethereal woman, soft focus, glowing atmosphere, flowing dress, beautiful face, gentle expression, magical lighting, soft pastel colors, artistic, high quality, sharp focus, photorealistic, 8k, graceful, elegant",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, harsh lighting",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 9,
                "name": "优雅侧影肖像",
                "profile": True,
                "prompt": "elegant profile portrait, beautiful woman, side view, refined features, graceful neck, soft lighting, elegant hairstyle, sophisticated, professional photography, high quality, sharp focus, photorealistic, 8k, stunning",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, front view, full face",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 10,
                "name": "柔美光影女性",
                "prompt": "soft beautiful woman, gentle lighting, warm ambiance, serene expression, elegant outfit, peaceful setting, natural beauty, professional photography, high quality, sharp focus, photorealistic, 8k, graceful, refined",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, revealing, exposed",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 11,
                "name": "时尚封面女性",
                "prompt": "fashion magazine cover, beautiful woman, high fashion, elegant pose, designer outfit, stylish, sophisticated, studio lighting, professional photography, high quality, sharp focus, photorealistic, 8k, stunning, graceful",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, casual, amateur",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 12,
                "name": "优雅半身肖像",
                "prompt": "elegant half-body portrait, beautiful woman, refined features, graceful posture, sophisticated outfit, professional photography, soft lighting, high quality, sharp focus, photorealistic, 8k, stunning, natural expression",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, bad hands, unnatural pose, oversaturated, revealing, exposed",
                "model": "anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 13,
                "name": "优雅双人合影",
                "prompt": "two elegant women, friendly portrait, graceful poses, beautiful faces, sophisticated outfits, warm atmosphere, studio photography, soft lighting, high quality, sharp focus, photorealistic, 8k, refined, stylish",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, extra hands, fused bodies, merged faces, bad proportions, unnatural pose, revealing, exposed",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 14,
                "name": "闺蜜优雅合影",
                "prompt": "two beautiful women, friends portrait, elegant outfits, warm embrace, beautiful smiles, sophisticated style, studio photography, soft natural lighting, high quality, sharp focus, photorealistic, 8k, graceful, refined",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, extra hands, fused bodies, merged faces, bad proportions, unnatural pose, revealing, exposed",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 15,
                "name": "光影艺术双人",
                "prompt": "artistic dual portrait, two elegant women, dramatic lighting, sophisticated poses, refined beauty, artistic composition, studio photography, high quality, sharp focus, photorealistic, 8k, masterpiece, graceful, stylish",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, extra hands, fused bodies, merged faces, bad proportions, unnatural pose, revealing, exposed",
                "model": "realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 20,
                "cfg_scale": 7.5,
                "seed": -1
            }
        ]

    def run_command(self, cmd):
        try:
            result = subprocess.run(cmd, text=True, encoding='utf-8', errors='replace')
            return result.returncode == 0
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return False

    # scripts/generate_all_girls.py 的 generate_one 方法

    def generate_one(self, scheme):
        """生成单张图片 - 直接调用"""
        print(f"\n{'='*60}")
        print(f"   [{scheme['id']}/15] {scheme['name']}")
        print('='*60)

        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from markflow.cli.commands import execute_skill

        seed = scheme.get('seed', -1)
        if isinstance(seed, str):
            try:
                seed = int(seed)
            except:
                seed = -1

        try:
            result = execute_skill(
                "sd_image_generator",
                prompt=scheme["prompt"],
                negative_prompt=scheme["negative_prompt"],
                model_name=scheme["model"],
                width=scheme["width"],
                height=scheme["height"],
                steps=scheme["steps"],
                cfg_scale=scheme["cfg_scale"],
                seed=seed,
                batch_size=scheme.get("batch_size", 1)
            )
            return result is not None
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            return False
        
    def list_schemes(self):
        """列出所有方案"""
        print("\n" + "="*60)
        print("   📸 SD 图片生成方案列表 - 安全优雅版")
        print("="*60)
        print()
        print(f"{'ID':<4} {'名称':<20} {'模型':<35} {'尺寸'}")
        print("-"*80)
        for s in self.schemes:
            print(f"{s['id']:<4} {s['name']:<20} {s['model']:<35} {s['width']}x{s['height']}")
        print()
        print(f"共 {len(self.schemes)} 个方案")
        print("\n💡 所有方案均使用安全、优雅的描述，适合各种场合使用。")

    def generate_by_id(self, ids):
        """根据 ID 生成"""
        for s in self.schemes:
            if s['id'] in ids:
                self.generate_one(s)

    def generate_all(self):
        """生成所有"""
        total = len(self.schemes)
        success = 0
        for s in self.schemes:
            if self.generate_one(s):
                success += 1
            time.sleep(0.5)
        print(f"\n✅ 完成！成功 {success}/{total} 张")

    def run(self, args):
        if args.list:
            self.list_schemes()
            return

        if args.id:
            self.generate_by_id([args.id])
            return

        if args.ids:
            ids = [int(x.strip()) for x in args.ids.split(',')]
            self.generate_by_id(ids)
            return

        self.generate_all()


def main():
    parser = argparse.ArgumentParser(
        description="SD 图片批量生成器 - 安全优雅版",
        epilog="示例：\n"
               "  python generate_images.py              # 生成所有方案\n"
               "  python generate_images.py --list       # 列出所有方案\n"
               "  python generate_images.py --id 1       # 生成第 1 组\n"
               "  python generate_images.py --ids 1,3,5  # 生成指定组"
    )
    parser.add_argument("--list", action="store_true", help="列出所有方案")
    parser.add_argument("--id", type=int, help="生成指定 ID 的方案")
    parser.add_argument("--ids", type=str, help="生成多个方案，用逗号分隔，如 1,3,5")

    args = parser.parse_args()
    generator = SDImageGenerator()
    generator.run(args)


if __name__ == "__main__":
    main()