# code_reviewer

> AI 代码审查，发现问题和安全风险

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 9
- **函数数**: 1

## 技能描述

AI 代码审查，发现问题和安全风险

## 依赖

```bash
pip install pylint
pip install flake8
pip install radon
pip install ollama
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code_path` | string | `` | 代码文件或目录路径 |
| `language` | string | `python` | 编程语言 (python/js/go) |
| `review_level` | string | `basic` | 审查深度 (basic/deep) |
| `focus` | string | `security` | 审查重点 (security/performance/style) |

## 输出

| 字段 | 说明 |
|------|------|
| `issues` | 发现的问题列表 |
| `suggestions` | 改进建议 |
| `security_risks` | 安全风险警告 |
| `code_score` | 代码质量评分 |

## 使用方法

```bash
python -m markflow.cli.commands execute code_reviewer [参数]
```

### 示例

```bash
python -m markflow.cli.commands execute code_reviewer code_path="your_code_path"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info code_reviewer
```

## 输出位置

生成的输出保存在 `skills/code_reviewer/output/` 目录下。

---

*文档自动生成于 2026-08-23 21:55:01*