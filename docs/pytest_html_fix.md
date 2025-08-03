# pytest-html 版本兼容性问题解决方案

## 问题描述

在执行测试时遇到以下错误：

```
E:\bgtest\.venv\Lib\site-packages\_pytest\config\__init__.py:325: PluggyTeardownRaisedWarning: A plugin raised an exception during an old-style hookwrapper teardown.
Plugin: helpconfig, Hook: pytest_cmdline_parse
ModuleNotFoundError: No module named 'pytest_html.fixtures'
```

## 问题原因

这个错误是由于 `pytest-html` 版本兼容性问题导致的。在较旧版本的 `pytest-html`（如 3.0.0）中，存在模块导入路径的问题，导致 pytest 无法正确加载 HTML 报告插件。

## 解决方案

### 1. 升级 pytest-html 版本

将 `pytest-html` 从 3.0.0 升级到 4.1.1 或更高版本：

```bash
pip install --upgrade pytest-html
```

### 2. 更新依赖文件

更新 `requirements.txt` 文件中的版本要求：

```txt
pytest-html>=4.0.0,<5.0.0
```

更新 `pyproject.toml` 文件中的版本要求：

```toml
dependencies = [
    "pytest-html>=4.0.0,<5.0.0",
    # ... 其他依赖
]
```

### 3. 验证修复

运行测试确认问题已解决：

```bash
python run.py --help
python run.py --dry-run
python run.py -k "test_allure_simple" --html
```

## 版本兼容性说明

- **pytest-html 3.0.0**: 存在模块导入问题，不推荐使用
- **pytest-html 4.1.1+**: 修复了兼容性问题，推荐使用

## 相关文件

- `requirements.txt`: 项目依赖配置
- `pyproject.toml`: 项目配置文件
- `run.py`: 测试执行脚本

## 注意事项

1. 升级后请确保所有团队成员都更新了虚拟环境中的依赖
2. 如果使用 CI/CD 环境，请确保构建脚本中也更新了依赖版本
3. 建议定期检查依赖包的更新，以获取最新的安全修复和功能改进 