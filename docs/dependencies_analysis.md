# 项目依赖分析文档

## 📋 依赖包分类说明

### 🧪 测试框架核心

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `pytest` | 7.0.0 | 主要测试框架 | ✅ 必需 |
| `pytest-html` | 4.0.0 | HTML报告生成 | ✅ 必需 |
| `pytest-cov` | 4.0.0 | 代码覆盖率测试 | ✅ 必需 |
| `pytest-xdist` | 3.0.0 | 并行测试执行 | ✅ 必需 |
| `allure-pytest` | 2.13.0 | Allure报告集成 | ✅ 必需 |
| `allure-commandline` | 2.20.0 | Allure命令行工具 | ✅ 必需 |

### 🌐 HTTP请求

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `requests` | 2.28.0 | HTTP请求库 | ✅ 必需 |

### 📄 配置文件处理

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `PyYAML` | 6.0.0 | YAML配置文件解析 | ✅ 必需 |

### 📊 数据处理

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `pandas` | 1.5.0 | 数据处理和分析 | ✅ 必需 |
| `openpyxl` | 3.0.0 | Excel文件读写 | ✅ 必需 |

### 🗄️ 数据库驱动

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `pymysql` | 1.0.0 | MySQL数据库连接 | ✅ 必需 |
| `psycopg2-binary` | 2.9.0 | PostgreSQL数据库连接 | ✅ 必需 |
| `redis` | 4.0.0 | Redis缓存连接 | ✅ 必需 |

### 🔧 ORM支持

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `SQLAlchemy` | 2.0.0 | 数据库ORM框架 | ✅ 必需 |

### 📨 消息队列

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `pika` | 1.3.0 | RabbitMQ客户端 | ✅ 必需 |
| `rocketmq-client-python` | 2.0.0 | RocketMQ客户端 | ✅ 必需 |

### 🏷️ 类型提示支持

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `typing-extensions` | 4.0.0 | Python类型提示扩展 | ✅ 必需 |

### 🛠️ 开发工具（可选）

| 包名 | 最低版本 | 用途 | 必需性 |
|------|----------|------|--------|
| `black` | 22.0.0 | 代码格式化工具 | ⚪ 可选 |
| `flake8` | 5.0.0 | 代码风格检查 | ⚪ 可选 |
| `mypy` | 1.0.0 | 静态类型检查 | ⚪ 可选 |

## 🔍 版本兼容性说明

### Python版本要求
- **支持版本**: Python 3.8.0 - 3.8.10
- **推荐版本**: Python 3.8.10
- **不支持**: Python 3.7.x及以下，Python 3.9.x及以上

### 版本选择原因

#### pytest 7.x
- 与Python 3.8.10最佳兼容
- 支持现代pytest功能
- 与所有插件兼容性良好

#### requests 2.28+
- 支持现代HTTP功能
- 安全性更新
- 与Python 3.8兼容

#### PyYAML 6.x
- 稳定的YAML处理
- 支持复杂配置结构
- 性能优化

#### pandas 1.5+
- 与Python 3.8.10兼容
- 支持现代数据处理功能
- 性能优化

## 📦 安装指南

### 完整安装
```bash
pip install -r requirements_complete.txt
```

### 使用国内镜像源
```bash
pip install -r requirements_complete.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 分步安装
```bash
# 1. 测试框架
pip install pytest>=7.0.0 pytest-html>=4.0.0 pytest-cov>=4.0.0 pytest-xdist>=3.0.0

# 2. 报告工具
pip install allure-pytest>=2.13.0 allure-commandline>=2.20.0

# 3. HTTP和配置
pip install requests>=2.28.0 PyYAML>=6.0.0

# 4. 数据处理
pip install pandas>=1.5.0 openpyxl>=3.0.0

# 5. 数据库
pip install pymysql>=1.0.0 psycopg2-binary>=2.9.0 redis>=4.0.0 SQLAlchemy>=2.0.0

# 6. 消息队列
pip install pika>=1.3.0 rocketmq-client-python>=2.0.0

# 7. 类型支持
pip install typing-extensions>=4.0.0
```

## 🔧 开发环境设置

### 可选开发工具
```bash
# 代码格式化
pip install black>=22.0.0

# 代码风格检查
pip install flake8>=5.0.0

# 静态类型检查
pip install mypy>=1.0.0
```

## ⚠️ 注意事项

1. **Python版本**: 严格使用Python 3.8.x版本
2. **虚拟环境**: 建议使用虚拟环境隔离依赖
3. **依赖冲突**: 如遇依赖冲突，优先使用项目指定的版本
4. **系统依赖**: 某些包可能需要系统级依赖（如编译工具）

## 🔄 更新策略

### 定期更新
- 每月检查安全更新
- 每季度评估版本兼容性
- 每年评估主要版本升级

### 更新流程
1. 在测试环境中验证新版本
2. 运行完整的测试套件
3. 检查功能兼容性
4. 更新文档和配置

## 📊 依赖使用统计

根据代码分析，各依赖包的使用情况：

- **pytest**: 所有测试文件
- **allure**: 报告生成和装饰器
- **requests**: HTTP工具类
- **PyYAML**: 配置文件处理
- **pandas**: 数据处理和Excel操作
- **SQLAlchemy**: 数据库ORM操作
- **pymysql/psycopg2**: 数据库连接
- **redis**: 缓存操作
- **pika/rocketmq**: 消息队列操作 