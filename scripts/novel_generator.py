#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说生成器 - 每日续写指定章节 + 有声书
用法：python novel_generator.py [章节数]
示例：python novel_generator.py 6    # 续写到6章
      python novel_generator.py       # 默认每天+3章
"""

import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path


class NovelGenerator:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.novel_dir = self.base_dir / "generated_novels"
        self.audio_dir = self.base_dir / "audio_output"
        self.novel_dir.mkdir(exist_ok=True)
        self.audio_dir.mkdir(exist_ok=True)

    def get_today(self):
        return datetime.now().strftime("%Y%m%d")

    def get_today_display(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run_command(self, cmd):
        try:
            result = subprocess.run(cmd, text=True, encoding='utf-8', errors='replace')
            if result.returncode != 0:
                print(f"⚠️ 命令执行失败，返回码: {result.returncode}")
                return False
            return True
        except Exception as e:
            print(f"❌ 执行异常: {e}")
            return False

    def get_current_chapters(self, novel_file: Path) -> int:
        """统计当前章节数"""
        if not novel_file.exists():
            return 0
        try:
            with open(novel_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # 统计 "第X章" 的数量
            import re
            chapters = re.findall(r'第\d+章', content)
            return len(chapters)
        except:
            return 0

    def get_novel_file(self) -> Path:
        """获取当前使用的小说文件"""
        today = self.get_today()
        zh_file = self.novel_dir / f"novel_zh_{today}.txt"
        
        # 优先使用今天的文件
        if zh_file.exists():
            return zh_file
        
        # 查找最近的小说文件
        zh_files = list(self.novel_dir.glob("novel_zh_*.txt"))
        if zh_files:
            return sorted(zh_files)[-1]
        
        # 兼容旧文件
        old_files = list(self.novel_dir.glob("星际行者*.txt"))
        if old_files:
            return sorted(old_files)[-1]
        
        return None

    def continue_novel(self, novel_file: Path, target_chapters: int) -> bool:
        """续写小说到目标章节数"""
        current = self.get_current_chapters(novel_file)
        
        if current >= target_chapters:
            print(f"✅ 已有 {current} 章，已达到目标 {target_chapters} 章")
            return True
        
        print(f"📝 从 {current} 章续写到 {target_chapters} 章（+{target_chapters - current} 章）")
        
        cmd = [
            "python", "-m", "markflow.cli.commands", "execute", "NovelWriterOllama",
            "genre=科幻",
            "title=星际行者",
            "outline=一个普通少年意外获得星际航行能力，在宇宙中探索未知文明",
            "characters=主角阿星，16岁，好奇心强；AI助手小智，幽默风趣",
            f"chapter_count={target_chapters}",
            "model=qwen2.5:7b",
            f"continue_from={novel_file}"
        ]
        
        return self.run_command(cmd)

    def generate_audiobook(self, text_file: Path) -> bool:
        """生成有声书"""
        today = self.get_today()
        audio_file = self.audio_dir / f"novel_zh_{today}.mp3"

        print("[2/2] 正在生成有声书...")
        cmd = [
            "python", "-m", "markflow.cli.commands", "execute", "VoiceAssistant",
            "action=tts",
            f"text_file={text_file}",
            "voice=zh-CN-XiaoxiaoNeural",
            "chunk_size=10000",
            f"output_file={audio_file}"
        ]

        if not self.run_command(cmd):
            return False

        print(f"   ✅ 有声书：{audio_file}")
        return True

    def run(self, target_chapters: int = None):
        """执行主流程"""
        print("\n" + "=" * 60)
        print("   📖 小说生成器（每日续写）")
        print("=" * 60)
        print()
        print(f"📅 时间：{self.get_today_display()}")
        print()

        # 获取今天的小说文件
        novel_file = self.get_novel_file()
        
        # 如果今天的文件不存在，从旧文件复制
        if novel_file is None or not novel_file.exists():
            # 查找最近的小说文件作为源
            old_files = list(self.novel_dir.glob("novel_zh_*.txt"))
            if old_files:
                source = sorted(old_files)[-1]
                today = self.get_today()
                novel_file = self.novel_dir / f"novel_zh_{today}.txt"
                import shutil
                shutil.copy2(source, novel_file)
                print(f"📂 从 {source} 复制到 {novel_file}")
            else:
                # 首次生成 3 章
                print("📝 首次生成 3 章...")
                cmd = [
                    "python", "-m", "markflow.cli.commands", "execute", "NovelWriterOllama",
                    "genre=科幻",
                    "title=星际行者",
                    "outline=一个普通少年意外获得星际航行能力，在宇宙中探索未知文明",
                    "characters=主角阿星，16岁，好奇心强；AI助手小智，幽默风趣",
                    "chapter_count=3",
                    "model=qwen2.5:7b",
                    "continue_from="
                ]
                if not self.run_command(cmd):
                    return
                novel_file = self.get_novel_file()
                if novel_file is None:
                    print("❌ 生成失败")
                    return
        
        # 计算目标章节数
        current = self.get_current_chapters(novel_file)
        if target_chapters is None:
            # 默认每天 +3 章
            target_chapters = current + 3
        
        # 续写
        print(f"📖 当前：{current} 章 → 目标：{target_chapters} 章")
        if not self.continue_novel(novel_file, target_chapters):
            return

        # 生成有声书
        self.generate_audiobook(novel_file)

        # 显示最终结果
        final_chapters = self.get_current_chapters(novel_file)
        print("\n" + "=" * 60)
        print("   ✅ 完成！")
        print("=" * 60)
        print()
        print(f"   📖 小说：{novel_file}")
        print(f"   📊 章节：{final_chapters} 章")
        print(f"   🎤 有声书：{self.audio_dir}/novel_zh_{self.get_today()}.mp3")
        print()
    

def main():
    parser = argparse.ArgumentParser(
        description="小说生成器 - 每日续写 + 有声书",
        epilog="示例：python novel_generator.py 6   # 续写到6章"
    )
    parser.add_argument(
        "chapters", 
        nargs="?", 
        type=int, 
        default=None,
        help="目标章节数（默认在当前基础上+3）"
    )
    
    args = parser.parse_args()
    
    generator = NovelGenerator()
    generator.run(args.chapters)


if __name__ == "__main__":
    main()