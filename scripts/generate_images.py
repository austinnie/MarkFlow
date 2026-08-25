#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SD 图片批量生成器 - 配置文件版
用法：
  python generate_images.py                    # 生成所有方案
  python generate_images.py --list             # 列出所有方案
  python generate_images.py --id 1             # 只生成第 1 组
  python generate_images.py --ids 1,3,5        # 生成指定的组
  python generate_images.py --config custom.json # 使用自定义配置
"""

import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


class SDImageGenerator:
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.output_dir = Path(self.config.get("output_dir", "./skills/sd_image_generator/output/images"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.schemes = self.config.get("schemes", [])
        self.default_params = self.config.get("default_params", {})

    def _load_config(self, config_path: str = None):
        """加载配置文件"""
        if config_path is None:
            config_path = Path(__file__).parent / "configs" / "girls_config.json"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            print(f"❌ 配置文件不存在: {config_path}")
            print("   请确保 configs/girls_config.json 存在")
            sys.exit(1)

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_one(self, scheme):
        """生成单张图片"""
        print(f"\n{'='*60}")
        print(f"   [{scheme['id']}/{len(self.schemes)}] {scheme['name']}")
        print('='*60)

        # 合并默认参数
        params = self.default_params.copy()
        params.update(scheme)

        # 处理 seed
        seed = params.get('seed', -1)
        if isinstance(seed, str):
            try:
                seed = int(seed)
            except:
                seed = -1
        params['seed'] = seed

        try:
            result = execute_skill(
                "sd_image_generator",
                prompt=params["prompt"],
                negative_prompt=params.get("negative_prompt", ""),
                model_name=params.get("model", self.default_params.get("model", "anytimeRealistic_v10.safetensors")),
                width=params.get("width", 512),
                height=params.get("height", 768),
                steps=params.get("steps", 30),
                cfg_scale=params.get("cfg_scale", 7.5),
                seed=seed,
                batch_size=params.get("batch_size", 1)
            )
            return result is not None
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            return False

    def list_schemes(self):
        """列出所有方案"""
        print("\n" + "="*70)
        print("   📸 SD 图片生成方案列表")
        print("="*70)
        print()
        print(f"{'ID':<4} {'名称':<25} {'尺寸':<12} {'步数':<6} {'CFG':<6}")
        print("-"*70)
        for s in self.schemes:
            w = s.get('width', self.default_params.get('width', 512))
            h = s.get('height', self.default_params.get('height', 768))
            steps = s.get('steps', self.default_params.get('steps', 30))
            cfg = s.get('cfg_scale', self.default_params.get('cfg_scale', 7.5))
            print(f"{s['id']:<4} {s['name']:<25} {w}x{h:<6} {steps:<6} {cfg:<6}")
        print()
        print(f"共 {len(self.schemes)} 个方案")
        print(f"默认模型: {self.default_params.get('model', '未指定')}")

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
        description="SD 图片批量生成器 - 配置文件版",
        epilog="示例：\n"
               "  python generate_images.py                    # 生成所有方案\n"
               "  python generate_images.py --list             # 列出所有方案\n"
               "  python generate_images.py --id 1             # 生成第 1 组\n"
               "  python generate_images.py --ids 1,3,5        # 生成指定组\n"
               "  python generate_images.py --config custom.json # 使用自定义配置"
    )
    parser.add_argument("--list", action="store_true", help="列出所有方案")
    parser.add_argument("--id", type=int, help="生成指定 ID 的方案")
    parser.add_argument("--ids", type=str, help="生成多个方案，用逗号分隔，如 1,3,5")
    parser.add_argument("--config", type=str, help="使用自定义配置文件")

    args = parser.parse_args()
    generator = SDImageGenerator(args.config)
    generator.run(args)


if __name__ == "__main__":
    main()