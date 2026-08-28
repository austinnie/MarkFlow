# scripts/review_skill.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
对已有技能进行 AI 代码审查（不重新生成）
用法: python scripts/review_skill.py doc_generator
      python scripts/review_skill.py doc_generator --model qwen2.5:7b
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.core.quality import CodeQualityChecker


def review_skill(skill_name: str, model: str = "qwen2.5:7b"):
    """审查指定技能的代码"""
    
    # 读取 skill.py
    skill_dir = project_root / "skills" / skill_name
    skill_file = skill_dir / "skill.py"
    
    if not skill_file.exists():
        print(f"❌ 技能不存在: {skill_name}")
        print(f"   路径: {skill_file}")
        return False
    
    print(f"📂 技能: {skill_name}")
    print(f"📄 文件: {skill_file}")
    print(f"🤖 模型: {model}")
    print("-" * 50)
    
    # 读取代码
    code = skill_file.read_text(encoding='utf-8')
    print(f"📊 代码行数: {len(code.splitlines())}")
    print("-" * 50)
    
    # 执行 AI 审查
    print("⏳ 正在执行 AI 审查...")
    checker = CodeQualityChecker()
    result = checker.review_code_with_ollama(
        code,
        language="python",
        model=model
    )
    
    # 显示结果
    print("\n" + "=" * 60)
    print("📋 AI 审查结果")
    print("=" * 60)
    
    score = result.get("score", 0)
    if score >= 80:
        icon = "🟢"
    elif score >= 60:
        icon = "🟡"
    else:
        icon = "🔴"
    
    print(f"评分: {icon} {score}/100")
    print()
    
    # 维度
    dimensions = result.get("dimensions", {})
    if dimensions:
        print("📊 维度评分:")
        for name, value in dimensions.items():
            print(f"   {name}: {value}/10")
        print()
    
    # 问题
    issues = result.get("issues", [])
    if issues:
        print(f"🐛 问题 ({len(issues)} 个):")
        for issue in issues:
            print(f"   - {issue}")
        print()
    
    # 建议
    suggestions = result.get("suggestions", [])
    if suggestions:
        print(f"💡 建议 ({len(suggestions)} 个):")
        for suggestion in suggestions:
            print(f"   - {suggestion}")
        print()
    
    # 总结
    summary = result.get("summary", "")
    if summary:
        print(f"📝 总结: {summary}")
    
    print("=" * 60)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="AI 审查已有技能")
    parser.add_argument("skill", help="技能名称 (如 doc_generator)")
    parser.add_argument("--model", "-m", default="qwen2.5:7b", 
                       help="Ollama 模型 (默认: qwen2.5:7b)")
    
    args = parser.parse_args()
    
    review_skill(args.skill, args.model)


if __name__ == "__main__":
    main()