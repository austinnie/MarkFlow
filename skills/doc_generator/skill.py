"""
doc_generator - 代码文档自动生成器，从 Python 代码自动生成 API 文档

目的: 自动化生成项目文档，支持 API 参考、README 和使用指南
"""

import os
import ast
import inspect
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DocGenerator:
    """
    代码文档自动生成器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "doc_generator"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        logger.info("DocGenerator 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'output_dir': './generated_docs',
            'default_doc_type': 'all',
            'default_format': 'md',
            'exclude_patterns': ['__pycache__', '*.pyc', 'test_*', '*_test.py'],
            'include_patterns': ['*.py']
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        if 'code_path' not in kwargs or not kwargs['code_path']:
            raise ValueError("code_path 是必填参数")
        
        code_path = Path(kwargs['code_path'])
        if not code_path.exists():
            raise ValueError(f"代码路径不存在: {code_path}")
        
        doc_type = kwargs.get('doc_type', self.config.get('default_doc_type', 'all'))
        if doc_type not in ['api', 'readme', 'all']:
            raise ValueError(f"doc_type 必须为 api、readme 或 all，当前值: {doc_type}")
        
        output_format = kwargs.get('output_format', self.config.get('default_format', 'md'))
        if output_format not in ['md', 'html']:
            raise ValueError(f"output_format 必须为 md 或 html，当前值: {output_format}")
        
        return True
    
    def _should_include_file(self, file_path: Path) -> bool:
        """检查文件是否应该被包含"""
        # 检查排除模式
        exclude_patterns = self.config.get('exclude_patterns', ['__pycache__', '*.pyc'])
        for pattern in exclude_patterns:
            if file_path.match(pattern):
                return False
        
        # 检查包含模式
        include_patterns = self.config.get('include_patterns', ['*.py'])
        for pattern in include_patterns:
            if file_path.match(pattern):
                return True
        
        return False
    
    def _collect_python_files(self, code_path: Path) -> List[Path]:
        """收集所有 Python 文件"""
        files = []
        if code_path.is_file():
            if code_path.suffix == '.py' and self._should_include_file(code_path):
                files.append(code_path)
        else:
            for root, dirs, files_in_dir in os.walk(code_path):
                # 排除某些目录
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', 'node_modules']]
                for file in files_in_dir:
                    file_path = Path(root) / file
                    if file_path.suffix == '.py' and self._should_include_file(file_path):
                        files.append(file_path)
        return files
    
    def _parse_python_file(self, file_path: Path) -> Dict[str, Any]:
        """解析 Python 文件"""
        result = {
            'file_path': str(file_path),
            'module_name': file_path.stem,
            'docstring': '',
            'imports': [],
            'classes': [],
            'functions': [],
            'constants': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 提取模块 docstring
            module_doc = ast.get_docstring(tree)
            if module_doc:
                result['docstring'] = module_doc
            
            # 解析 AST
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        result['imports'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module
                    for alias in node.names:
                        result['imports'].append(f"{module_name}.{alias.name}" if module_name else alias.name)
                elif isinstance(node, ast.ClassDef):
                    class_info = self._parse_class(node, content)
                    result['classes'].append(class_info)
                elif isinstance(node, ast.FunctionDef):
                    func_info = self._parse_function(node, content)
                    result['functions'].append(func_info)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result['constants'].append({
                                'name': target.id,
                                'value': self._get_constant_value(node.value)
                            })
            
        except Exception as e:
            logger.warning(f"解析文件失败 {file_path}: {e}")
        
        return result
    
    def _parse_class(self, node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """解析类"""
        class_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'bases': [self._get_name(base) for base in node.bases],
            'methods': [],
            'attributes': [],
            'class_variables': []
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._parse_function(item, content)
                class_info['methods'].append(method_info)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_info['class_variables'].append({
                            'name': target.id,
                            'value': self._get_constant_value(item.value)
                        })
        
        return class_info
    
    def _parse_function(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """解析函数"""
        func_info = {
            'name': node.name,
            'docstring': ast.get_docstring(node) or '',
            'params': [],
            'return_type': '',
            'decorators': [],
            'line_number': node.lineno,
            'is_async': isinstance(node, ast.AsyncFunctionDef)
        }
        
        # 解析参数
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': self._get_annotation(arg.annotation) if arg.annotation else 'Any',
                'default': None
            }
            func_info['params'].append(param_info)
        
        # 解析默认参数
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                param_index = len(func_info['params']) - len(defaults) + i
                if param_index < len(func_info['params']):
                    func_info['params'][param_index]['default'] = self._get_constant_value(default)
        
        # 解析返回类型
        if node.returns:
            func_info['return_type'] = self._get_annotation(node.returns)
        
        # 解析装饰器
        for decorator in node.decorator_list:
            decorator_name = self._get_name(decorator)
            if decorator_name:
                func_info['decorators'].append(decorator_name)
        
        return func_info
    
    def _get_name(self, node) -> str:
        """获取 AST 节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return self._get_name(node.value)
        elif hasattr(node, 'id'):
            return node.id
        return str(node)[:50]
    
    def _get_annotation(self, node) -> str:
        """获取类型注解字符串"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[...]"
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        return str(node)[:50]
    
    def _get_constant_value(self, node) -> Any:
        """获取常量值"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.List):
            return [self._get_constant_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Dict):
            return {self._get_constant_value(k): self._get_constant_value(v) for k, v in zip(node.keys, node.values)}
        elif isinstance(node, ast.Tuple):
            return tuple(self._get_constant_value(elt) for elt in node.elts)
        return str(node)[:50]
    
    def _generate_api_doc_md(self, parsed_files: List[Dict], project_name: str, project_description: str) -> str:
        """生成 API 参考文档（Markdown 格式）"""
        lines = []
        
        # 标题
        lines.append(f"# {project_name} API 参考")
        lines.append("")
        lines.append(f"*{project_description}*")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 按模块分组
        for file_info in parsed_files:
            module_name = file_info['module_name']
            file_path = file_info['file_path']
            
            lines.append(f"## 模块: {module_name}")
            lines.append("")
            lines.append(f"**文件**: `{file_path}`")
            lines.append("")
            
            if file_info['docstring']:
                lines.append(file_info['docstring'])
                lines.append("")
            
            # 导入信息
            if file_info['imports']:
                lines.append("### 导入")
                lines.append("")
                for imp in file_info['imports'][:10]:
                    lines.append(f"- `{imp}`")
                if len(file_info['imports']) > 10:
                    lines.append(f"- ... 还有 {len(file_info['imports']) - 10} 个导入")
                lines.append("")
            
            # 类
            if file_info['classes']:
                lines.append("### 类")
                lines.append("")
                for cls in file_info['classes']:
                    lines.append(f"#### `{cls['name']}`")
                    lines.append("")
                    if cls['bases']:
                        lines.append(f"- **基类**: {', '.join(cls['bases'])}")
                        lines.append("")
                    if cls['docstring']:
                        lines.append(f"- **说明**: {cls['docstring']}")
                        lines.append("")
                    
                    # 类变量
                    if cls['class_variables']:
                        lines.append("**类变量**:")
                        lines.append("")
                        for var in cls['class_variables']:
                            lines.append(f"- `{var['name']}` = `{var['value']}`")
                        lines.append("")
                    
                    # 方法
                    if cls['methods']:
                        lines.append("**方法**:")
                        lines.append("")
                        for method in cls['methods']:
                            params_str = ', '.join([f"{p['name']}: {p['type']}" + (f" = {p['default']}" if p.get('default') is not None else '') for p in method['params']])
                            lines.append(f"- `{method['name']}({params_str})` -> `{method['return_type']}`")
                            if method['docstring']:
                                lines.append(f"  - {method['docstring'][:100]}")
                            if method['decorators']:
                                lines.append(f"  - @{', @'.join(method['decorators'])}")
                        lines.append("")
            
            # 函数
            if file_info['functions']:
                lines.append("### 函数")
                lines.append("")
                for func in file_info['functions']:
                    params_str = ', '.join([f"{p['name']}: {p['type']}" + (f" = {p['default']}" if p.get('default') is not None else '') for p in func['params']])
                    lines.append(f"- `{func['name']}({params_str})` -> `{func['return_type']}`")
                    if func['docstring']:
                        lines.append(f"  - {func['docstring'][:100]}")
                lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_readme_md(self, parsed_files: List[Dict], project_name: str, 
                           project_description: str, author: str) -> str:
        """生成 README 文档"""
        lines = []
        
        # 标题
        lines.append(f"# {project_name}")
        lines.append("")
        lines.append(f"> {project_description}")
        lines.append("")
        
        # 作者
        if author:
            lines.append(f"**作者**: {author}")
            lines.append("")
        
        # 概览
        total_classes = sum(len(f['classes']) for f in parsed_files)
        total_functions = sum(len(f['functions']) for f in parsed_files)
        
        lines.append("## 📊 概览")
        lines.append("")
        lines.append(f"- **文件数**: {len(parsed_files)}")
        lines.append(f"- **类数**: {total_classes}")
        lines.append(f"- **函数数**: {total_functions}")
        lines.append("")
        
        # 模块列表
        lines.append("## 📁 模块列表")
        lines.append("")
        lines.append("| 模块 | 类数 | 函数数 |")
        lines.append("|------|------|--------|")
        for file_info in parsed_files:
            lines.append(f"| `{file_info['module_name']}` | {len(file_info['classes'])} | {len(file_info['functions'])} |")
        lines.append("")
        
        # 快速开始
        lines.append("## 🚀 快速开始")
        lines.append("")
        lines.append("```python")
        lines.append(f"from {parsed_files[0]['module_name'] if parsed_files else 'your_module'} import *")
        lines.append("")
        lines.append("# 使用示例")
        lines.append("...")
        lines.append("```")
        lines.append("")
        
        # 安装
        lines.append("## 📦 安装")
        lines.append("")
        lines.append("```bash")
        lines.append("pip install -e .")
        lines.append("```")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append(f"*文档自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return '\n'.join(lines)
    
    def _generate_usage_examples(self, parsed_files: List[Dict], project_name: str) -> str:
        """生成使用示例"""
        lines = []
        
        lines.append(f"# {project_name} 使用示例")
        lines.append("")
        lines.append("以下是从代码中提取的使用示例：")
        lines.append("")
        
        for file_info in parsed_files:
            module_name = file_info['module_name']
            lines.append(f"## {module_name}")
            lines.append("")
            
            for cls in file_info['classes']:
                lines.append(f"### {cls['name']}")
                lines.append("")
                
                # 查找 __init__ 方法
                init_method = None
                for method in cls['methods']:
                    if method['name'] == '__init__':
                        init_method = method
                        break
                
                if init_method:
                    params = [p for p in init_method['params'] if p['name'] != 'self']
                    if params:
                        param_str = ', '.join([f"{p['name']}={repr(p['default'])}" if p.get('default') is not None else p['name'] for p in params])
                        lines.append("```python")
                        lines.append(f"# 创建实例")
                        lines.append(f"obj = {cls['name']}({param_str})")
                        lines.append("```")
                        lines.append("")
                
                # 其他方法
                methods = [m for m in cls['methods'] if m['name'] not in ['__init__', '__repr__']]
                if methods:
                    lines.append("```python")
                    for method in methods[:3]:
                        params = [p for p in method['params'] if p['name'] != 'self']
                        param_str = ', '.join([f"{p['name']}={repr(p['default'])}" if p.get('default') is not None else p['name'] for p in params])
                        if param_str:
                            lines.append(f"result = obj.{method['name']}({param_str})")
                        else:
                            lines.append(f"result = obj.{method['name']}()")
                        if method['docstring']:
                            lines.append(f"# {method['docstring'][:60]}")
                    lines.append("```")
                lines.append("")
        
        return '\n'.join(lines)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行文档生成"""
        start_time = datetime.now()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            code_path = Path(kwargs.get('code_path'))
            doc_type = kwargs.get('doc_type', self.config.get('default_doc_type', 'all'))
            output_format = kwargs.get('output_format', self.config.get('default_format', 'md'))
            project_name = kwargs.get('project_name', code_path.name)
            project_description = kwargs.get('project_description', '')
            author = kwargs.get('author', '')
            include_tests = kwargs.get('include_tests', False)
            extract_classes = kwargs.get('extract_classes', True)
            extract_functions = kwargs.get('extract_functions', True)
            generate_examples = kwargs.get('generate_examples', True)
            
            output_dir = Path(self.config.get('output_dir', './generated_docs'))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"扫描代码目录: {code_path}")
            files = self._collect_python_files(code_path)
            
            if not files:
                return {
                    "status": "error",
                    "error": f"未找到任何 Python 文件: {code_path}"
                }
            
            logger.info(f"找到 {len(files)} 个 Python 文件")
            
            parsed_files = []
            for file_path in files:
                logger.info(f"  解析: {file_path}")
                parsed = self._parse_python_file(file_path)
                parsed_files.append(parsed)
            
            # 生成文档
            results = {}
            saved_paths = []
            
            if doc_type in ['api', 'all']:
                api_doc = self._generate_api_doc_md(parsed_files, project_name, project_description)
                api_path = output_dir / f"{project_name}_api_reference.{output_format}"
                with open(api_path, 'w', encoding='utf-8') as f:
                    f.write(api_doc)
                saved_paths.append(str(api_path))
                results['api_reference'] = api_doc
            
            if doc_type in ['readme', 'all']:
                readme_doc = self._generate_readme_md(parsed_files, project_name, project_description, author)
                readme_path = output_dir / f"README.{output_format}"
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_doc)
                saved_paths.append(str(readme_path))
                results['readme'] = readme_doc
            
            if generate_examples:
                examples_doc = self._generate_usage_examples(parsed_files, project_name)
                examples_path = output_dir / f"{project_name}_examples.md"
                with open(examples_path, 'w', encoding='utf-8') as f:
                    f.write(examples_doc)
                saved_paths.append(str(examples_path))
                results['usage_examples'] = examples_doc
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ 文档生成完成! 保存位置: {output_dir}")
            logger.info(f"  耗时: {generation_time:.2f}s")
            
            return {
                "status": "success",
                "result": {
                    "doc_path": str(output_dir),
                    "saved_files": saved_paths,
                    "api_reference": results.get('api_reference', ''),
                    "readme": results.get('readme', ''),
                    "usage_examples": results.get('usage_examples', ''),
                    "modules_summary": {
                        "total_files": len(parsed_files),
                        "total_classes": sum(len(f['classes']) for f in parsed_files),
                        "total_functions": sum(len(f['functions']) for f in parsed_files)
                    },
                    "generated_at": datetime.now().isoformat(),
                    "generation_time": f"{generation_time:.2f}s"
                },
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def __repr__(self):
        return f"<DocGenerator(name={self.name}, version={self.version})>"