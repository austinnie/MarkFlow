#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说生成器 - 定时自动执行版
用法：python novel_scheduler.py
"""

import time
import schedule
import subprocess
from datetime import datetime
from pathlib import Path


class NovelScheduler:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)

    def log(self, message):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        print(log_line.strip())
        
        log_file = self.log_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def run_daily(self):
        """每日执行任务"""
        self.log("=" * 50)
        self.log("📖 开始执行每日小说生成任务")
        
        try:
            # ✅ 直接调用 novel_generator.py 脚本
            cmd = ["python", str(self.base_dir / "scripts" / "novel_generator.py"), "3"]
            result = subprocess.run(
                cmd, 
                text=True, 
                encoding='utf-8', 
                errors='replace',
                cwd=self.base_dir
            )
            
            if result.returncode == 0:
                self.log("✅ 任务执行成功")
            else:
                self.log(f"❌ 任务执行失败，返回码: {result.returncode}")
        except Exception as e:
            self.log(f"❌ 异常: {e}")
        
        self.log("=" * 50)

    def run_now(self):
        """立即执行一次"""
        self.log("🚀 手动触发执行")
        self.run_daily()

    def start_schedule(self, time_str="23:00"):
        """启动定时任务"""
        schedule.every().day.at(time_str).do(self.run_daily)
        
        self.log(f"⏰ 定时任务已启动，每天 {time_str} 执行")
        self.log("💡 按 Ctrl+C 停止")
        
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    import sys
    scheduler = NovelScheduler()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        scheduler.run_now()
    else:
        scheduler.start_schedule()


if __name__ == "__main__":
    main()