# markflow/core/registry.py
"""
技能注册中心 - 管理和注册技能
"""

from typing import Dict, Type, Any, Optional, List  # 添加 List 和 Type
from pathlib import Path
import importlib
import importlib.util
import json
import logging

logger = logging.getLogger(__name__)


class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self, storage_dir: Path = None):
        self._skills: Dict[str, Type] = {}
        self._metadata: Dict[str, Dict] = {}
        self._instances: Dict[str, Any] = {}
        self.storage_dir = storage_dir or Path("./skills")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def register(self, skill_class: Type, metadata: Dict = None) -> None:
        """
        注册技能
        
        Args:
            skill_class: 技能类
            metadata: 技能元数据
        """
        name = skill_class.__name__
        self._skills[name] = skill_class
        
        if metadata:
            self._metadata[name] = metadata
        elif hasattr(skill_class, '__metadata__'):
            self._metadata[name] = skill_class.__metadata__
        else:
            self._metadata[name] = {
                "name": name,
                "description": skill_class.__doc__ or f"{name} skill"
            }
        
        logger.info(f"注册技能: {name}")
    
    def unregister(self, name: str) -> bool:
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
            if name in self._metadata:
                del self._metadata[name]
            if name in self._instances:
                del self._instances[name]
            logger.info(f"注销技能: {name}")
            return True
        return False
    
    def get(self, name: str) -> Type:
        """获取技能类"""
        if name not in self._skills:
            raise KeyError(f"技能未注册: {name}")
        return self._skills[name]
    
    def create_instance(self, name: str, config: Dict = None) -> Any:
        """
        创建技能实例
        
        Args:
            name: 技能名称
            config: 配置参数
            
        Returns:
            技能实例
        """
        skill_class = self.get(name)
        instance = skill_class(config or {})
        self._instances[name] = instance
        return instance
    
    def get_instance(self, name: str, config: Dict = None) -> Any:
        """
        获取或创建技能实例
        
        Args:
            name: 技能名称
            config: 配置参数
            
        Returns:
            技能实例
        """
        if name in self._instances:
            return self._instances[name]
        return self.create_instance(name, config)
    
    def list(self) -> Dict[str, Dict]:
        """列出所有已注册的技能"""
        return {
            name: self._metadata.get(name, {})
            for name in self._skills.keys()
        }
    
    def has(self, name: str) -> bool:
        """检查技能是否已注册"""
        return name in self._skills
    
    def load_from_file(self, file_path: Path) -> Optional[Type]:
        """
        从文件加载技能
        
        Args:
            file_path: 技能文件路径
            
        Returns:
            加载的技能类
        """
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找技能类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    attr.__module__ == module.__name__ and
                    attr_name != 'SkillSpec'):
                    # 检查是否有execute方法
                    if hasattr(attr, 'execute') and callable(getattr(attr, 'execute')):
                        self.register(attr)
                        return attr
            
            logger.warning(f"未找到技能类: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"加载技能失败 {file_path}: {e}")
            return None
    
    def load_from_directory(self, directory: Path) -> List[Type]:
        """
        从目录加载所有技能
        
        Args:
            directory: 技能目录
            
        Returns:
            加载的技能类列表
        """
        loaded = []
        for py_file in directory.glob("*.py"):
            if not py_file.name.startswith("_"):
                skill_class = self.load_from_file(py_file)
                if skill_class:
                    loaded.append(skill_class)
        return loaded
    
    def save_to_file(self, name: str, code: str, metadata: Dict = None) -> Path:
        """
        保存技能到文件
        
        Args:
            name: 技能名称
            code: 技能代码
            metadata: 元数据
            
        Returns:
            保存的文件路径
        """
        # 保存代码
        code_file = self.storage_dir / f"{name}.py"
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 保存元数据
        if metadata:
            meta_file = self.storage_dir / f"{name}.meta.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return code_file
    
    def clear(self):
        """清空注册表"""
        self._skills.clear()
        self._metadata.clear()
        self._instances.clear()
        logger.info("清空技能注册表")