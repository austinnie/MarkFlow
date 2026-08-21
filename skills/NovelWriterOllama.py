"""
novel_writer_ollama - 使用本地 Ollama 大模型自动写小说（支持断点续写和连载）

功能：
  - 自动保存小说到文件
  - 断点续写：中断后可以从上次进度继续
  - 连载：基于已有内容生成后续章节
"""

import requests
import json
import logging
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class NovelWriterOllama:
    """
    使用本地 Ollama 大模型自动写小说（支持断点续写和连载）
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化技能"""
        self.config = config or {}
        self.name = "novel_writer_ollama"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        logger.info("NovelWriterOllama 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'default_model': 'qwen2.5:7b',
            'ollama_url': 'http://localhost:11434',
            'default_temperature': 0.85,
            'default_chapter_count': 3,
            'default_words_per_chapter': 500,
            'output_dir': './generated_novels'
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        required = ['genre', 'title', 'outline', 'characters']
        for param in required:
            if param not in kwargs or not kwargs[param]:
                raise ValueError(f"缺少必需参数: {param}")
        
        chapter_count = kwargs.get('chapter_count', self.config.get('default_chapter_count', 3))
        words_per_chapter = kwargs.get('words_per_chapter', self.config.get('default_words_per_chapter', 500))
        temperature = kwargs.get('temperature', self.config.get('default_temperature', 0.85))
        
        if not (1 <= chapter_count <= 20):
            raise ValueError(f"chapter_count 必须在 1-20 之间，当前值: {chapter_count}")
        if not (200 <= words_per_chapter <= 2000):
            raise ValueError(f"words_per_chapter 必须在 200-2000 之间，当前值: {words_per_chapter}")
        if not (0 <= temperature <= 1):
            raise ValueError(f"temperature 必须在 0-1 之间，当前值: {temperature}")
        
        return True
    
    def _check_ollama(self, ollama_url: str) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                logger.info(f"Ollama 服务可用，已安装模型: {', '.join(models)}")
                return True
        except Exception as e:
            logger.error(f"Ollama 服务连接失败: {e}")
            return False
        return False
    
    def _call_ollama(self, ollama_url: str, model: str, prompt: str, temperature: float = 0.85) -> str:
        """调用 Ollama API"""
        url = f"{ollama_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2048
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            return data.get('response', '').strip()
        except requests.exceptions.Timeout:
            logger.error("Ollama 请求超时")
            return ""
        except Exception as e:
            logger.error(f"Ollama API 调用失败: {e}")
            return ""
    
    def _load_existing_novel(self, filepath: str) -> Dict:
        """加载已有小说内容"""
        path = Path(filepath)
        if not path.exists():
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析标题
        title_match = re.search(r'标题：(.+)', content)
        title = title_match.group(1).strip() if title_match else None
        
        # 解析类型
        genre_match = re.search(r'类型：(.+)', content)
        genre = genre_match.group(1).strip() if genre_match else None
        
        # 解析总字数
        words_match = re.search(r'总字数：(\d+)', content)
        total_words = int(words_match.group(1)) if words_match else 0
        
        # 解析各章节
        chapters = []
        chapter_pattern = r'第(\d+)章：(.+?)\n-{40,}\n(.*?)(?=\n-{40,}\n第\d+章：|$)'
        matches = re.findall(chapter_pattern, content, re.DOTALL)
        
        for match in matches:
            chapters.append({
                "index": int(match[0]),
                "title": match[1].strip(),
                "content": match[2].strip()
            })
        
        return {
            "title": title,
            "genre": genre,
            "chapters": chapters,
            "total_words": total_words,
            "filepath": str(path)
        }
    
    def _save_novel(self, result_data: Dict, is_continue: bool = False) -> str:
        """保存小说到文件"""
        output_dir = Path(self.config.get('output_dir', './generated_novels'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        title = result_data.get('title', 'untitled')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 如果是续写，使用原文件名
        if is_continue and result_data.get('filepath'):
            filepath = Path(result_data['filepath'])
        else:
            filepath = output_dir / f"{title}_{timestamp}.txt"
        
        content_lines = []
        content_lines.append("=" * 60)
        content_lines.append(f"  标题：{result_data.get('title', '')}")
        content_lines.append(f"  类型：{result_data.get('genre', '')}")
        content_lines.append(f"  模型：{result_data.get('model_used', '')}")
        content_lines.append(f"  生成时间：{result_data.get('generated_at', '')}")
        content_lines.append(f"  总字数：{result_data.get('total_words', 0)}")
        content_lines.append("=" * 60)
        content_lines.append("")
        content_lines.append("【小说简介】")
        content_lines.append(result_data.get('summary', ''))
        content_lines.append("")
        content_lines.append("=" * 60)
        content_lines.append("")
        
        for chapter in result_data.get('chapters', []):
            content_lines.append(f"第{chapter['index']}章：{chapter['title']}")
            content_lines.append("-" * 40)
            content_lines.append(chapter['content'])
            content_lines.append("")
            content_lines.append("-" * 40)
            content_lines.append("")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
        return str(filepath)
    
    def _generate_chapter(self, ollama_url: str, model: str, genre: str, title: str,
                          outline: str, characters: str, chapter_index: int,
                          total_chapters: int, style: str, temperature: float,
                          prev_chapters: List[Dict] = None) -> Dict[str, str]:
        """生成单个章节"""
        
        # 构建系统提示词
        system_prompt = f"""你是一位专业的小说作家，擅长写{genre}类型的小说。
请根据以下设定继续写小说：

小说标题：{title}
小说类型：{genre}
故事大纲：{outline}
角色设定：{characters}
写作风格：{style}
当前正在写第 {chapter_index}/{total_chapters} 章

要求：
- 每章约500-800字
- 章节需要有标题
- 内容连贯，情节推进
- 符合角色设定
- 语言流畅，描写生动
"""
        
        # 添加之前章节的上下文
        context = ""
        if prev_chapters:
            # 提供最近2章的完整内容，确保连贯性
            recent = prev_chapters[-2:]
            context = "\n\n前面章节内容：\n"
            for c in recent:
                context += f"第{c['index']}章：{c['title']}\n"
                context += c['content'][:300] + "...\n\n"
        
        # 生成章节标题
        title_prompt = f"{system_prompt}\n{context}\n\n请为第{chapter_index}章生成一个吸引人的章节标题（仅输出标题，不要其他内容）："
        chapter_title = self._call_ollama(ollama_url, model, title_prompt, temperature)
        chapter_title = chapter_title.strip().strip('"').strip('「').strip('」')
        if not chapter_title:
            chapter_title = f"第{chapter_index}章"
        
        # 生成章节内容
        content_prompt = f"{system_prompt}\n{context}\n\n章节标题：{chapter_title}\n\n请写出第{chapter_index}章的完整内容："
        chapter_content = self._call_ollama(ollama_url, model, content_prompt, temperature)
        
        return {
            "index": chapter_index,
            "title": chapter_title,
            "content": chapter_content
        }
    
    def _generate_summary(self, ollama_url: str, model: str, genre: str, title: str,
                          outline: str, characters: str, chapters: List[Dict]) -> str:
        """生成小说简介"""
        if not chapters:
            return f"《{title}》是一部{genre}小说，讲述了{outline}的故事。"
        
        chapter_summaries = "\n".join([f"第{c['index']}章：{c['title']}" for c in chapters])
        
        prompt = f"""你是一位小说编辑，请为以下小说撰写一段吸引人的简介（200字以内）：

小说标题：{title}
小说类型：{genre}
故事大纲：{outline}
角色设定：{characters}
章节概览：{chapter_summaries}

请写出小说简介："""
        
        summary = self._call_ollama(ollama_url, model, prompt, 0.7)
        if not summary:
            summary = f"《{title}》是一部{genre}小说，讲述了{outline}的故事。"
        return summary
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行小说生成（支持断点续写）"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            self._validate_inputs(**kwargs)
            
            genre = kwargs.get('genre')
            title = kwargs.get('title')
            outline = kwargs.get('outline')
            characters = kwargs.get('characters')
            chapter_count = kwargs.get('chapter_count', self.config.get('default_chapter_count', 3))
            words_per_chapter = kwargs.get('words_per_chapter', self.config.get('default_words_per_chapter', 500))
            style = kwargs.get('style', '细腻')
            temperature = kwargs.get('temperature', self.config.get('default_temperature', 0.85))
            model = kwargs.get('model', self.config.get('default_model', 'qwen2.5:7b'))
            ollama_url = kwargs.get('ollama_url', self.config.get('ollama_url', 'http://localhost:11434'))
            continue_from = kwargs.get('continue_from', None)  # 续写文件路径
            
            logger.info(f"检查 Ollama 服务: {ollama_url}")
            if not self._check_ollama(ollama_url):
                return {
                    "status": "error",
                    "error": f"Ollama 服务不可用: {ollama_url}"
                }
            
            # 检查是否是续写模式
            existing_data = None
            if continue_from:
                existing_data = self._load_existing_novel(continue_from)
                if existing_data:
                    logger.info(f"📖 加载已有小说: {existing_data['title']}")
                    logger.info(f"   已有 {len(existing_data['chapters'])} 章，{existing_data['total_words']} 字")
                    # 使用已有数据
                    genre = existing_data.get('genre', genre)
                    title = existing_data.get('title', title)
                    existing_chapters = existing_data.get('chapters', [])
                    # 从已有章节数+1开始续写
                    start_index = len(existing_chapters) + 1
                    # 计算需要续写的章节数
                    total_needed = chapter_count
                    chapters_to_generate = total_needed - len(existing_chapters)
                    if chapters_to_generate <= 0:
                        return {
                            "status": "success",
                            "result": existing_data,
                            "message": f"已有 {len(existing_chapters)} 章，已达到目标章节数 {total_needed}"
                        }
                    logger.info(f"  续写 {chapters_to_generate} 章 (从第 {start_index} 章开始)")
                else:
                    logger.warning(f"未找到续写文件: {continue_from}，将从头开始生成")
                    existing_chapters = []
                    start_index = 1
                    chapters_to_generate = chapter_count
            else:
                existing_chapters = []
                start_index = 1
                chapters_to_generate = chapter_count
            
            logger.info(f"开始生成小说: {title}")
            logger.info(f"  模型: {model}")
            logger.info(f"  类型: {genre}")
            logger.info(f"  总章节数: {chapter_count}")
            logger.info(f"  已有章节: {len(existing_chapters)}")
            logger.info(f"  需生成: {chapters_to_generate}")
            
            # 准备章节列表
            all_chapters = existing_chapters.copy()
            prev_chapters = all_chapters.copy()
            
            for i in range(chapters_to_generate):
                chapter_idx = start_index + i
                logger.info(f"  生成第 {chapter_idx}/{chapter_count} 章...")
                chapter = self._generate_chapter(
                    ollama_url, model, genre, title, outline, characters,
                    chapter_idx, chapter_count, style, temperature, prev_chapters
                )
                all_chapters.append(chapter)
                prev_chapters.append(chapter)
                time.sleep(0.5)
            
            # 生成或更新简介
            logger.info("  生成小说简介...")
            summary = self._generate_summary(ollama_url, model, genre, title, outline, characters, all_chapters)
            
            total_words = sum(len(c['content']) for c in all_chapters)
            
            result_data = {
                "title": title,
                "genre": genre,
                "summary": summary,
                "chapters": all_chapters,
                "total_words": total_words,
                "model_used": model,
                "generated_at": datetime.now().isoformat(),
                "generation_time": f"{time.time() - start_time:.2f}s"
            }
            
            # 如果是续写，保留原文件路径
            if existing_data and existing_data.get('filepath'):
                result_data['filepath'] = existing_data['filepath']
            
            # 保存到文件
            saved_path = self._save_novel(result_data, is_continue=bool(existing_data))
            result_data['saved_to'] = saved_path
            
            generation_time = time.time() - start_time
            
            logger.info(f"✅ 小说生成完成! 共 {len(all_chapters)} 章，{total_words} 字")
            logger.info(f"  耗时: {generation_time:.2f}s")
            logger.info(f"  保存位置: {saved_path}")
            
            return {
                "status": "success",
                "result": result_data,
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
        return f"<NovelWriterOllama(name={self.name}, version={self.version})>"