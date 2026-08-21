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
            if 'text' not in kwargs or not kwargs['text']:
                raise ValueError("tts 操作需要 text 参数")
        
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
    

    def _tts(self, text: str, voice: str = None, speed: float = None,
             pitch: str = None, output_file: str = None) -> Dict:
        """文字转语音"""
        if not EDGE_TTS_AVAILABLE:
            return {"error": "edge-tts 未安装，请运行: pip install edge-tts", "status": "error"}
        
        voice = voice or self.config.get('default_voice', 'zh-CN-XiaoxiaoNeural')
        speed = speed or self.config.get('default_speed', 1.0)
        
        # 创建输出目录
        output_dir = Path(self.config.get('output_dir', './audio_output'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = str(output_dir / f"tts_{timestamp}.mp3")
        else:
            output_path = Path(output_file)
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import asyncio
            
            # 语速设置
            rate = f"{int((speed - 1.0) * 100):+d}%"
            
            # 只传 text, voice, rate，不传 pitch
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(communicate.save(output_file))
            
            duration = self._get_audio_duration(output_file)
            
            return {
                "audio_path": output_file,
                "duration": duration,
                "text": text,
                "voice": voice,
                "speed": speed,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"TTS 失败: {e}")
            return {"error": str(e), "status": "error"}
        
  
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        if not PYDUB_AVAILABLE:
            return 0.0
        try:
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except:
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
                text = params.get('text')
                voice = params.get('voice', self.config.get('default_voice', 'zh-CN-XiaoxiaoNeural'))
                speed = params.get('speed', self.config.get('default_speed', 1.0))
                pitch = params.get('pitch', 'default')
                output_file = params.get('output_file')
                result = self._tts(text, voice, speed, pitch, output_file)
            
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