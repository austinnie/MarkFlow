"""
voice_assistant - 语音合成（TTS）和语音识别（STT）助手
"""

import os
import time
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# TTS 依赖
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# STT 依赖
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# 音频处理
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    from mutagen.mp3 import MP3
    from mutagen import File
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

class VoiceAssistant:
    """语音合成和识别助手"""
    
    # 默认语音列表
    DEFAULT_VOICES = [
        {"name": "zh-CN-XiaoxiaoNeural", "locale": "zh-CN", "gender": "Female", "style": "General"},
        {"name": "zh-CN-XiaoyiNeural", "locale": "zh-CN", "gender": "Female", "style": "General"},
        {"name": "zh-CN-YunjianNeural", "locale": "zh-CN", "gender": "Male", "style": "General"},
        {"name": "zh-CN-YunxiNeural", "locale": "zh-CN", "gender": "Male", "style": "General"},
        {"name": "zh-CN-YunxiaNeural", "locale": "zh-CN", "gender": "Male", "style": "General"},
        {"name": "en-US-JennyNeural", "locale": "en-US", "gender": "Female", "style": "General"},
        {"name": "en-US-GuyNeural", "locale": "en-US", "gender": "Male", "style": "General"},
        {"name": "en-US-AriaNeural", "locale": "en-US", "gender": "Female", "style": "General"},
        {"name": "ja-JP-NanamiNeural", "locale": "ja-JP", "gender": "Female", "style": "General"},
        {"name": "ko-KR-SunHiNeural", "locale": "ko-KR", "gender": "Female", "style": "General"},
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "voice_assistant"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        if not EDGE_TTS_AVAILABLE:
            logger.warning("edge-tts 未安装，TTS 功能不可用。请运行: pip install edge-tts")
        if not WHISPER_AVAILABLE:
            logger.warning("whisper 未安装，STT 功能不可用。请运行: pip install openai-whisper")
        
        logger.info("VoiceAssistant 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _setup_config(self):
        defaults = {
            'output_dir': './audio_output',
            'default_voice': 'zh-CN-XiaoxiaoNeural',
            'default_speed': 1.0,
            'default_language': 'zh-CN',
            'sample_rate': 16000
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _validate_inputs(self, **kwargs) -> Dict:
        """验证输入参数"""
        action = kwargs.get('action', '')
        if action not in ['tts', 'stt', 'list_voices']:
            raise ValueError(f"不支持的操作: {action}，支持: tts, stt, list_voices")
        
        if action == 'tts':
            # 支持 text 或 text_file
            text = kwargs.get('text', '')
            text_file = kwargs.get('text_file', '')
            if not text and not text_file:
                raise ValueError("tts 操作需要 text 或 text_file 参数")
        
        if action == 'stt':
            if 'audio_file' not in kwargs or not kwargs['audio_file']:
                raise ValueError("stt 操作需要 audio_file 参数")
            audio_path = Path(kwargs['audio_file'])
            if not audio_path.exists():
                raise ValueError(f"音频文件不存在: {audio_path}")
        
        return kwargs
    
    
    def _list_voices(self) -> Dict:
        """列出可用语音"""
        # 如果 edge-tts 可用，获取最新列表
        voices = self.DEFAULT_VOICES
        if EDGE_TTS_AVAILABLE:
            try:
                import asyncio
                # 尝试获取最新语音列表
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(edge_tts.list_voices())
                    if result:
                        voices = []
                        for v in result:
                            voices.append({
                                "name": v.get("ShortName", ""),
                                "locale": v.get("Locale", ""),
                                "gender": v.get("Gender", ""),
                                "style": v.get("StyleList", [""])[0] if v.get("StyleList") else "General"
                            })
                except:
                    pass
            except:
                pass
        
        return {
            "voices": voices,
            "count": len(voices),
            "default": self.config.get('default_voice', 'zh-CN-XiaoxiaoNeural')
        }
    
    def _generate_filename(self, text: str, voice: str, output_dir: Path) -> str:
        """生成有意义的文件名"""
        # 取文本前 15 个字符作为名称
        text_preview = text[:15].strip()
        # 移除特殊字符
        text_preview = re.sub(r'[^\w\u4e00-\u9fff]', '', text_preview)
        if not text_preview:
            text_preview = "语音"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        voice_short = voice.split('-')[0] if '-' in voice else voice[:8]
        
        return f"{text_preview}_{voice_short}_{timestamp}.mp3"
    

    def _tts(self, text: str, voice: str = None, speed: float = None,
             pitch: str = None, output_file: str = None) -> Dict:
        """文字转语音"""
        if not EDGE_TTS_AVAILABLE:
            return {"error": "edge-tts 未安装", "status": "error"}
        
        voice = voice or self.config.get('default_voice', 'zh-CN-XiaoxiaoNeural')
        speed = speed or self.config.get('default_speed', 1.0)
        
        output_dir = Path(self.config.get('output_dir', './audio_output'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not output_file:
            # 生成有意义的文件名
            output_file = str(output_dir / self._generate_filename(text, voice, output_dir))
        else:
            output_path = Path(output_file)
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import asyncio
            rate = f"{int((speed - 1.0) * 100):+d}%"
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(communicate.save(output_file))
            
            duration = self._get_audio_duration(output_file)
            
            return {
                "audio_path": output_file,
                "duration": duration,
                "text": text[:100] + "..." if len(text) > 100 else text,
                "voice": voice,
                "speed": speed,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"TTS 失败: {e}")
            return {"error": str(e), "status": "error"}
        


    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        if MUTAGEN_AVAILABLE:
            try:
                audio = File(audio_path)
                if audio:
                    return audio.info.length
            except:
                pass
        return 0.0
    
    def _stt(self, audio_file: str, language: str = None) -> Dict:
        """语音转文字"""
        if not WHISPER_AVAILABLE:
            return {"error": "whisper 未安装，请运行: pip install openai-whisper", "status": "error"}
        
        language = language or self.config.get('default_language', 'zh-CN')
        
        try:
            # 加载模型
            model = whisper.load_model("base")
            
            # 转录音频
            result = model.transcribe(audio_file, language=language)
            
            return {
                "transcript": result["text"].strip(),
                "language": result.get("language", language),
                "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0,
                "confidence": result.get("segments", [{}])[0].get("confidence", 0) if result.get("segments") else 0,
                "segments": result.get("segments", []),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"STT 失败: {e}")
            return {"error": str(e), "status": "error"}


    def _read_text_file(self, file_path: str) -> str:
        """读取文本文件并清理 Markdown 标记"""
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"文件不存在: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 清理 Markdown 标记
        content = self._clean_markdown(content)
        
        return content.strip()

    def _clean_markdown(self, text: str) -> str:
        """清理 Markdown 标记，只保留纯文本"""
        import re
        
        # 移除代码块 ```...```
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # 移除标题标记 # ## ### 等
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 移除分割线 --- 或 *** 或 ===
        text = re.sub(r'^[-=*]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # 移除粗体 **text** 或 __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # 移除斜体 *text* 或 _text_
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # 移除行内代码 `code`
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # 移除链接 [text](url)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        # 移除图片 ![alt](url)
        text = re.sub(r'!\[(.+?)\]\(.+?\)', r'\1', text)
        
        # 移除列表标记 - 或 * 或 1. 等
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 移除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除分隔线字符（单独一行的 ======）
        text = re.sub(r'^[=\-]{10,}\s*$', '', text, flags=re.MULTILINE)
        
        return text
    
    def _split_text(self, text: str, chunk_size: int = 500, auto_split: bool = True) -> List[str]:
        """将长文本分割成段落"""
        if not text:
            return []
        
        # 按句子分割
        if auto_split:
            import re
            # 按中文标点分割：。！？；\n
            sentences = re.split(r'[。！？；\n]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
        else:
            sentences = [text]
        
        # 合并成 chunk
        chunks = []
        current = ""
        for sentence in sentences:
            if len(current) + len(sentence) <= chunk_size:
                current += sentence + "。"
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence + "。"
        
        if current:
            chunks.append(current.strip())
        
        return chunks
    

    def _merge_audio(self, audio_paths: List[str], output_path: str = None) -> str:
        """使用 ffmpeg 合并多个音频文件为一个"""
        if len(audio_paths) == 1:
            return audio_paths[0]
        
        try:
            import subprocess
            
            # 检查 ffmpeg 是否可用
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            if result.returncode != 0:
                logger.warning("ffmpeg 未安装，无法合并音频")
                return None
            
            if not output_path:
                output_dir = Path(audio_paths[0]).parent
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(output_dir / f"merged_{timestamp}.mp3")
            
            # 创建 ffmpeg 需要的文件列表
            list_file = Path(audio_paths[0]).parent / "merge_list.txt"
            with open(list_file, 'w', encoding='utf-8') as f:
                for path in audio_paths:
                    # ffmpeg concat 需要绝对路径
                    abs_path = str(Path(path).absolute())
                    f.write(f"file '{abs_path}'\n")
            
            # 执行 ffmpeg 合并
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(list_file),
                '-c', 'copy',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            
            # 清理临时文件
            if list_file.exists():
                list_file.unlink()
            
            if result.returncode == 0 and Path(output_path).exists():
                return output_path
            else:
                logger.error(f"ffmpeg 合并失败: {result.stderr.decode() if result.stderr else '未知错误'}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("ffmpeg 合并超时")
            return None
        except Exception as e:
            logger.error(f"合并音频失败: {e}")
            return None
        

    def _ensure_ffmpeg(self):
        """确保 ffmpeg 可用"""
        import subprocess
        import sys
        
        try:
            # 检查 ffmpeg 是否可用
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            logger.warning("ffmpeg 未安装，尝试自动安装...")
            try:
                # 使用 pip 安装 ffmpeg-python
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'ffmpeg-python'], 
                              capture_output=True, check=True)
                return True
            except:
                logger.error("ffmpeg 安装失败，请手动安装")
                return False
            
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行操作"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            params = self._validate_inputs(**kwargs)
            action = params.get('action')
            
            if action == 'list_voices':
                result = self._list_voices()
            
            elif action == 'tts':
                text = params.get('text', '')
                text_file = params.get('text_file', '')
                voice = params.get('voice', self.config.get('default_voice', 'zh-CN-XiaoxiaoNeural'))
                speed = params.get('speed', self.config.get('default_speed', 1.0))
                output_file = params.get('output_file')
                chunk_size = params.get('chunk_size', 500)
                auto_split = params.get('auto_split', True)

                # 定义输出目录（这里添加）
                output_dir = Path(self.config.get('output_dir', './audio_output'))
                output_dir.mkdir(parents=True, exist_ok=True)
    
                # 从文件读取文本
                if text_file and not text:
                    text = self._read_text_file(text_file)
                
                if not text:
                    raise ValueError("请提供 text 或 text_file 参数")
                
                # 如果文本太长，分段生成
                chunks = self._split_text(text, chunk_size, auto_split)
                
                if len(chunks) > 1:
                    logger.info(f"文本较长，分为 {len(chunks)} 段朗读")
                    audio_paths = []
                    for i, chunk in enumerate(chunks):
                        logger.info(f"  生成第 {i+1}/{len(chunks)} 段...")
                        # 为每段生成有意义的文件名
                        seg_file = str(output_dir / self._generate_filename(
                            chunk[:20] + f"_第{i+1}段", voice, output_dir
                        ))
                        result = self._tts(chunk, voice, speed, seg_file)
                        if result.get('status') != 'success':
                            return result
                        audio_paths.append(result.get('audio_path'))
                    
                    # ✅ 合并所有分段
                    merged_path = None
                    if len(audio_paths) > 1:
                        logger.info(f"🔄 正在合并 {len(audio_paths)} 段音频...")
                        merged_path = self._merge_audio(audio_paths)
                        if merged_path:
                            logger.info(f"✅ 合并完成: {merged_path}")
                            result = {
                                "audio_path": merged_path,
                                "chunks": len(chunks),
                                "segment_files": audio_paths,
                                "text": text[:200] + "..." if len(text) > 200 else text,
                                "voice": voice,
                                "speed": speed,
                                "status": "success"
                            }
                        else:
                            # 合并失败，返回分段文件
                            result = {
                                "audio_paths": audio_paths,
                                "chunks": len(chunks),
                                "text": text[:200] + "..." if len(text) > 200 else text,
                                "voice": voice,
                                "speed": speed,
                                "status": "success",
                                "warning": "合并失败，返回分段文件"
                            }
                    else:
                        result = {
                            "audio_path": audio_paths[0] if audio_paths else None,
                            "chunks": len(chunks),
                            "text": text[:200] + "..." if len(text) > 200 else text,
                            "voice": voice,
                            "speed": speed,
                            "status": "success"
                        }
                else:
                    result = self._tts(text, voice, speed, output_file)
            
            elif action == 'stt':
                audio_file = params.get('audio_file')
                language = params.get('language', self.config.get('default_language', 'zh-CN'))
                result = self._stt(audio_file, language)
            
            else:
                result = {"message": f"未知操作: {action}", "status": "error"}
            
            result['action'] = action
            result['processing_time'] = f"{time.time() - start_time:.2f}s"
            
            return {
                "status": "success" if result.get('status') != 'error' else "error",
                "result": result,
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
        return f"<VoiceAssistant(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="语音助手")
    parser.add_argument("--action", "-a", choices=['tts', 'stt', 'list_voices'], 
                       required=True, help="操作类型")
    parser.add_argument("--text", "-t", help="要合成的文本")
    parser.add_argument("--audio", "-f", help="音频文件路径")
    parser.add_argument("--voice", "-v", default="zh-CN-XiaoxiaoNeural", help="语音类型")
    parser.add_argument("--speed", "-s", type=float, default=1.0, help="语速 0.5-2.0")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--language", "-l", default="zh-CN", help="识别语言")
    
    args = parser.parse_args()
    
    assistant = VoiceAssistant()
    result = assistant.execute(
        action=args.action,
        text=args.text,
        audio_file=args.audio,
        voice=args.voice,
        speed=args.speed,
        output_file=args.output,
        language=args.language
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))