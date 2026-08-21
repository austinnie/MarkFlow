"""
代码收集器 - 收集和整理项目中的所有代码文件
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import argparse  # 添加这行


class CodeCollector:
    """代码收集器 - 收集项目中的所有代码文件"""
    
    # 支持的代码文件扩展名
    SUPPORTED_EXTENSIONS = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.xml': 'XML',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.bat': 'Batch',
        '.ps1': 'PowerShell',
        '.go': 'Go',
        '.rs': 'Rust',
        '.java': 'Java',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.pl': 'Perl',
        '.lua': 'Lua',
        '.r': 'R',
        '.swift': 'Swift',
        '.m': 'Objective-C',
        '.mm': 'Objective-C++',
        '.dart': 'Dart',
        '.ex': 'Elixir',
        '.exs': 'Elixir Script',
        '.erl': 'Erlang',
        '.hrl': 'Erlang Header',
        '.clj': 'Clojure',
        '.fs': 'F#',
        '.fsx': 'F# Script',
        '.vb': 'Visual Basic',
        '.vbs': 'VBScript',
        '.lisp': 'Lisp',
        '.el': 'Emacs Lisp',
        '.rkt': 'Racket',
        '.scm': 'Scheme',
        '.ml': 'OCaml',
        '.mli': 'OCaml Interface',
        '.hs': 'Haskell',
        '.lhs': 'Literate Haskell',
    }
    
    # 要忽略的目录
    IGNORE_DIRS = {
        '__pycache__',
        '.git',
        '.svn',
        '.hg',
        'node_modules',
        'vendor',
        'dist',
        'build',
        'target',
        'out',
        'bin',
        'obj',
        '.idea',
        '.vscode',
        '.mypy_cache',
        '.pytest_cache',
        '.coverage',
        'htmlcov',
        '.tox',
        'venv',
        'env',
        '.env',
        'virtualenv',
        '.eggs',
        '*.egg-info',
        '.mvn',
        '.gradle',
        '.settings',
        'logs',
        'tmp',
        'temp',
        'collected_code',   # 新增：忽略收集输出目录
        'skills',           # 新增：忽略技能目录
        'generated_images', # 新增：忽略图片生成目录
        '__pycache__',
    }
    
    # 要忽略的文件模式
    IGNORE_PATTERNS = {
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '*.so',
        '*.dll',
        '*.dylib',
        '*.exe',
        '*.class',
        '*.o',
        '*.a',
        '*.lib',
        '*.jar',
        '*.war',
        '*.ear',
        '*.zip',
        '*.tar.gz',
        '*.rar',
        '*.7z',
        '*.log',
        '*.tmp',
        '*.swp',
        '*.swo',
        '*~',
        '*.bak',
        '*.orig',
        '*.rej',
        '.DS_Store',
        'Thumbs.db',
        'desktop.ini',
        '*.safetensors',   # 新增：忽略模型文件
        '*.ckpt',          # 新增：忽略模型文件
        '*.pth',           # 新增：忽略模型文件
        '*.bin',           # 新增：忽略二进制文件
    }
    
    def __init__(self, root_dir: str = ".", output_dir: str = "collected_code"):
        """
        初始化代码收集器
        
        Args:
            root_dir: 项目根目录
            output_dir: 输出目录
        """
        self.root_dir = Path(root_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.files: List[Dict] = []
        self.stats: Dict = {
            'total_files': 0,
            'total_lines': 0,
            'total_characters': 0,
            'by_extension': {},
            'by_language': {},
            'largest_files': [],
            'oldest_files': [],
            'newest_files': []
        }
    
    def collect(self, include_extensions: List[str] = None, 
                exclude_dirs: List[str] = None,
                exclude_files: List[str] = None) -> Dict:
        """
        收集所有代码文件
        
        Args:
            include_extensions: 要包含的扩展名列表
            exclude_dirs: 要排除的目录列表
            exclude_files: 要排除的文件模式列表
            
        Returns:
            收集结果统计
        """
        include_extensions = include_extensions or list(self.SUPPORTED_EXTENSIONS.keys())
        exclude_dirs = exclude_dirs or []
        exclude_files = exclude_files or []
        
        # 合并忽略规则
        ignore_dirs = self.IGNORE_DIRS | set(exclude_dirs)
        ignore_patterns = self.IGNORE_PATTERNS | set(exclude_files)
        
        self.files = []
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_characters': 0,
            'by_extension': {},
            'by_language': {},
            'largest_files': [],
            'oldest_files': [],
            'newest_files': []
        }
        
        # 遍历目录
        for root, dirs, files in os.walk(self.root_dir):
            # 过滤目录
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            # 处理文件
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.root_dir)
                
                # 检查是否应该忽略
                if self._should_ignore(file_path, ignore_patterns):
                    continue
                
                # 检查扩展名
                ext = file_path.suffix.lower()
                if ext not in include_extensions:
                    continue
                
                # 收集文件信息
                file_info = self._collect_file_info(file_path, rel_path)
                if file_info:
                    self.files.append(file_info)
                    self._update_stats(file_info)
        
        # 排序文件
        self.stats['largest_files'] = sorted(
            self.files, 
            key=lambda x: x['size'], 
            reverse=True
        )[:10]
        
        self.stats['oldest_files'] = sorted(
            self.files,
            key=lambda x: x['modified_time']
        )[:10]
        
        self.stats['newest_files'] = sorted(
            self.files,
            key=lambda x: x['modified_time'],
            reverse=True
        )[:10]
        
        self.stats['total_files'] = len(self.files)
        
        return self.stats
    
    def _should_ignore(self, file_path: Path, patterns: set) -> bool:
        """检查文件是否应该被忽略"""
        # 检查文件名模式
        for pattern in patterns:
            if file_path.match(pattern):
                return True
        
        # 检查是否是隐藏文件
        if file_path.name.startswith('.'):
            return True
        
        return False
    
    def _collect_file_info(self, file_path: Path, rel_path: Path) -> Optional[Dict]:
        """收集单个文件的信息"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 统计信息
            lines = content.splitlines()
            line_count = len(lines)
            char_count = len(content)
            
            # 获取文件元数据
            stat = file_path.stat()
            
            ext = file_path.suffix.lower()
            language = self.SUPPORTED_EXTENSIONS.get(ext, 'Unknown')
            
            # 计算文件哈希
            file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            return {
                'path': str(rel_path),
                'absolute_path': str(file_path),
                'name': file_path.name,
                'extension': ext,
                'language': language,
                'size': stat.st_size,
                'lines': line_count,
                'characters': char_count,
                'hash': file_hash,
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'content': content,
                'preview': self._get_preview(content)
            }
            
        except Exception as e:
            print(f"⚠️  读取文件失败: {file_path} - {e}")
            return None
    
    def _get_preview(self, content: str, max_lines: int = 20) -> str:
        """获取文件预览"""
        lines = content.splitlines()
        if len(lines) <= max_lines:
            return content
        
        preview_lines = lines[:max_lines]
        return '\n'.join(preview_lines) + '\n... (截断)'
    
    def _update_stats(self, file_info: Dict):
        """更新统计信息"""
        ext = file_info['extension']
        language = file_info['language']
        
        self.stats['total_lines'] += file_info['lines']
        self.stats['total_characters'] += file_info['characters']
        
        # 按扩展名统计
        self.stats['by_extension'][ext] = self.stats['by_extension'].get(ext, 0) + 1
        
        # 按语言统计
        self.stats['by_language'][language] = self.stats['by_language'].get(language, 0) + 1
    
    def export_to_json(self, filename: str = "code_collection.json") -> Path:
        """导出到JSON文件"""
        output_file = self.output_dir / filename
        
        # 准备导出数据（不包含完整内容以减小文件大小）
        export_data = {
            'metadata': {
                'collected_at': datetime.now().isoformat(),
                'root_dir': str(self.root_dir),
                'total_files': self.stats['total_files'],
                'total_lines': self.stats['total_lines'],
                'total_characters': self.stats['total_characters']
            },
            'stats': {
                'by_extension': self.stats['by_extension'],
                'by_language': self.stats['by_language'],
                'largest_files': [
                    {
                        'path': f['path'],
                        'size': f['size'],
                        'lines': f['lines'],
                        'language': f['language']
                    }
                    for f in self.stats['largest_files']
                ]
            },
            'files': [
                {
                    'path': f['path'],
                    'extension': f['extension'],
                    'language': f['language'],
                    'size': f['size'],
                    'lines': f['lines'],
                    'hash': f['hash'],
                    'modified_time': f['modified_time'],
                    'preview': f['preview']
                }
                for f in self.files
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def export_to_markdown(self, filename: str = "code_collection.md") -> Path:
        """导出到Markdown文件"""
        output_file = self.output_dir / filename
        
        lines = []
        
        # 标题
        lines.append("# 代码收集报告")
        lines.append("")
        lines.append(f"**收集时间**: {datetime.now().isoformat()}")
        lines.append(f"**项目根目录**: `{self.root_dir}`")
        lines.append("")
        
        # 概览
        lines.append("## 📊 概览")
        lines.append("")
        lines.append(f"- 总文件数: **{self.stats['total_files']}**")
        lines.append(f"- 总代码行数: **{self.stats['total_lines']:,}**")
        lines.append(f"- 总字符数: **{self.stats['total_characters']:,}**")
        lines.append("")
        
        # 按语言统计
        lines.append("## 📈 按语言统计")
        lines.append("")
        lines.append("| 语言 | 文件数 |")
        lines.append("|------|--------|")
        for lang, count in sorted(self.stats['by_language'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {lang} | {count} |")
        lines.append("")
        
        # 按扩展名统计
        lines.append("## 📁 按扩展名统计")
        lines.append("")
        lines.append("| 扩展名 | 文件数 |")
        lines.append("|--------|--------|")
        for ext, count in sorted(self.stats['by_extension'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {ext} | {count} |")
        lines.append("")
        
        # 最大文件
        lines.append("## 📄 最大文件 (Top 10)")
        lines.append("")
        lines.append("| 文件 | 大小 | 行数 | 语言 |")
        lines.append("|------|------|------|------|")
        for f in self.stats['largest_files']:
            size_kb = f['size'] / 1024
            lines.append(f"| `{f['path']}` | {size_kb:.1f} KB | {f['lines']:,} | {f['language']} |")
        lines.append("")
        
        # 所有文件列表
        lines.append("## 📂 所有文件列表")
        lines.append("")
        lines.append("| 文件 | 扩展名 | 语言 | 行数 |")
        lines.append("|------|--------|------|------|")
        for f in self.files:
            lines.append(f"| `{f['path']}` | {f['extension']} | {f['language']} | {f['lines']:,} |")
        lines.append("")
        
        # 文件内容摘要
        lines.append("## 📝 文件内容摘要")
        lines.append("")
        
        for f in self.files:
            lines.append(f"### {f['path']}")
            lines.append("")
            lines.append(f"- **语言**: {f['language']}")
            lines.append(f"- **行数**: {f['lines']:,}")
            lines.append(f"- **大小**: {f['size'] / 1024:.1f} KB")
            lines.append("")
            lines.append("```" + f['language'].lower())
            lines.append(f['preview'])
            lines.append("```")
            lines.append("")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return output_file
    
    def export_all(self, format: str = "all") -> Dict[str, Path]:
        """
        导出所有格式
        
        Args:
            format: 导出格式 ('json', 'md', 'all')
            
        Returns:
            导出的文件路径字典
        """
        results = {}
        
        if format in ['json', 'all']:
            results['json'] = self.export_to_json()
        
        if format in ['md', 'markdown', 'all']:
            results['markdown'] = self.export_to_markdown()
        
        return results
    
    def generate_index_html(self) -> Path:
        """生成HTML索引页面"""
        output_file = self.output_dir / "index.html"
        
        # 使用字符串模板，避免format冲突
        html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码收集报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #fff;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .meta {{
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card .number {{
            font-size: 28px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-card .label {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .code-preview {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 10px 0;
            max-height: 200px;
            overflow-y: auto;
        }}
        .section {{
            margin-top: 30px;
        }}
        .section h2 {{
            font-size: 24px;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }}
        .file-item {{
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 10px;
        }}
        .file-item .file-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .file-item .file-name {{
            font-weight: 500;
            color: #2c3e50;
        }}
        .file-item .file-meta {{
            font-size: 13px;
            color: #7f8c8d;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            background: #3498db;
            color: #fff;
        }}
        .badge-python {{ background: #3572A5; }}
        .badge-javascript {{ background: #f1e05a; color: #333; }}
        .badge-typescript {{ background: #3178c6; }}
        .badge-html {{ background: #e34c26; }}
        .badge-css {{ background: #563d7c; }}
        .badge-json {{ background: #f5a623; }}
        .badge-go {{ background: #00ADD8; }}
        .badge-rust {{ background: #dea584; }}
        .badge-java {{ background: #b07219; }}
        .badge-default {{ background: #6c757d; }}
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .stats-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 代码收集报告</h1>
        <div class="meta">
            收集时间: {time}<br>
            项目目录: <code>{root_dir}</code>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{total_files}</div>
                <div class="label">总文件数</div>
            </div>
            <div class="stat-card">
                <div class="number">{total_lines}</div>
                <div class="label">总代码行数</div>
            </div>
            <div class="stat-card">
                <div class="number">{total_chars}</div>
                <div class="label">总字符数</div>
            </div>
            <div class="stat-card">
                <div class="number">{languages}</div>
                <div class="label">编程语言</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 语言分布</h2>
            <table>
                <tr><th>语言</th><th>文件数</th></tr>
                {language_rows}
            </table>
        </div>
        
        <div class="section">
            <h2>📁 扩展名分布</h2>
            <table>
                <tr><th>扩展名</th><th>文件数</th></tr>
                {extension_rows}
            </table>
        </div>
        
        <div class="section">
            <h2>📄 最大文件</h2>
            <table>
                <tr><th>文件</th><th>大小</th><th>行数</th><th>语言</th></tr>
                {largest_rows}
            </table>
        </div>
        
        <div class="section">
            <h2>📂 所有文件</h2>
            {file_list}
        </div>
    </div>
</body>
</html>'''
        
        # 准备数据
        languages = len(self.stats['by_language'])
        
        language_rows = '\n'.join([
            f"<tr><td>{lang}</td><td>{count}</td></tr>"
            for lang, count in sorted(self.stats['by_language'].items(), key=lambda x: x[1], reverse=True)
        ])
        
        extension_rows = '\n'.join([
            f"<tr><td>{ext}</td><td>{count}</td></tr>"
            for ext, count in sorted(self.stats['by_extension'].items(), key=lambda x: x[1], reverse=True)
        ])
        
        largest_rows = '\n'.join([
            f"<tr><td><code>{f['path']}</code></td><td>{f['size'] / 1024:.1f} KB</td><td>{f['lines']:,}</td><td>{f['language']}</td></tr>"
            for f in self.stats['largest_files']
        ])
        
        file_items = []
        for f in self.files:
            lang_lower = f['language'].lower()
            if lang_lower in ['python', 'javascript', 'typescript', 'html', 'css', 'json', 'go', 'rust', 'java']:
                badge_class = f"badge-{lang_lower}"
            else:
                badge_class = 'badge-default'
            
            # 转义HTML特殊字符
            preview = f['preview'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            file_items.append(f'''
            <div class="file-item">
                <div class="file-header">
                    <span class="file-name"><code>{f['path']}</code></span>
                    <span class="file-meta">{f['lines']:,} 行 · {f['size'] / 1024:.1f} KB · <span class="badge {badge_class}">{f['language']}</span></span>
                </div>
                <div class="code-preview">{preview}</div>
            </div>
            ''')
        
        file_list = '\n'.join(file_items)
        
        # 格式化数字
        total_lines = f"{self.stats['total_lines']:,}"
        total_chars = f"{self.stats['total_characters']:,}"
        
        html = html_template.format(
            time=datetime.now().isoformat(),
            root_dir=self.root_dir,
            total_files=self.stats['total_files'],
            total_lines=total_lines,
            total_chars=total_chars,
            languages=languages,
            language_rows=language_rows,
            extension_rows=extension_rows,
            largest_rows=largest_rows,
            file_list=file_list
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_file


def collect_and_export(root_dir: str = ".", output_dir: str = "collected_code", 
                       format: str = "all", generate_html: bool = True):
    """
    便捷函数：收集并导出代码
    
    Args:
        root_dir: 项目根目录
        output_dir: 输出目录
        format: 导出格式 ('json', 'md', 'all')
        generate_html: 是否生成HTML报告
    """
    collector = CodeCollector(root_dir, output_dir)
    
    print("🔍 正在收集代码文件...")
    stats = collector.collect()
    
    print(f"\n📊 收集完成!")
    print(f"   总文件数: {stats['total_files']}")
    print(f"   总代码行数: {stats['total_lines']:,}")
    print(f"   总字符数: {stats['total_characters']:,}")
    
    print(f"\n📝 导出文件...")
    results = collector.export_all(format)
    
    for name, path in results.items():
        print(f"   ✅ {name}: {path}")
    
    if generate_html:
        html_path = collector.generate_index_html()
        print(f"   ✅ HTML: {html_path}")
    
    print(f"\n✅ 完成! 输出目录: {output_dir}")
    return stats, results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="代码收集器")
    parser.add_argument("--root", "-r", default=".", help="项目根目录")
    parser.add_argument("--output", "-o", default="collected_code", help="输出目录")
    parser.add_argument("--format", "-f", choices=['json', 'md', 'all'], default='all', help="导出格式")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    
    args = parser.parse_args()
    
    collect_and_export(
        root_dir=args.root,
        output_dir=args.output,
        format=args.format,
        generate_html=not args.no_html
    )