# run.py 使用指南

## 概述

`run.py` 是项目的统一测试执行器，用于执行 `testcase` 目录下的所有测试用例。它提供了丰富的命令行选项和报告生成功能。

## 基本用法

### 执行所有测试
```bash
python run.py
```

### 查看帮助信息
```bash
python run.py --help
```

### 列出可用的测试文件
```bash
python run.py --dry-run
```

## 命令行参数

### 测试选择参数

- `-m, --markers MARKERS`: 只运行指定标记的测试
  ```bash
  python run.py -m "smoke"           # 执行标记为smoke的测试
  python run.py -m "api or unit"     # 执行标记为api或unit的测试
  ```

- `-k, --keyword KEYWORD`: 只运行包含指定关键字的测试
  ```bash
  python run.py -k "login"           # 执行包含login的测试
  python run.py -k "assertion"       # 执行包含assertion的测试
  ```

- `--maxfail MAXFAIL`: 最多失败多少个测试后停止
  ```bash
  python run.py --maxfail 3          # 最多失败3个测试后停止
  ```

### 报告参数

- `--html`: 生成HTML报告
  ```bash
  python run.py --html
  ```

- `--allure`: 生成Allure报告
  ```bash
  python run.py --allure
  ```

- `--coverage`: 生成覆盖率报告
  ```bash
  python run.py --coverage
  ```

### 执行参数

- `--parallel`: 并行执行测试
  ```bash
  python run.py --parallel
  ```

- `--workers WORKERS`: 指定并行工作进程数
  ```bash
  python run.py --workers 4
  ```

- `--dry-run`: 只显示将要执行的测试，不实际执行
  ```bash
  python run.py --dry-run
  ```

## 使用示例

### 1. 基本测试执行
```bash
# 执行所有测试
python run.py

# 执行特定标记的测试
python run.py -m "smoke"

# 执行包含特定关键字的测试
python run.py -k "api"
```

### 2. 生成报告
```bash
# 生成HTML报告
python run.py --html

# 生成Allure报告
python run.py --allure

# 同时生成HTML和Allure报告
python run.py --html --allure

# 生成覆盖率报告
python run.py --coverage
```

### 3. 并行执行
```bash
# 自动检测CPU核心数进行并行执行
python run.py --parallel

# 指定4个工作进程
python run.py --workers 4
```

### 4. 组合使用
```bash
# 执行API测试并生成HTML报告
python run.py -m "api" --html

# 执行包含login的测试，最多失败2个后停止
python run.py -k "login" --maxfail 2

# 并行执行smoke测试并生成Allure报告
python run.py -m "smoke" --parallel --allure
```

## 输出说明

### 执行信息
```
============================================================
测试执行器 - 统一执行testcase目录下的所有测试用例
============================================================
将生成HTML报告: report\test_report_20250802_184949.html
执行目录: testcase
pytest参数: testcase -s -v --tb=short --strict-markers --disable-warnings -k assertion_utils --html=report\test_report_20250802_184949.html --self-contained-html
------------------------------------------------------------
开始执行测试...
```

### 执行结果
```
------------------------------------------------------------
测试执行完成!
执行时间: 0:00:01.824436
退出码: 0
✅ 所有测试通过!
```

### 报告位置
- HTML报告: `report/test_report_YYYYMMDD_HHMMSS.html`
- Allure报告: `report/allure-results-YYYYMMDD_HHMMSS/`
- 覆盖率报告: `report/coverage/index.html`

## 环境要求

### 必需依赖
- Python 3.7+
- pytest
- 项目相关依赖包

### 可选依赖
- `pytest-html`: 用于生成HTML报告
- `allure-pytest`: 用于生成Allure报告
- `pytest-cov`: 用于生成覆盖率报告
- `pytest-xdist`: 用于并行执行测试

### 安装可选依赖
```bash
pip install pytest-html allure-pytest pytest-cov pytest-xdist
```

## 故障排除

### 1. 找不到测试文件
确保 `testcase` 目录存在且包含测试文件。

### 2. 插件未安装警告
如果看到插件未安装的警告，可以安装相应的插件：
```bash
pip install pytest-html allure-pytest pytest-cov pytest-xdist
```

### 3. 测试执行失败
检查：
- 测试环境是否正确配置
- 依赖服务是否启动（如数据库、API服务等）
- 网络连接是否正常

### 4. 并行执行问题
如果并行执行出现问题，可以：
- 使用串行执行：`python run.py`
- 减少工作进程数：`python run.py --workers 2`

## 最佳实践

1. **使用标记组织测试**
   ```python
   @pytest.mark.smoke
   def test_basic_functionality():
       pass
   ```

2. **合理使用关键字过滤**
   ```bash
   python run.py -k "login or auth"
   ```

3. **结合报告功能**
   ```bash
   python run.py -m "smoke" --html --allure
   ```

4. **使用并行执行提高效率**
   ```bash
   python run.py --parallel --workers 4
   ```

5. **设置失败阈值**
   ```bash
   python run.py --maxfail 5
   ```

## 配置文件

`run.py` 会自动读取以下配置文件：
- `pytest.ini`: pytest配置
- `conftest.py`: 测试配置和fixtures
- `requirements.txt`: 项目依赖

## 扩展功能

### 自定义测试标记
在测试文件中使用 `@pytest.mark` 装饰器：
```python
@pytest.mark.smoke
@pytest.mark.api
def test_api_functionality():
    pass
```

### 自定义报告
可以通过修改 `run.py` 中的 `build_pytest_args` 函数来添加更多报告选项。

### 集成CI/CD
可以将 `run.py` 集成到CI/CD流程中：
```yaml
# GitHub Actions示例
- name: Run Tests
  run: python run.py --html --allure
```

## 总结

`run.py` 提供了统一、灵活的测试执行方式，支持多种报告格式和并行执行，是项目测试自动化的重要工具。 