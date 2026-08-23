"""
命令行工具
"""

import argparse
import sys
from pathlib import Path
import json

try:
    from rich.console import Console
    from rich.table import Table
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # 创建简单的替代
    class Console:
        def print(self, *args, **kwargs):
            print(*args)

from ..core.executor import SkillExecutor


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="MarkFlow - 从Markdown到可执行技能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  markflow build weather.md                    # 从Markdown构建技能
  markflow list                               # 列出所有技能
  markflow execute WeatherFetcher city=Beijing # 执行技能
  markflow generate -t data -n data_cleaner   # 从模板生成
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # build命令
    build_parser = subparsers.add_parser("build", help="从Markdown构建技能")
    build_parser.add_argument("file", help="Markdown文件路径")
    build_parser.add_argument("--no-save", action="store_true", help="不保存到文件")
    build_parser.add_argument("--output", "-o", default="./skills", help="输出目录")
    
    # execute命令
    exec_parser = subparsers.add_parser("execute", help="执行技能")
    exec_parser.add_argument("skill", help="技能名称")
    exec_parser.add_argument("params", nargs="*", help="参数 key=value")
    
    # list命令
    subparsers.add_parser("list", help="列出所有技能")
    
    # info命令
    info_parser = subparsers.add_parser("info", help="显示技能详情")
    info_parser.add_argument("skill", help="技能名称")
    
    # generate命令
    gen_parser = subparsers.add_parser("generate", help="从模板生成技能")
    gen_parser.add_argument("--template", "-t", choices=["basic", "data", "api", "automation"],
                           default="basic", help="模板类型")
    gen_parser.add_argument("--name", "-n", required=True, help="技能名称")
    gen_parser.add_argument("--description", "-d", default="", help="技能描述")
    gen_parser.add_argument("--output", "-o", default="./skills", help="输出目录")
    
    # remove命令
    remove_parser = subparsers.add_parser("remove", help="删除技能")
    remove_parser.add_argument("skill", help="技能名称")
    
    args = parser.parse_args()
    
    if RICH_AVAILABLE:
        console = Console()
    else:
        console = Console()
    
    executor = SkillExecutor()
    
    if args.command == "build":
        build_skill(args, executor, console)
    elif args.command == "execute":
        # 获取技能名称
        skill_name = getattr(args, 'skill', None)
        if not skill_name:
            console.print("[red]❌ 请指定技能名称[/red]")
            return
        
        # 提取参数
        kwargs = {k: v for k, v in vars(args).items() 
                  if k not in ['command', 'skill', 'func'] and v is not None}
        
        execute_skill(skill_name, **kwargs)
    elif args.command == "list":
        list_skills(executor, console)
    elif args.command == "info":
        show_info(args, executor, console)
    elif args.command == "generate":
        generate_skill(args, executor, console)
    elif args.command == "remove":
        remove_skill(args, executor, console)
    else:
        parser.print_help()


def build_skill(args, executor, console):
    """构建技能"""
    file_path = Path(args.file)
    
    if not file_path.exists():
        console.print("[red]错误: 文件不存在: {}[/red]".format(file_path))
        sys.exit(1)
    
    try:
        result = executor.build_from_file(file_path, save=not args.no_save)
        
        console.print("\n[bold green]✅ 技能构建成功![/bold green]")
        console.print("  名称: [cyan]{}[/cyan]".format(result['name']))
        console.print("  类名: [cyan]{}[/cyan]".format(result['class_name']))
        console.print("  版本: [cyan]{}[/cyan]".format(result['metadata'].get('version', '1.0.0')))
        
        if result['metadata'].get('dependencies'):
            deps = ", ".join(result['metadata']['dependencies'])
            console.print("  依赖: [yellow]{}[/yellow]".format(deps))
        
        if not args.no_save:
            code_file = executor.registry.storage_dir / "{}.py".format(result['class_name'])
            console.print("  保存位置: [blue]{}[/blue]".format(code_file))
        
        if RICH_AVAILABLE:
            console.print("\n[bold]代码预览:[/bold]")
            syntax = Syntax(result['code'][:500] + "...", "python", theme="monokai")
            console.print(syntax)
        
    except Exception as e:
        console.print("[red]❌ 构建失败: {}[/red]".format(e))
        sys.exit(1)


# markflow/cli/commands.py
# 找到 execute 命令部分，更新技能加载逻辑

# 找到类似这样的代码：
def execute_skill(skill_name, **kwargs):
    """执行技能"""
    import importlib
    import sys
    from pathlib import Path
    
    # 确保项目根目录在 sys.path 中
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        # 尝试从新的 skills 目录导入
        module = importlib.import_module(f"skills.{skill_name}.skill")
        
        # 查找技能类
        skill_class = None
        for attr_name in dir(module):
            if attr_name.endswith("Generator") or \
               attr_name.endswith("Assistant") or \
               attr_name.endswith("Toolbox") or \
               attr_name.endswith("Viewer"):
                skill_class = getattr(module, attr_name)
                break
        
        if not skill_class:
            print(f"❌ 未找到技能类: {skill_name}")
            return False
        
        # 创建实例并执行
        skill = skill_class()
        
        # 如果 skill 有 execute 方法
        if hasattr(skill, 'execute'):
            result = skill.execute(**kwargs)
            print(f"✅ 执行成功")
            return result
        else:
            print(f"❌ 技能 {skill_name} 没有 execute 方法")
            return False
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False    

def list_skills(executor, console):
    """列出所有技能"""
    skill_dir = Path("./skills")
    if skill_dir.exists():
        executor.registry.load_from_directory(skill_dir)
    
    skills = executor.list_skills()
    
    if not skills:
        console.print("[yellow]未找到任何技能[/yellow]")
        console.print("使用 [cyan]markflow build <file>[/cyan] 创建技能")
        return
    
    if RICH_AVAILABLE:
        table = Table(title="📚 已注册技能")
        table.add_column("名称", style="cyan", no_wrap=True)
        table.add_column("描述", style="green")
        table.add_column("版本", style="yellow")
        table.add_column("依赖", style="magenta")
        table.add_column("标签", style="blue")
        
        for name, metadata in skills.items():
            table.add_row(
                name,
                metadata.get('description', '')[:50],
                metadata.get('version', '1.0.0'),
                ", ".join(metadata.get('dependencies', [])),
                ", ".join(metadata.get('tags', []))
            )
        
        console.print(table)
    else:
        console.print("已注册技能:")
        for name, metadata in skills.items():
            console.print("  - {}: {}".format(name, metadata.get('description', '')[:50]))
    
    console.print("\n总计: [bold]{}[/bold] 个技能".format(len(skills)))


def show_info(args, executor, console):
    """显示技能详情"""
    skill_dir = Path("./skills")
    if skill_dir.exists():
        executor.registry.load_from_directory(skill_dir)
    
    info = executor.get_skill_info(args.skill)
    
    if not info:
        console.print("[red]技能 '{}' 不存在[/red]".format(args.skill))
        sys.exit(1)
    
    console.print("\n[bold cyan]📋 {}[/bold cyan]".format(args.skill))
    console.print("  描述: {}".format(info.get('description', '')))
    console.print("  版本: {}".format(info.get('version', '1.0.0')))
    
    if info.get('tags'):
        console.print("  标签: {}".format(', '.join(info['tags'])))
    
    if info.get('dependencies'):
        console.print("  依赖: {}".format(', '.join(info['dependencies'])))
    
    if info.get('inputs'):
        console.print("\n[bold]输入参数:[/bold]")
        for inp in info['inputs']:
            console.print("  - {} ({}): {}".format(
                inp['name'], 
                inp.get('type', 'string'), 
                inp.get('description', '')
            ))
    
    if info.get('outputs'):
        console.print("\n[bold]输出:[/bold]")
        for out in info['outputs']:
            console.print("  - {}: {}".format(out['name'], out.get('description', '')))
    
    if info.get('config'):
        console.print("\n[bold]配置:[/bold]")
        for key, value in info['config'].items():
            console.print("  - {}: {}".format(key, value))


def generate_skill(args, executor, console):
    """从模板生成技能"""
    skill_name = args.name
    skill_title = skill_name.title()
    
    templates = {
        'basic': {
            'description': '基础技能模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
执行基本功能

## 输入
- input_data: string: 输入数据

## 输出
- result: 执行结果

## 步骤
1. 处理输入数据
2. 执行主要功能
3. 返回结果

## 依赖

## 示例
```python
skill = {title}()
result = skill.execute(input_data="test")
print(result)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' 基础技能',
                title=skill_title
            )
        },
        'data': {
            'description': '数据处理模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
处理和分析数据

## 输入
- data_source: string: 数据源路径
- method: string: 处理方法
- output: string: 输出路径

## 输出
- processed_data: 处理后的数据
- report: 处理报告

## 步骤
1. 读取数据源
2. 数据清洗
3. 数据处理
4. 生成报告
5. 保存结果

## 依赖
- pandas
- numpy

## 示例
```python
skill = {title}()
result = skill.execute(
    data_source="data.csv",
    method="clean",
    output="result.csv"
)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' 数据处理技能',
                title=skill_title
            )
        },
        'api': {
            'description': 'API客户端模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
调用外部API服务

## 输入
- endpoint: string: API端点
- method: string: HTTP方法 (GET, POST)
- params: json: 请求参数

## 输出
- response: API响应数据
- status_code: HTTP状态码

## 步骤
1. 构建请求
2. 发送请求
3. 处理响应
4. 返回数据

## 依赖
- requests

## 示例
```python
skill = {title}()
result = skill.execute(
    endpoint="/api/data",
    method="GET",
    params={{'page': 1}}
)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' API客户端',
                title=skill_title
            )
        },
        'automation': {
            'description': '自动化任务模板',
            'markdown': """# {name}

## 描述
{description}

## 目的
自动化执行重复性任务

## 输入
- schedule: string: 调度配置
- target: string: 目标
- action: string: 执行动作

## 输出
- task_id: 任务ID
- status: 任务状态

## 步骤
1. 解析任务配置
2. 执行任务
3. 记录日志
4. 返回结果

## 依赖
- schedule

## 示例
```python
skill = {title}()
result = skill.execute(
    schedule="daily",
    target="report",
    action="generate"
)
```""".format(
                name=skill_name,
                description=args.description or skill_name + ' 自动化任务',
                title=skill_title
            )
        }
    }
    
    template = templates.get(args.template, templates['basic'])
    result = executor.build_from_markdown(template['markdown'])
    
    console.print("\n[bold green]✅ 技能生成成功![/bold green]")
    console.print("  名称: [cyan]{}[/cyan]".format(result['name']))
    console.print("  模板: [yellow]{}[/yellow] ({})".format(
        args.template, 
        template['description']
    ))
    console.print("  类名: [cyan]{}[/cyan]".format(result['class_name']))
    
    code_file = executor.registry.storage_dir / "{}.py".format(result['class_name'])
    console.print("  保存位置: [blue]{}[/blue]".format(code_file))


def remove_skill(args, executor, console):
    """删除技能"""
    skill_dir = Path("./skills")
    if not skill_dir.exists():
        console.print("[yellow]没有找到技能目录[/yellow]")
        return
    
    code_file = skill_dir / "{}.py".format(args.skill)
    meta_file = skill_dir / "{}.meta.json".format(args.skill)
    
    removed = []
    if code_file.exists():
        code_file.unlink()
        removed.append(str(code_file))
    
    if meta_file.exists():
        meta_file.unlink()
        removed.append(str(meta_file))
    
    if removed:
        console.print("[green]✅ 已删除: {}[/green]".format(', '.join(removed)))
        executor.registry.unregister(args.skill)
    else:
        console.print("[yellow]未找到技能: {}[/yellow]".format(args.skill))


if __name__ == "__main__":
    main()