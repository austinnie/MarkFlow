#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SD 图片批量生成器
用法：
  python generate_images.py           # 生成所有 15 组
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
        self.base_dir = Path(__file__).parent
        self.output_dir = self.base_dir / "generated_images"
        self.output_dir.mkdir(exist_ok=True)

        # ✅ 模型路径前缀（模型在 sd-v1-5 子目录下）
        MODEL_PREFIX = "sd-v1-5/"
        
        # 所有方案配置
        self.schemes = [
            {
                "id": 1,
                "name": "纯欲风亚洲美女",
                "prompt": "beautiful Asian woman, photorealistic, detailed face, natural lighting, high quality, 8k, sharp focus, gorgeous body, big breasts, ample cleavage, sexy white lace lingerie, silky skin, smooth body, seductive pose, elegant, cinematic lighting",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, deformed breasts, extra fingers, bad proportions, bad hands, unnatural body",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 2,
                "name": "曲线超写实亚洲美女",
                "prompt": "beautiful Asian woman, photorealistic, natural lighting, detailed face, soft smile, high quality, curvy hourglass figure, big breasts, deep cleavage, sexy sheer transparent dress, elegant posture, delicate skin, attractive beautiful body, soft glowing skin, alluring",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, deformed breasts, sagging, weird cleavage, illogical clothing, flat chest, unnatural body, extra fingers",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 3,
                "name": "成熟性感亚洲美女",
                "prompt": "beautiful Asian woman, photorealistic, detailed face, natural lighting, high quality, 8k, busty, large breasts, ample cleavage, sexy tight dress, revealing, slim waist, wide hips, hourglass figure, beautiful female body, soft cinematic lighting, realistic skin texture",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, bad hands, extra fingers, awkward pose, deformed breasts, sagging, unrealistic clothing",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 4,
                "name": "写实西方模特",
                "prompt": "a beautiful woman, photorealistic, detailed face, natural lighting, high quality, 8k, sharp focus, gorgeous body, big breasts, ample cleavage, seductive pose, sexy tight dress, beautiful female body, soft glowing skin",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, deformed breasts, extra fingers, bad proportions",
                "model": f"{MODEL_PREFIX}anytimeRealistic_v10.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 5,
                "name": "亚洲唯美曲线",
                "prompt": "beautiful Asian woman, photorealistic, natural lighting, detailed face, soft smile, high quality, curvy hourglass figure, big breasts, deep cleavage, sexy transparent lace dress, elegant posture, delicate skin, attractive beautiful body, cinematic lighting",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, deformed breasts, sagging, weird cleavage, illogical clothing, flat chest, unnatural body",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 6,
                "name": "欧美沙漏型身材",
                "prompt": "beautiful European woman, photorealistic, detailed face, natural lighting, high quality, 8k, busty, large breasts, ample cleavage, sexy lingerie, revealing, slim waist, wide hips, hourglass figure, alluring, beautiful female body, soft cinematic lighting",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, bad hands, extra fingers, awkward pose, deformed breasts, sagging",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.0,
                "seed": -1
            },
            {
                "id": 7,
                "name": "柔美性感风",
                "prompt": "beautiful Asian woman, photorealistic, natural lighting, detailed face, soft smile, high quality, 8k, sharp focus, realistic skin texture, big breasts, ample cleavage, sexy lingerie, delicate lace bra, slim waist, curvy body, elegant posture, soft chest, attractive figure, graceful, alluring, beautiful body",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, deformed breasts, sagging, extra arms, extra fingers, bad hands, missing fingers, long neck, bad proportions, unnatural body, weird cleavage, illogical clothing, clothed",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 8,
                "name": "若隐若现透视风",
                "prompt": "beautiful Asian woman, photorealistic, natural lighting, high quality, 8k, detailed face, soft smile, see-through lace dress, white sheer fabric, revealing, showing cleavage, large breasts, deep cleavage, glowing skin, soft skin, wet skin look, seductive pose, beautiful body, elegant",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, bad hands, extra fingers, awkward pose",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 9,
                "name": "极致身材与光影",
                "prompt": "beautiful European and Asian mix, photorealistic, detailed face, natural lighting, high quality, 8k, extreme detail, big breasts, push-up bra, tight fitting dress, hourglass figure, slim waist, wide hips, erotic, beautiful body, gorgeous, beautiful female body, soft glowing skin, cinematic lighting",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, bad hands, extra fingers, awkward pose",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 10,
                "name": "唯美蕾丝透感",
                "prompt": "beautiful Asian woman, photorealistic, detailed face, natural lighting, high quality, 8k, sharp focus, big breasts, ample cleavage, wearing sheer white lace bra, subtle nipple outline, nipple bulge piercing through fabric, lace transparency, soft peaks, delicate skin texture, alluring, elegant, cinematic lighting",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, deformed breasts, weird nipple, nude, naked, topless, bare breasts, sagging, unnatural body, extra fingers, bad hands",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 11,
                "name": "极致光影勾勒",
                "prompt": "photorealistic Asian woman, attractive figure, high quality, 8k, cinematic lighting, big breasts, deep cleavage, wearing a very thin transparent silk camisole, visible nipple bulge, tight fit, revealing silhouette, wet fabric clinging to skin, exquisite skin texture, warm ambient lighting, beautiful female body, elegant",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, deformed breasts, extreme close up, nude, naked, topless, bare breasts, bad proportions, extra fingers, awkward pose",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 12,
                "name": "柔软曲线微凸",
                "prompt": "beautiful Asian woman, photorealistic, natural lighting, detailed face, soft smile, high quality, curvy hourglass figure, big breasts, deep cleavage, delicate lace lingerie, subtle nipple outline, soft peaks, pushing against fabric, soft glowing skin, beautiful female body, natural body shape, graceful, alluring",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, flat chest, deformed breasts, lumpy breasts, extreme close up, nude, naked, topless, bare breasts, bad hands, extra fingers, unnatural body",
                "model": f"{MODEL_PREFIX}asianrealisticSdlife_v40.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 13,
                "name": "蕾丝内衣亲密贴贴",
                "prompt": "two beautiful Asian women, photorealistic, 8k, cinematic lighting, detailed faces, delicate skin, intimate hug, soft embrace, big breasts, ample cleavage, wearing sheer lace lingerie, glowing skin, sexy, attractive bodies, natural lighting, high quality, sharp focus",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra fingers, extra hands, fused bodies, merged faces, deformed breasts, bad proportions, flat chest, bad hands, illogical clothing",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 14,
                "name": "透视薄纱唯美互动",
                "prompt": "two beautiful Asian women, photorealistic, high quality, 8k, soft glowing skin, gorgeous figures, deep cleavage, curvy bodies, sexy sheer see-through dresses, intimate position, sitting together, touching gently, alluring expressions, beautiful female bodies, cinematic soft lighting",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, long necks, missing arms, merged bodies, weird cleavage, unnatural pose, bad hands, extra limbs",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
                "cfg_scale": 7.5,
                "seed": -1
            },
            {
                "id": 15,
                "name": "卧室亲密氛围",
                "prompt": "two beautiful Asian women, photorealistic, detailed face, natural soft lighting, high quality, curvy hourglass figures, big breasts, sexy tight silk nightgowns, intimate embrace, leaning on each other, bedroom setting, realistic skin texture, beautiful bodies, seductive, gorgeous",
                "negative_prompt": "ugly, blurry, cartoon, anime, painting, low quality, deformed, bad anatomy, extra arms, fused fingers, weird hands, flat chest, sagging, bad proportions, unnatural pose, distorted face, extra legs",
                "model": f"{MODEL_PREFIX}realisticmix_iiV12Version12.safetensors",
                "width": 512,
                "height": 768,
                "steps": 30,
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

    def generate_one(self, scheme):
        """生成单张图片"""
        print(f"\n{'='*60}")
        print(f"   [{scheme['id']}/15] {scheme['name']}")
        print('='*60)

        cmd = [
            "python", "-m", "markflow.cli.commands", "execute", "Sdimagegenerator",
            f'prompt="{scheme["prompt"]}"',
            f'negative_prompt="{scheme["negative_prompt"]}"',
            f'model_name="{scheme["model"]}"',
            f'width={scheme["width"]}',
            f'height={scheme["height"]}',
            f'steps={scheme["steps"]}',
            f'cfg_scale={scheme["cfg_scale"]}',
            f'seed={scheme["seed"]}'
        ]

        return self.run_command(cmd)

    def list_schemes(self):
        """列出所有方案"""
        print("\n" + "="*60)
        print("   📸 SD 图片生成方案列表")
        print("="*60)
        print()
        print(f"{'ID':<4} {'名称':<20} {'模型':<35} {'尺寸'}")
        print("-"*80)
        for s in self.schemes:
            print(f"{s['id']:<4} {s['name']:<20} {s['model']:<35} {s['width']}x{s['height']}")
        print()
        print(f"共 {len(self.schemes)} 个方案")

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
            time.sleep(0.5)  # 避免请求过快
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

        # 默认：生成所有
        self.generate_all()


def main():
    parser = argparse.ArgumentParser(
        description="SD 图片批量生成器",
        epilog="示例：\n"
               "  python generate_images.py              # 生成所有 15 组\n"
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