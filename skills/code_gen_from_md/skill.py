"""
code_gen_from_md - 从 Markdown 文档生成代码（带质量保证）

质量保证策略：
  1. 提示词工程 - 引导模型生成高质量代码
  2. 代码校验 - 语法检查、结构检查
  3. 代码优化 - 自动格式化、优化建议
  4. 单元测试生成 - 自动生成测试用例
  5. 代码审查 - 模拟代码审查
"""

import os
import re
import json
import logging
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import ast
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False

try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False

try:
    import pylint
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False


class CodeGenFromMD:

    QUALITY_CHECKS = {
        "python": {
            "syntax": True,
            "imports": True,
            "docstrings": True,
            "type_hints": True,
            "naming": True,
            "complexity": True,
        },
        "javascript": {
            "syntax": True,
            "imports": True,
            "docstrings": True,
            "naming": True,
        },
        "java": {
            "syntax": True,
            "imports": True,
            "docstrings": True,
            "naming": True,
        },
    }

    REVIEW_DIMENSIONS = [
        "功能完整性",
        "代码可读性",
        "性能效率",
        "安全性",
        "可维护性",
        "测试覆盖",
        "错误处理",
        "文档完整",
    ]

    SUPPORTED_LANGUAGES = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "go": ".go",
        "rust": ".rs",
        "cpp": ".cpp",
        "c": ".c",
        "html": ".html",
        "css": ".css",
        "bash": ".sh",
        "sql": ".sql",
        "json": ".json",
        "yaml": ".yml",
        "toml": ".toml",
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "code_gen_from_md"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        logger.info("CodeGenFromMD 初始化完成")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/code_gen_from_md/output",
            "ollama_url": "http://localhost:11434",
            "model": "qwen2.5:7b",
            "temperature": 0.3,
            "quality_threshold": 0.7,
            "auto_fix": True,
            "generate_tests": True,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
        
    def _call_ollama(self, prompt: str, temperature: float = 0.3) -> str:
        url = f"{self.config.get('ollama_url')}/api/generate"
        model = self.config.get("model", "qwen2.5:7b")

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096,  # ✅ 减少到 4096，生成更快
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=600)  # ✅ 增加到 600 秒
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama 调用失败: {e}")
            return ""
        
    def parse_markdown(self, md_content: str) -> Dict:
        result = {
            "title": "",
            "description": "",
            "language": "python",
            "requirements": [],
            "code_blocks": [],
            "full_content": md_content,
        }

        lines = md_content.split("\n")
        current_section = None
        description_lines = []

        for line in lines:
            line = line.strip()

            if line.startswith("# "):
                result["title"] = line[2:].strip()
                continue

            if line.startswith("## "):
                section = line[3:].strip().lower()
                if "语言" in section or "language" in section:
                    current_section = "language"
                elif "需求" in section or "requirements" in section:
                    current_section = "requirements"
                elif "代码" in section or "code" in section:
                    current_section = "code"
                else:
                    current_section = "description"
                continue

            if line.startswith("### "):
                req = line[4:].strip()
                if req:
                    result["requirements"].append(req)
                continue

            if current_section == "language" and line:
                lang = line.lower().strip()
                if lang in self.SUPPORTED_LANGUAGES:
                    result["language"] = lang

            if current_section == "description" and line and not line.startswith("#"):
                description_lines.append(line)

        result["description"] = "\n".join(description_lines)

        code_pattern = r'```(\w+)\n(.*?)```'
        matches = re.findall(code_pattern, md_content, re.DOTALL)
        for lang, code in matches:
            result["code_blocks"].append({
                "language": lang,
                "code": code.strip()
            })

        return result

    def _build_quality_prompt(self, parsed: Dict) -> str:
        title = parsed.get("title", "未命名项目")
        description = parsed.get("description", "")
        language = parsed.get("language", "python")
        requirements = parsed.get("requirements", [])

        req_text = "\n".join([f"- {r}" for r in requirements]) if requirements else "无特定需求"

        # ✅ 简化提示词，直接要求生成完整代码
        prompt = f"""请根据以下需求生成完整的 {language} 代码。

    项目：{title}
    描述：{description}
    需求：
    {req_text}

    要求：
    1. 生成完整可运行的代码
    2. 包含必要的 import
    3. 添加中文注释
    4. 代码结构清晰

    请直接输出完整代码："""

        return prompt
    
    def _validate_python_syntax(self, code: str) -> Tuple[bool, str]:
        if not AST_AVAILABLE:
            return True, "AST 模块不可用，跳过语法检查"

        try:
            ast.parse(code)
            return True, "语法检查通过"
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        except Exception as e:
            return False, f"检查失败: {e}"

    def _validate_imports(self, code: str, language: str) -> Tuple[bool, str]:
        if language != "python":
            return True, "非 Python 语言，跳过导入检查"

        import_pattern = r'^(?:from|import)\s+\S+'
        imports = re.findall(import_pattern, code, re.MULTILINE)

        if not imports:
            return False, "没有检测到 import 语句，代码可能不完整"

        return True, f"检测到 {len(imports)} 个导入语句"

    def _validate_docstrings(self, code: str, language: str) -> Tuple[bool, str]:
        if language != "python":
            return True, "非 Python 语言，跳过文档检查"

        func_pattern = r'def\s+\w+\s*\([^)]*\)\s*->?[^:]*:\s*\n\s*"""[^"]*"""'
        funcs_with_doc = re.findall(func_pattern, code, re.DOTALL)
        funcs_total = len(re.findall(r'def\s+\w+\s*\(', code))

        if funcs_total > 0 and len(funcs_with_doc) < funcs_total:
            return False, f"有 {funcs_total - len(funcs_with_doc)} 个函数缺少 docstring"

        return True, "文档字符串检查通过"

    def _validate_naming(self, code: str, language: str) -> Tuple[bool, str]:
        if language != "python":
            return True, "非 Python 语言，跳过命名检查"

        class_pattern = r'class\s+([a-z][a-zA-Z0-9_]*)'
        invalid_classes = re.findall(class_pattern, code)

        if invalid_classes:
            return False, f"类名不符合 PascalCase: {', '.join(invalid_classes[:3])}"

        func_pattern = r'def\s+([A-Z][a-zA-Z0-9_]*)'
        invalid_funcs = re.findall(func_pattern, code)

        if invalid_funcs:
            return False, f"函数名不符合 snake_case: {', '.join(invalid_funcs[:3])}"

        return True, "命名检查通过"

    def validate_code(self, code: str, language: str) -> Dict:
        results = {
            "passed": True,
            "checks": [],
            "errors": [],
            "warnings": [],
        }

        checks = {
            "syntax": self._validate_python_syntax if language == "python" else None,
            "imports": lambda c, l: self._validate_imports(c, l),
            "docstrings": lambda c, l: self._validate_docstrings(c, l),
            "naming": lambda c, l: self._validate_naming(c, l),
        }

        for name, func in checks.items():
            if func is None:
                continue

            try:
                passed, message = func(code, language)
                if passed:
                    results["checks"].append({"name": name, "status": "pass", "message": message})
                else:
                    results["warnings" if name == "docstrings" else "errors"].append(
                        {"name": name, "message": message}
                    )
                    if name != "docstrings":
                        results["passed"] = False
            except Exception as e:
                results["checks"].append({"name": name, "status": "error", "message": str(e)})

        return results

    def _optimize_with_ollama(self, code: str, language: str) -> str:
        prompt_lines = [
            f"请优化以下 {language} 代码，提高质量：",
            "",
            "优化要求：",
            "1. 改进代码结构",
            "2. 添加缺失的文档字符串",
            "3. 完善错误处理",
            "4. 提高代码可读性",
            "5. 添加类型注解（如果是 Python）",
            "",
            "代码：",
            "```" + language,
            code,
            "```",
            "",
            "请直接输出优化后的代码，不要其他解释："
        ]

        prompt = "\n".join(prompt_lines)
        optimized = self._call_ollama(prompt)
        return optimized if optimized else code

    def _format_code(self, code: str, language: str) -> str:
        if language == "python" and BLACK_AVAILABLE:
            try:
                import black
                mode = black.Mode()
                return black.format_str(code, mode=mode)
            except Exception as e:
                logger.warning(f"Black 格式化失败: {e}")
                return code
        return code

    def _add_tests(self, code: str, language: str) -> str:
        if language != "python":
            return code

        prompt_lines = [
            f"请为以下 Python 代码生成单元测试（使用 unittest 或 pytest）：",
            "",
            "代码：",
            "```python",
            code,
            "```",
            "",
            "要求：",
            "1. 覆盖主要功能",
            "2. 包含边界测试",
            "3. 使用 assert 断言",
            "4. 测试命名清晰",
            "",
            "请直接输出测试代码："
        ]

        prompt = "\n".join(prompt_lines)
        test_code = self._call_ollama(prompt)
        if test_code:
            return code + "\n\n\n# ==================== 单元测试 ====================\n\n" + test_code
        return code

    def _review_code(self, code: str, language: str) -> Dict:
        prompt_lines = [
            f"请对以下 {language} 代码进行代码审查：",
            "",
            "代码：",
            "```" + language,
            code,
            "```",
            "",
            "请从以下维度审查：",
            "1. 功能完整性",
            "2. 代码可读性",
            "3. 性能效率",
            "4. 安全性",
            "5. 可维护性",
            "6. 错误处理",
            "7. 文档完整",
            "",
            '请输出 JSON 格式的审查结果：',
            '{',
            '    "score": 0-100,',
            '    "dimensions": {"维度名": 0-10},',
            '    "issues": ["问题1", "问题2"],',
            '    "suggestions": ["建议1", "建议2"],',
            '    "summary": "总结"',
            '}'
        ]

        prompt = "\n".join(prompt_lines)
        review_text = self._call_ollama(prompt)

        try:
            review = json.loads(review_text)
        except:
            score_match = re.search(r'"score":\s*(\d+)', review_text)
            score = int(score_match.group(1)) if score_match else 0

            review = {
                "score": score,
                "dimensions": {},
                "issues": [],
                "suggestions": [],
                "summary": review_text[:200] + "..." if len(review_text) > 200 else review_text,
            }

        return review

    def generate_code_with_quality(self, parsed: Dict) -> Dict:
        result = {
            "code": "",
            "quality_score": 0,
            "validations": {},
            "review": {},
            "tests": "",
            "optimized": False,
        }

        prompt = self._build_quality_prompt(parsed)
        code = self._call_ollama(prompt)

        code = re.sub(r'^```\w*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n```$', '', code, flags=re.MULTILINE)

        result["code"] = code

        validation = self.validate_code(code, parsed["language"])
        result["validations"] = validation

        if not validation["passed"] and self.config.get("auto_fix", True):
            logger.info("代码校验失败，尝试自动修复...")
            optimized = self._optimize_with_ollama(code, parsed["language"])
            if optimized and optimized != code:
                code = optimized
                result["code"] = code
                result["optimized"] = True
                validation = self.validate_code(code, parsed["language"])
                result["validations"] = validation

        formatted = self._format_code(code, parsed["language"])
        if formatted != code:
            code = formatted
            result["code"] = code

        if self.config.get("generate_tests", True):
            logger.info("生成单元测试...")
            test_code = self._add_tests(code, parsed["language"])
            if test_code:
                result["tests"] = test_code
                result["code"] = test_code

        logger.info("执行代码审查...")
        review = self._review_code(code, parsed["language"])
        result["review"] = review
        result["quality_score"] = review.get("score", 0)

        return result

    def save_code(self, code: str, language: str, title: str, quality_result: Dict) -> List[str]:
        output_dir = Path(self.config["output_dir"])
        ext = self.SUPPORTED_LANGUAGES.get(language, ".txt")

        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        saved_files = []

        code_file = output_dir / f"{safe_title}_{timestamp}{ext}"
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        saved_files.append(str(code_file))
        logger.info(f"代码已保存: {code_file}")

        report = {
            "file": str(code_file),
            "language": language,
            "timestamp": datetime.now().isoformat(),
            "quality_score": quality_result.get("quality_score", 0),
            "validations": quality_result.get("validations", {}),
            "review": quality_result.get("review", {}),
            "optimized": quality_result.get("optimized", False),
            "has_tests": bool(quality_result.get("tests")),
        }

        report_file = output_dir / f"{safe_title}_{timestamp}_quality.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        saved_files.append(str(report_file))
        logger.info(f"质量报告已保存: {report_file}")

        return saved_files


    def _execute_step_by_step(self, parsed: Dict) -> Dict[str, Any]:
        """分步生成代码（适合复杂需求）"""
        requirements = parsed.get("requirements", [])
        language = parsed.get("language", "python")
        title = parsed.get("title", "未命名项目")

        all_code = []
        saved_files = []

        for i, req in enumerate(requirements):
            logger.info(f"生成第 {i+1}/{len(requirements)} 个功能: {req}")

            prompt = f"""请根据以下需求生成 {language} 代码片段：

    需求：{req}
    项目：{title}
    语言：{language}

    要求：
    1. 代码完整可运行
    2. 包含必要的 import
    3. 添加注释

    请直接输出代码："""

            code = self._call_ollama(prompt)
            if code:
                code = re.sub(r'^```\w*\n', '', code, flags=re.MULTILINE)
                code = re.sub(r'\n```$', '', code, flags=re.MULTILINE)
                all_code.append(f"# ==================== {req} ====================\n{code}")

        # 合并所有代码
        full_code = "\n\n".join(all_code)

        # 添加主入口
        if language == "python":
            full_code += "\n\n\nif __name__ == '__main__':\n    pass"

        # 保存
        output_dir = Path(self.config["output_dir"])
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title.replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self.SUPPORTED_LANGUAGES.get(language, ".txt")

        code_file = output_dir / f"{safe_title}_{timestamp}{ext}"
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(full_code)
        saved_files.append(str(code_file))
        logger.info(f"代码已保存: {code_file}")

        return {
            "status": "success",
            "result": {
                "title": title,
                "language": language,
                "saved_files": saved_files,
                "total_requirements": len(requirements),
                "generated_at": datetime.now().isoformat(),
            },
            "metadata": {
                "skill": self.name,
                "version": self.version,
            }
        }
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            md_file = kwargs.get("md_file", "")
            md_content = kwargs.get("md_content", "")
            mode = kwargs.get("mode", "full")  # full 或 step

            if md_file:
                filepath = Path(md_file)
                if not filepath.exists():
                    return {"status": "error", "error": f"文件不存在: {md_file}"}
                with open(filepath, 'r', encoding='utf-8') as f:
                    md_content = f.read()

            if not md_content:
                return {"status": "error", "error": "请提供 md_file 或 md_content 参数"}

            parsed = self.parse_markdown(md_content)
            logger.info(f"解析完成: {parsed['title']} ({parsed['language']})")

            # ✅ 分步生成模式
            if mode == "step":
                return self._execute_step_by_step(parsed)

            quality_result = self.generate_code_with_quality(parsed)
            saved_files = self.save_code(
                quality_result["code"],
                parsed["language"],
                parsed["title"],
                quality_result
            )

            return {
                "status": "success",
                "result": {
                    "title": parsed["title"],
                    "language": parsed["language"],
                    "saved_files": saved_files,
                    "quality_score": quality_result.get("quality_score", 0),
                    "generated_at": datetime.now().isoformat(),
                },
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
            }
        
    def __repr__(self):
        return f"<CodeGenFromMD(name={self.name}, version={self.version})>"