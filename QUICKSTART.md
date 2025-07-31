# PythonProject 快速开始指南

## 🚀 5分钟快速开始

### 前提条件

- Python 3.8.10（必须）
- pip（Python包管理器）
- 网络连接

### 步骤1：检查Python版本

```bash
python --version
```

**期望输出**：`Python 3.8.10`

如果版本不匹配，请参考 [Python版本管理指南](PYTHON_VERSION_GUIDE.md)

### 步骤2：运行环境检查

```bash
python check_environment.py
```

### 步骤3：安装依赖

```bash
# 快速安装（推荐）
python quick_install.py

# 或完整安装
python install_dependencies.py
```

### 步骤4：运行测试

```bash
python run.py
```

### 步骤5：查看结果

- 测试报告：`report/` 目录
- 日志文件：`log/` 目录

## 📁 项目结构

```
PythonProject/
├── caseparams/          # 测试数据
├── common/              # 核心模块
├── conf/                # 配置文件
├── testcase/            # 测试用例
├── utils/               # 工具类
├── log/                 # 日志目录
├── report/              # 报告目录
├── requirements.txt     # 依赖列表
├── run.py              # 运行入口
└── README.md           # 详细文档
```

## 🔧 常用命令

### 环境管理

```bash
# 检查环境
python check_environment.py

# 安装依赖
pip install -r requirements.txt

# 创建虚拟环境
python -m venv venv
```

### 测试执行

```bash
# 运行所有测试
python run.py

# 运行特定测试
pytest testcase/test_http_data.py

# 运行带标记的测试
pytest -m "not slow"
```

### 开发工具

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

## 📖 学习路径

### 1. 基础概念
- 阅读 [README.md](README.md) 了解项目架构
- 查看 [环境配置](README.md#环境配置) 部分

### 2. 配置文件
- `conf/env.yaml` - 环境配置
- `conf/interface_info.yaml` - 接口配置
- `conf/database.yaml` - 数据库配置

### 3. 测试用例
- 查看 `testcase/` 目录中的示例
- 学习数据驱动测试
- 了解断言和验证

### 4. 工具使用
- HTTP工具类：`utils/http_utils.py`
- 数据库工具：`common/requestdb.py`
- JSON工具：`utils/read_jsonfile_utils.py`

## 🐛 故障排除

### 常见错误

1. **Python版本错误**
   ```
   ❌ Python版本不兼容
   ```
   **解决**：安装Python 3.8.10

2. **依赖安装失败**
   ```
   ❌ 依赖安装失败
   ```
   **解决**：使用国内镜像源
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```

3. **配置文件缺失**
   ```
   ❌ 配置文件不存在
   ```
   **解决**：检查 `conf/` 目录下的配置文件

### 获取帮助

- 查看详细文档：[README.md](README.md)
- 环境问题：[PYTHON_VERSION_GUIDE.md](PYTHON_VERSION_GUIDE.md)
- 运行环境检查：`python check_environment.py`

## 🎯 下一步

1. **创建第一个测试用例**
   - 在 `testcase/` 目录创建测试文件
   - 在 `caseparams/` 目录添加测试数据

2. **配置环境**
   - 修改 `conf/env.yaml` 配置测试环境
   - 添加接口配置到 `conf/interface_info.yaml`

3. **集成CI/CD**
   - 配置持续集成
   - 自动化测试执行

4. **扩展功能**
   - 添加自定义断言
   - 集成更多数据库
   - 扩展MQ支持

## 📞 支持

- 查看文档：[README.md](README.md)
- 环境指南：[PYTHON_VERSION_GUIDE.md](PYTHON_VERSION_GUIDE.md)
- 运行检查：`python check_environment.py`

---

**开始您的自动化测试之旅！** 🚀 