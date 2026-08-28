# markflow/core/executor.py
"""
技能执行器 - 执行和管理技能
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from .registry import SkillRegistry
from .generator import CodeGenerator
from .parser import MarkdownParser, SkillSpec

logger = logging.getLogger(__name__)


class SkillExecutor:
    """技能执行器"""
    
    def __init__(self, registry: SkillRegistry = None):
        self.registry = registry or SkillRegistry()
        self.parser = MarkdownParser()
        self.generator = CodeGenerator()
    
    def execute(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill_name: 技能名称
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        try:
            instance = self.registry.get_instance(skill_name)
            return instance.execute(**kwargs)
        except Exception as e:
            logger.error(f"执行技能失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": skill_name
            }
    
    def execute_from_markdown(self, markdown_content: str, **kwargs) -> Dict[str, Any]:
        """
        从Markdown执行技能
        
        Args:
            markdown_content: Markdown内容
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        # 解析Markdown
        spec = self.parser.parse(markdown_content)
        
        # 生成代码
        result = self.generator.generate(spec)
        
        # 注册技能
        self._register_generated_skill(result)
        
        # 执行技能
        return self.execute(result['class_name'], **kwargs)
    
    def build_from_markdown(self, markdown_content: str, save: bool = True, 
                            quality_check: bool = True, format_code: bool = True) -> Dict[str, Any]:
        """
        从Markdown构建技能
        
        Args:
            markdown_content: Markdown内容
            save: 是否保存到文件
            quality_check: 是否执行质量检查
            format_code: 是否格式化代码
        """
        spec = self.parser.parse(markdown_content)
        result = self.generator.generate(spec, quality_check=quality_check, format_code=format_code)
        
        self._register_generated_skill(result)
        
        if save:
            # 保存到技能目录（新格式）
            skill_name = result['class_name'].lower()
            skill_dir = self.registry.storage_dir / skill_name
            skill_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存 skill.py
            skill_file = skill_dir / "skill.py"
            with open(skill_file, 'w', encoding='utf-8') as f:
                f.write(result['code'])
            
            # 保存 meta.json（包含质量信息）
            metadata = result['metadata']
            if result.get('quality'):
                metadata['quality'] = result['quality']
            if result.get('stats'):
                metadata['stats'] = result['stats']
            
            meta_file = skill_dir / "meta.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"技能已保存: {skill_dir}")
        
        return result
    
    def build_from_file(self, markdown_path: Path, save: bool = True) -> Dict[str, Any]:
        """
        从Markdown文件构建技能
        
        Args:
            markdown_path: Markdown文件路径
            save: 是否保存到文件
            
        Returns:
            构建结果
        """
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.build_from_markdown(content, save)
    
    def _register_generated_skill(self, result: Dict[str, Any]):
        """注册生成的技能"""
        # 动态执行代码创建类
        namespace = {}
        exec(result['code'], namespace)
        skill_class = namespace.get(result['class_name'])
        
        if skill_class:
            self.registry.register(skill_class, result['metadata'])
        else:
            raise ValueError(f"生成技能类失败: {result['class_name']}")
    
    def list_skills(self) -> Dict[str, Dict]:
        """列出所有技能"""
        return self.registry.list()
    
    def get_skill_info(self, skill_name: str) -> Dict:
        """获取技能信息"""
        if skill_name in self.registry._metadata:
            return self.registry._metadata[skill_name]
        return {}
    
    def reload_skill(self, skill_name: str) -> bool:
        """重新加载技能"""
        # 注销
        self.registry.unregister(skill_name)
        
        # 从文件重新加载
        code_file = self.registry.storage_dir / f"{skill_name}.py"
        if code_file.exists():
            skill_class = self.registry.load_from_file(code_file)
            return skill_class is not None
        
        return False