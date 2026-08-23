# scripts/diagnose_params.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 模拟 generate_all_girls.py 的调用方式
from markflow.cli.commands import execute_skill

# 测试一个简单的调用
print("测试1: 直接传递参数")
execute_skill("sd_image_generator", prompt="test prompt")

print("\n测试2: 传递多个参数")
execute_skill("sd_image_generator", 
              prompt="test prompt",
              negative_prompt="bad",
              steps=20)