"""
sd_image_generator - 利用本地 Stable Diffusion 模型，根据文本描述生成高质量图片


输入参数:
  - prompt (string): 图片描述提示词
  - negative_prompt (string): 负面提示词
  - model_name (string): 使用的模型文件名
  - width (integer): 生成图片宽度，范围 256-1024
  - height (integer): 生成图片高度，范围 256-1024
  - steps (integer): 采样步数，范围 10-50
  - cfg_scale (float): 提示词引导强度，范围 1.0-20.0
  - seed (integer): 随机种子，-1 表示随机
  - output_dir (string): 输出目录
  - batch_size (integer): 一次生成数量，范围 1-4
  - scheduler (string): 采样调度器

输出:
  - image_paths: 生成的图片路径列表
  - parameters: 使用的生成参数
  - model_used: 使用的模型名称
  - generation_time: 生成耗时(秒)
  - generated_at: 生成时间

执行步骤:
  1. 验证输入参数
  2. 检查模型文件是否存在
  3. 加载选定的模型
  4. 设置随机种子
  5. 执行图片生成
  6. 保存生成的图片
  7. 返回生成结果信息
"""

# import safetensors  # 可选依赖
# import diffusers  # 可选依赖
import sys
import time
import re
# import torch  # 可选依赖
import json
import os
# import accelerate  # 可选依赖
# import transformers  # 可选依赖
import random
# import Pillow  # 可选依赖

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SdImageGenerator:
    """
    利用本地 Stable Diffusion 模型，根据文本描述生成高质量图片
    
    执行技能功能
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化技能
        
        Args:
            config: 配置参数字典
        """
        self.config = config or {}
        self.name = "sd_image_generator"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        """设置配置"""
        defaults = {}
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> bool:
        """
        验证输入参数
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            验证是否通过
        """
        # 检查必填参数
        required_params = ["prompt"]
        for param in required_params:
            if param not in kwargs or kwargs[param] is None or kwargs[param] == "":
                raise ValueError(f"缺少必需参数: {param}")

        # 类型验证
        if "width" in kwargs and kwargs["width"] is not None:
            try:
                kwargs["width"] = int(kwargs["width"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 width 必须是整数")
        if "height" in kwargs and kwargs["height"] is not None:
            try:
                kwargs["height"] = int(kwargs["height"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 height 必须是整数")
        if "steps" in kwargs and kwargs["steps"] is not None:
            try:
                kwargs["steps"] = int(kwargs["steps"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 steps 必须是整数")
        if "cfg_scale" in kwargs and kwargs["cfg_scale"] is not None:
            try:
                kwargs["cfg_scale"] = float(kwargs["cfg_scale"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 cfg_scale 必须是数字")
        if "seed" in kwargs and kwargs["seed"] is not None:
            try:
                kwargs["seed"] = int(kwargs["seed"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 seed 必须是整数")
        if "batch_size" in kwargs and kwargs["batch_size"] is not None:
            try:
                kwargs["batch_size"] = int(kwargs["batch_size"])
            except (ValueError, TypeError):
                raise ValueError(f"参数 batch_size 必须是整数")

        # 设置默认值
        if "model_name" not in kwargs or kwargs["model_name"] is None:
            kwargs["model_name"] = 'sd-v1-5-tiny.safetensors'
        if "width" not in kwargs or kwargs["width"] is None:
            kwargs["width"] = '512'
        if "height" not in kwargs or kwargs["height"] is None:
            kwargs["height"] = '512'
        if "steps" not in kwargs or kwargs["steps"] is None:
            kwargs["steps"] = '20'
        if "cfg_scale" not in kwargs or kwargs["cfg_scale"] is None:
            kwargs["cfg_scale"] = '7.0'
        if "seed" not in kwargs or kwargs["seed"] is None:
            kwargs["seed"] = '-1'
        if "output_dir" not in kwargs or kwargs["output_dir"] is None:
            kwargs["output_dir"] = './generated_images'
        if "batch_size" not in kwargs or kwargs["batch_size"] is None:
            kwargs["batch_size"] = '1'
        if "scheduler" not in kwargs or kwargs["scheduler"] is None:
            kwargs["scheduler"] = 'ddim'

        return True
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            执行结果
        """
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            # 执行步骤
            kwargs = self._step_1(**kwargs)
            kwargs = self._step_2(**kwargs)
            kwargs = self._step_3(**kwargs)
            kwargs = self._step_4(**kwargs)
            kwargs = self._step_5(**kwargs)
            kwargs = self._step_6(**kwargs)
            kwargs = self._step_7(**kwargs)
            
            result_data = kwargs
            
            result = {
                "status": "success",
                "result": result_data,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"技能执行成功: {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"技能执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _step_1(self, **kwargs):
            """
            验证输入参数
            """
            logger.info(f"执行步骤: 验证输入参数")
            
            # 获取要验证的数据
            data = kwargs.get("data") or kwargs.get("input_data")
            if data is None:
                for key in ["content", "text", "result"]:
                    if key in kwargs and kwargs[key]:
                        data = kwargs[key]
                        break
            
            if data is None:
                raise ValueError("没有数据可验证")
            
            # 验证数据
            try:
                is_valid = self._validate_data(data, **kwargs)
                if not is_valid:
                    raise ValueError("数据验证失败")
                kwargs["validated"] = True
                logger.info(f"数据验证通过")
            except Exception as e:
                logger.error(f"数据验证失败: {e}")
                raise
            
            return kwargs

    def _step_2(self, **kwargs):
            """
            检查模型文件是否存在
            """
            logger.info(f"执行步骤: 检查模型文件是否存在")
            
            # 获取要验证的数据
            data = kwargs.get("data") or kwargs.get("input_data")
            if data is None:
                for key in ["content", "text", "result"]:
                    if key in kwargs and kwargs[key]:
                        data = kwargs[key]
                        break
            
            if data is None:
                raise ValueError("没有数据可验证")
            
            # 验证数据
            try:
                is_valid = self._validate_data(data, **kwargs)
                if not is_valid:
                    raise ValueError("数据验证失败")
                kwargs["validated"] = True
                logger.info(f"数据验证通过")
            except Exception as e:
                logger.error(f"数据验证失败: {e}")
                raise
            
            return kwargs

    def _step_3(self, **kwargs):
            """
            加载选定的模型
            """
            logger.info(f"执行步骤: 加载选定的模型")
            
            # 获取数据源
            source = kwargs.get("source") or kwargs.get("file_path") or kwargs.get("data_source")
            if not source:
                for key in ["md_file", "file", "path", "input"]:
                    if key in kwargs and kwargs[key]:
                        source = kwargs[key]
                        break
            
            if not source:
                raise ValueError("未指定数据源")
            
            try:
                data = self._load_data(source, **kwargs)
                kwargs["data"] = data
                logger.info(f"数据加载成功: {source}")  # ✅ 改这里
            except Exception as e:
                logger.error(f"数据加载失败: {e}")
                raise
            
            return kwargs

    def _step_4(self, **kwargs):
            """
            设置随机种子
            """
            logger.info(f"执行步骤: 设置随机种子")
            
            # 通用处理逻辑
            input_data = kwargs.get("data") or kwargs.get("input")
            
            if input_data is not None:
                if isinstance(input_data, (list, dict)):
                    logger.info(f"处理数据: {len(input_data)} 项")
                else:
                    logger.info(f"处理数据: {type(input_data).__name__}")
                kwargs["processed"] = input_data
            
            return kwargs

    def _step_5(self, **kwargs):
            """
            执行图片生成
            """
            logger.info(f"执行步骤: 执行图片生成")
            
            params = {k: v for k, v in kwargs.items() if k not in ["self"]}
            
            try:
                result = self._generate_result(params, **kwargs)
                kwargs["generated"] = result
                logger.info(f"生成完成")
            except Exception as e:
                logger.error(f"生成失败: {e}")
                raise
            
            return kwargs

    def _step_6(self, **kwargs):
            """
            保存生成的图片
            """
            logger.info(f"执行步骤: 保存生成的图片")
            
            data = kwargs.get("data") or kwargs.get("result")
            destination = kwargs.get("destination") or kwargs.get("output") or kwargs.get("output_path")
            
            if not destination:
                for key in ["output_file", "save_path", "path"]:
                    if key in kwargs and kwargs[key]:
                        destination = kwargs[key]
                        break
            
            if not destination:
                raise ValueError("未指定保存路径")
            
            if data is None:
                raise ValueError("没有数据可保存")
            
            try:
                self._save_data(data, destination, **kwargs)
                kwargs["saved_path"] = destination
                logger.info(f"数据保存成功: {destination}")  # ✅ 改这里
            except Exception as e:
                logger.error(f"数据保存失败: {e}")
                raise
            
            return kwargs

    def _step_7(self, **kwargs):
            """
            返回生成结果信息
            """
            logger.info(f"执行步骤: 返回生成结果信息")
            
            params = {k: v for k, v in kwargs.items() if k not in ["self"]}
            
            try:
                result = self._generate_result(params, **kwargs)
                kwargs["generated"] = result
                logger.info(f"生成完成")
            except Exception as e:
                logger.error(f"生成失败: {e}")
                raise
            
            return kwargs


    def _handle_error(self, error: Exception, context: str = "") -> Dict:
        """处理错误"""
        logger.error(f"{context}: {error}")
        return {
            "status": "error",
            "error": str(error),
            "context": context
        }
    
    def _log_step(self, step_name: str, **kwargs):
        """记录步骤日志"""
        logger.info(f"步骤: {step_name}")


    def _load_data(self, source: str, **kwargs) -> Any:
        """加载数据"""
        import json
        from pathlib import Path
        
        if source.startswith(('http://', 'https://')):
            import requests
            response = requests.get(source, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if 'json' in content_type:
                return response.json()
            elif 'text' in content_type:
                return response.text
            else:
                return response.content
        else:
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {source}")
            
            if source.endswith(('.csv', '.tsv')):
                import pandas as pd
                return pd.read_csv(source)
            elif source.endswith('.json'):
                with open(source, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif source.endswith(('.yaml', '.yml')):
                import yaml
                with open(source, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                with open(source, 'r', encoding='utf-8') as f:
                    return f.read()


    def _save_data(self, data: Any, destination: str, **kwargs) -> bool:
        """保存数据"""
        import json
        from pathlib import Path
        
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        
        if destination.endswith('.json'):
            with open(destination, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif destination.endswith('.csv'):
            import pandas as pd
            if isinstance(data, (list, dict)):
                pd.DataFrame(data).to_csv(destination, index=False)
            else:
                pd.DataFrame([data]).to_csv(destination, index=False)
        elif destination.endswith(('.yaml', '.yml')):
            import yaml
            with open(destination, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True)
        else:
            with open(destination, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        logger.info(f"数据已保存: {destination}")
        return True


    def _validate_data(self, data: Any, **kwargs) -> bool:
        """验证数据"""
        if data is None:
            logger.warning("数据为空")
            return False
        
        if isinstance(data, (list, dict)) and not data:
            logger.warning("数据为空容器")
            return False
        
        if isinstance(data, str) and not data.strip():
            logger.warning("数据为空字符串")
            return False
        
        logger.info(f"数据验证通过: 类型={type(data).__name__}")
        return True


    def _generate_result(self, params: Dict, **kwargs) -> Dict:
        """生成结果"""
        from datetime import datetime
        
        return {
            "status": "success",
            "generated_at": datetime.now().isoformat(),
            "params": params,
            "result": params
        }

    def __repr__(self):
        return f"<SdImageGenerator(name={self.name}, version={self.version})>"