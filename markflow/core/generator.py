"""
代码生成器 - 从SkillSpec生成可执行代码
"""

from typing import Dict, Any, List, Optional
from .parser import SkillSpec
from .quality import CodeQualityChecker  # 新增导入
import re
import logging

logger = logging.getLogger(__name__)


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self):
        self.templates = {}
        self.quality_checker = CodeQualityChecker()  # 新增

    def generate_tests(self, spec: SkillSpec, code: str) -> str:
        """根据技能规格生成单元测试"""
        class_name = self._generate_class_name(spec.name)
        
        test_lines = []
        test_lines.append('"""')
        test_lines.append(f'{spec.name} 单元测试')
        test_lines.append('"""')
        test_lines.append('')
        test_lines.append('import unittest')
        test_lines.append('import sys')
        test_lines.append('from pathlib import Path')
        test_lines.append('')
        test_lines.append('# 添加项目根目录到路径')
        test_lines.append('sys.path.insert(0, str(Path(__file__).parent.parent))')
        test_lines.append('')
        test_lines.append(f'from skills.{spec.name}.skill import {class_name}')
        test_lines.append('')
        test_lines.append('')
        test_lines.append(f'class Test{class_name}(unittest.TestCase):')
        test_lines.append('    """')
        test_lines.append(f'    {class_name} 测试类')
        test_lines.append('    """')
        test_lines.append('')
        test_lines.append('    def setUp(self):')
        test_lines.append('        """测试前准备"""')
        test_lines.append(f'        self.skill = {class_name}()')
        test_lines.append('')
        
        # 根据输入参数生成测试
        if spec.inputs:
            test_lines.append('    def test_execute_with_valid_params(self):')
            test_lines.append('        """测试正常执行"""')
            
            params = []
            for inp in spec.inputs:
                name = inp.get('name', '')
                default = inp.get('default', '')
                if default:
                    params.append(f'{name}={repr(default)}')
                elif inp.get('required', False):
                    params.append(f'{name}="test_{name}"')
                else:
                    params.append(f'{name}=""')
            
            params_str = ', '.join(params)
            test_lines.append(f'        result = self.skill.execute({params_str})')
            test_lines.append('        self.assertEqual(result.get("status"), "success")')
            test_lines.append('        self.assertIn("result", result)')
            test_lines.append('')
            
            # 必填参数测试
            required = [inp for inp in spec.inputs if inp.get('required', False)]
            if required:
                test_lines.append('    def test_execute_missing_required_params(self):')
                test_lines.append('        """测试缺少必填参数"""')
                for inp in required[:1]:
                    test_lines.append(f'        with self.assertRaises(ValueError):')
                    test_lines.append(f'            self.skill.execute({inp["name"]}="")')
                test_lines.append('')
        
        # 元数据测试
        test_lines.append('    def test_skill_metadata(self):')
        test_lines.append('        """测试技能元数据"""')
        test_lines.append(f'        self.assertEqual(self.skill.name, "{spec.name}")')
        test_lines.append('        self.assertIsInstance(self.skill.version, str)')
        test_lines.append('')
        
        test_lines.append('')
        test_lines.append('if __name__ == "__main__":')
        test_lines.append('    unittest.main()')
        
        return '\n'.join(test_lines)
        
    def generate(self, spec: SkillSpec, quality_check: bool = True, 
                 format_code: bool = True, generate_tests: bool = True) -> Dict[str, Any]:
        """生成技能代码"""
        from .tracer import RequirementTracer  # 新增导入
        
        class_name = self._generate_class_name(spec.name)
        code = self._generate_class_code(spec, class_name)
        
        # 质量检查
        quality_result = None
        if quality_check:
            logger.info("执行代码质量检查...")
            quality_result = self.quality_checker.validate_all(code, "python")
            if quality_result.get("score", 0) < 60:
                logger.warning(f"质量评分较低: {quality_result['score']}/100")
            else:
                logger.info(f"质量评分: {quality_result['score']}/100")
        
        # 格式化
        if format_code:
            logger.info("格式化代码...")
            code = self.quality_checker.format_code(code, "python")
        
        # 生成测试
        tests = ""
        if generate_tests:
            logger.info("生成单元测试...")
            tests = self.generate_tests(spec, code)
        
        # 需求追溯
        tracer = RequirementTracer()
        trace_result = tracer.trace(spec, code)
        
        metadata = self._generate_metadata(spec)
        if quality_result:
            metadata['quality'] = {
                'score': quality_result.get('score', 0),
                'passed': quality_result.get('passed', False),
                'errors_count': len(quality_result.get('errors', [])),
                'warnings_count': len(quality_result.get('warnings', []))
            }
        if trace_result:
            metadata['trace'] = {
                'coverage': trace_result['coverage'],
                'total_requirements': trace_result['total_requirements'],
                'implemented': trace_result['implemented']
            }
        
        stats = self.quality_checker.analyze_code_stats(code, "python")
        
        return {
            'name': spec.name,
            'class_name': class_name,
            'code': code,
            'tests': tests,
            'metadata': metadata,
            'quality': quality_result,
            'stats': stats,
            'trace': trace_result
        }
    
    def _generate_class_name(self, name: str) -> str:
        """生成类名"""
        words = name.replace('-', '_').replace(' ', '_').split('_')
        return ''.join(word.capitalize() for word in words)
    
    def _generate_class_code(self, spec: SkillSpec, class_name: str) -> str:
        """生成类代码"""
        imports = self._generate_imports(spec.dependencies)
        methods = self._generate_methods(spec)
        helper_methods = self._generate_helper_methods(spec)
        
        # 使用字符串拼接而不是format，避免花括号冲突
        code_lines = []
        
        # 文件头
        code_lines.append('"""')
        code_lines.append(f'{spec.name} - {spec.description}')
        code_lines.append('')
        code_lines.append(self._format_docstring(spec))
        code_lines.append('"""')
        code_lines.append('')
        code_lines.append(imports)
        code_lines.append('')
        code_lines.append('import logging')
        code_lines.append('from typing import Dict, Any, Optional, List')
        code_lines.append('from pathlib import Path')
        code_lines.append('from datetime import datetime')
        code_lines.append('import json')
        code_lines.append('')
        code_lines.append('logger = logging.getLogger(__name__)')
        code_lines.append('')
        code_lines.append('')
        code_lines.append(f'class {class_name}:')
        code_lines.append('    """')
        code_lines.append(f'    {spec.description}')
        code_lines.append('    ')
        code_lines.append(f'    {self._format_purpose(spec.purpose)}')
        code_lines.append('    """')
        code_lines.append('    ')
        code_lines.append('    def __init__(self, config: Dict[str, Any] = None):')
        code_lines.append('        """')
        code_lines.append('        初始化技能')
        code_lines.append('        ')
        code_lines.append('        Args:')
        code_lines.append('            config: 配置参数字典')
        code_lines.append('        """')
        code_lines.append('        self.config = config or {}')
        code_lines.append(f'        self.name = "{spec.name}"')
        code_lines.append(f'        self.version = "{spec.version}"')
        code_lines.append('        self._setup_logging()')
        code_lines.append('        self._setup_config()')
        code_lines.append('    ')
        code_lines.append('    def _setup_logging(self):')
        code_lines.append('        """设置日志"""')
        code_lines.append('        log_level = self.config.get(\'log_level\', \'INFO\')')
        code_lines.append('        logging.basicConfig(')
        code_lines.append('            level=getattr(logging, log_level.upper()),')
        code_lines.append('            format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\'')
        code_lines.append('        )')
        code_lines.append('    ')
        code_lines.append('    def _setup_config(self):')
        code_lines.append('        """设置配置"""')
        code_lines.append('        defaults = {}')
        for key, value in spec.config.items():
            if isinstance(value, str):
                code_lines.append(f'        defaults["{key}"] = "{value}"')
            else:
                code_lines.append(f'        defaults["{key}"] = {repr(value)}')
        code_lines.append('        for key, value in defaults.items():')
        code_lines.append('            if key not in self.config:')
        code_lines.append('                self.config[key] = value')
        code_lines.append('    ')
        code_lines.append('    def _validate_inputs(self, **kwargs) -> bool:')
        code_lines.append('        """')
        code_lines.append('        验证输入参数')
        code_lines.append('        ')
        code_lines.append('        Args:')
        code_lines.append('            **kwargs: 输入参数')
        code_lines.append('            ')
        code_lines.append('        Returns:')
        code_lines.append('            验证是否通过')
        code_lines.append('        """')
        
        # 必需的输入参数
        required = [inp['name'] for inp in spec.inputs if inp.get('required', True)]
        if required:
            code_lines.append('        required = [' + ', '.join([f'"{name}"' for name in required]) + ']')
            code_lines.append('        for param in required:')
            code_lines.append('            if param not in kwargs:')
            code_lines.append('                raise ValueError(f"缺少必需参数: {param}")')
        
        code_lines.append('        ')
        code_lines.append('        # 类型验证')
        code_lines.append('        for param, value in kwargs.items():')
        code_lines.append('            # 简单的类型检查')
        code_lines.append('            pass')
        code_lines.append('        ')
        code_lines.append('        return True')
        code_lines.append('    ')
        code_lines.append('    def execute(self, **kwargs) -> Dict[str, Any]:')
        code_lines.append('        """')
        code_lines.append('        执行技能')
        code_lines.append('        ')
        code_lines.append('        Args:')
        code_lines.append('            **kwargs: 输入参数')
        code_lines.append('            ')
        code_lines.append('        Returns:')
        code_lines.append('            执行结果')
        code_lines.append('        """')
        code_lines.append('        logger.info(f"执行技能: {self.name} (v{self.version})")')
        code_lines.append('        ')
        code_lines.append('        try:')
        code_lines.append('            self._validate_inputs(**kwargs)')
        code_lines.append('            ')
        code_lines.append('            result_data = {}')
        
        # 生成步骤代码
        for i, step in enumerate(spec.steps):
            method_name = self._step_to_method_name(step, i)
            code_lines.append(f'            # 步骤{i+1}: {step}')
            code_lines.append(f'            kwargs = self.{method_name}(**kwargs)')
        
        code_lines.append('            result_data = kwargs')
        code_lines.append('            ')
        code_lines.append('            result = {')
        code_lines.append('                "status": "success",')
        code_lines.append('                "result": result_data,')
        code_lines.append('                "metadata": {')
        code_lines.append('                    "skill": self.name,')
        code_lines.append('                    "version": self.version,')
        code_lines.append('                    "executed_at": datetime.now().isoformat()')
        code_lines.append('                }')
        code_lines.append('            }')
        code_lines.append('            ')
        code_lines.append('            logger.info(f"技能执行成功: {self.name}")')
        code_lines.append('            return result')
        code_lines.append('            ')
        code_lines.append('        except Exception as e:')
        code_lines.append('            logger.error(f"技能执行失败: {e}")')
        code_lines.append('            return {')
        code_lines.append('                "status": "error",')
        code_lines.append('                "error": str(e),')
        code_lines.append('                "skill": self.name,')
        code_lines.append('                "timestamp": datetime.now().isoformat()')
        code_lines.append('            }')
        code_lines.append('    ')
        
        # 添加步骤方法
        if methods:
            code_lines.append(methods)
        
        # 添加辅助方法
        if helper_methods:
            code_lines.append(helper_methods)
        
        code_lines.append('    def __repr__(self):')
        code_lines.append(f'        return f"<{class_name}(name={{self.name}}, version={{self.version}})>"')
        
        return '\n'.join(code_lines)
    
    def _generate_imports(self, dependencies: List[str]) -> str:
        """生成导入语句"""
        import_map = {
            'pandas': 'import pandas as pd',
            'numpy': 'import numpy as np',
            'requests': 'import requests',
            'sqlalchemy': 'from sqlalchemy import create_engine',
            'redis': 'import redis',
            'celery': 'from celery import Celery',
            'matplotlib': 'import matplotlib.pyplot as plt',
            'seaborn': 'import seaborn as sns',
            'flask': 'from flask import Flask',
            'fastapi': 'from fastapi import FastAPI',
            'click': 'import click',
            'yaml': 'import yaml',
            'toml': 'import toml',
            'diffusers': '# import diffusers  # 可选依赖',
            'torch': '# import torch  # 可选依赖',
            'transformers': '# import transformers  # 可选依赖',
            'accelerate': '# import accelerate  # 可选依赖',
            'safetensors': '# import safetensors  # 可选依赖',
            'PIL': '# from PIL import Image  # 可选依赖',
        }
        
        imports = []
        for dep in dependencies:
            if dep in import_map:
                imports.append(import_map[dep])
            elif dep:
                imports.append(f'# import {dep}  # 可选依赖')
        
        standard_imports = [
            'import os',
            'import sys',
            'import re',
            'import time',
            'import random',
            'import json'
        ]
        
        all_imports = list(set(imports + standard_imports))
        return '\n'.join(all_imports)
    
    def _generate_methods(self, spec: SkillSpec) -> str:
        """生成方法代码"""
        methods = []
        for i, step in enumerate(spec.steps):
            method_name = self._step_to_method_name(step, i)
            methods.append(self._generate_step_method(method_name, step))
        return '\n\n'.join(methods) if methods else ''
    
    def _step_to_method_name(self, step: str, index: int) -> str:
        """将步骤转换为方法名"""
        verbs = ['load', 'process', 'validate', 'transform', 'analyze', 
                'generate', 'save', 'export', 'import', 'convert', 'check']
        
        step_lower = step.lower()
        for verb in verbs:
            if verb in step_lower:
                parts = step_lower.split(verb, 1)
                if len(parts) > 1:
                    keywords = parts[1].strip()
                    words = re.findall(r'\w+', keywords)
                    if words:
                        return f"_{verb}_{'_'.join(words[:2])}"
                return f"_{verb}_data"
        
        return f"_step_{index + 1}"
    
    def _generate_step_method(self, method_name: str, step: str) -> str:
        """生成步骤方法"""
        return f'''    def {method_name}(self, **kwargs):
        """
        {step}
        """
        logger.info(f"执行步骤: {step}")
        # TODO: 实现具体逻辑
        return kwargs'''
    
    def _generate_helper_methods(self, spec: SkillSpec) -> str:
        """生成辅助方法"""
        helpers = []
        
        if any('读取' in step or 'load' in step.lower() for step in spec.steps):
            helpers.append('''
    def _load_data(self, source: str, **kwargs):
        """加载数据"""
        if source.startswith(('http://', 'https://')):
            import requests
            response = requests.get(source)
            return response.json() if 'json' in response.headers.get('content-type', '') else response.text
        elif source.endswith(('.csv', '.tsv')):
            import pandas as pd
            return pd.read_csv(source)
        elif source.endswith('.json'):
            with open(source, 'r') as f:
                return json.load(f)
        else:
            with open(source, 'r') as f:
                return f.read()
''')
        
        if any('保存' in step or 'save' in step.lower() for step in spec.steps):
            helpers.append('''
    def _save_data(self, data: Any, destination: str, **kwargs):
        """保存数据"""
        if destination.endswith('.json'):
            with open(destination, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif destination.endswith('.csv'):
            import pandas as pd
            if isinstance(data, (list, dict)):
                pd.DataFrame(data).to_csv(destination, index=False)
            else:
                pd.DataFrame([data]).to_csv(destination, index=False)
        else:
            with open(destination, 'w') as f:
                f.write(str(data))
''')
        
        if any('验证' in step or 'validate' in step.lower() for step in spec.steps):
            helpers.append('''
    def _validate_data(self, data: Any, rules: Dict = None, **kwargs) -> bool:
        """验证数据"""
        if data is None:
            return False
        
        if isinstance(data, (list, dict)) and not data:
            return False
        
        return True
''')
        
        helpers.append('''
    def _handle_error(self, error: Exception, context: str = "") -> Dict:
        """处理错误"""
        logger.error(f"{context}: {error}")
        return {{
            "status": "error",
            "error": str(error),
            "context": context
        }}
''')
        
        return '\n'.join(helpers) if helpers else ''
    
    def _format_docstring(self, spec: SkillSpec) -> str:
        """格式化文档字符串"""
        parts = []
        if spec.purpose:
            parts.append(f"目的: {spec.purpose}")
        if spec.inputs:
            parts.append("")
            parts.append("输入参数:")
            for inp in spec.inputs:
                parts.append(f"  - {inp['name']} ({inp.get('type', 'string')}): {inp.get('description', '')}")
        if spec.outputs:
            parts.append("")
            parts.append("输出:")
            for out in spec.outputs:
                parts.append(f"  - {out['name']}: {out.get('description', '')}")
        if spec.steps:
            parts.append("")
            parts.append("执行步骤:")
            for i, step in enumerate(spec.steps, 1):
                parts.append(f"  {i}. {step}")
        return '\n'.join(parts)
    
    def _format_purpose(self, purpose: str) -> str:
        """格式化目的"""
        if purpose:
            return purpose.strip()
        return "执行技能功能"
    
    def _generate_metadata(self, spec: SkillSpec) -> Dict:
        """生成元数据"""
        return {
            "name": spec.name,
            "version": spec.version,
            "description": spec.description,
            "tags": spec.tags,
            "dependencies": spec.dependencies,
            "inputs": spec.inputs,
            "outputs": spec.outputs,
            "config": spec.config
        }