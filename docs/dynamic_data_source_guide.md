# 动态数据源使用指南

## 概述

本项目支持动态加载多种数据源，包括文件、数据库、Redis等，让测试用例能够灵活地从不同数据源获取测试数据。

## 支持的数据源类型

### 1. 文件数据源
- **YAML文件**: `caseparams/test_chat_gateway.yaml`
- **CSV文件**: `caseparams/test_data.csv`
- **JSON文件**: `caseparams/test_data.json`
- **Excel文件**: `caseparams/test_data.xlsx`

### 2. 数据库数据源
- **MySQL**: 支持查询和缓存
- **PostgreSQL**: 支持查询和缓存
- **SQLite**: 支持查询和缓存
- **Redis**: 支持键值存储

### 3. 混合数据源
- 文件 + 数据库
- 数据库 + Redis
- 多数据库组合

## 配置数据库连接

### 数据库配置文件
编辑 `conf/database.yaml` 文件：

```yaml
database:
  default_type: mysql
  
  mysql:
    dev:
      host: 127.0.0.1
      port: 3306
      user: dev_user
      password: dev_pass
      database: dev_db
      charset: utf8mb4
      autocommit: true
    test:
      host: 192.168.1.100
      port: 3306
      user: test_user
      password: test_pass
      database: test_db
      charset: utf8mb4
      autocommit: true
```

## 使用方法

### 1. 基础文件数据源

```python
from common.get_caseparams import read_test_data

# 从YAML文件加载数据
test_data = read_test_data('caseparams/test_chat_gateway.yaml')

# 从CSV文件加载数据
csv_data = read_test_data('caseparams/test_data.csv')

# 从JSON文件加载数据
json_data = read_test_data('caseparams/test_data.json')
```

### 2. 数据库数据源

#### 直接使用数据库查询
```python
from common.data_source import get_test_data_from_db

# 从数据库加载测试数据
sql = "SELECT * FROM test_cases WHERE status = 'active'"
db_data = get_test_data_from_db(
    sql=sql,
    db_type='mysql',
    env='test',
    cache_key='active_cases'
)
```

#### 使用db://格式
```python
from common.get_caseparams import read_test_data

# 使用db://格式指定数据库查询
db_config = "db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' LIMIT 5?cache_key=active_cases"
test_data = read_test_data(db_config)
```

### 3. Redis数据源

```python
from common.data_source import get_redis_value, set_redis_value

# 设置Redis数据
set_redis_value('test:user:123', '{"user_id": 123, "username": "test_user"}', env='test', expire=3600)

# 获取Redis数据
user_data = get_redis_value('test:user:123', env='test')
```

### 4. 混合数据源

```python
from common.get_caseparams import read_test_data
from common.data_source import get_test_data_from_db

# 从文件加载基础配置
file_data = read_test_data('caseparams/test_chat_gateway.yaml')

# 从数据库加载动态数据
sql = "SELECT user_id, username FROM users WHERE is_active = 1"
db_data = get_test_data_from_db(sql, 'mysql', 'test', 'active_users')

# 合并数据源
combined_data = []
for file_case in file_data:
    for db_case in db_data:
        combined_case = file_case.copy()
        combined_case.update(db_case)
        combined_data.append(combined_case)
```

## 测试用例示例

### 1. 基础测试用例

```python
import pytest
from common.get_caseparams import read_test_data

# 读取测试数据
test_data = read_test_data('caseparams/test_chat_gateway.yaml')

@pytest.mark.parametrize("case", test_data)
def test_chat_gateway(case):
    url = case['url']
    method = case['method'].upper()
    params = case.get('params', {})
    expected = case.get('expected_result', {})
    
    # 执行测试逻辑
    # ...
```

### 2. 数据库驱动测试用例

```python
import pytest
from common.data_source import get_test_data_from_db

def test_with_db_data():
    # 从数据库获取测试数据
    sql = "SELECT * FROM test_cases WHERE status = 'active'"
    test_cases = get_test_data_from_db(sql, 'mysql', 'test', 'active_cases')
    
    for case in test_cases:
        # 执行测试逻辑
        # ...
```

### 3. 动态参数测试用例

```python
import pytest
from common.data_source import get_redis_value, set_redis_value

def test_with_dynamic_params():
    # 从Redis获取动态参数
    dynamic_params = get_redis_value('test:dynamic:params', env='test')
    
    if not dynamic_params:
        # 设置默认参数
        default_params = {'user_id': 123, 'action': 'login'}
        set_redis_value('test:dynamic:params', str(default_params), env='test')
        dynamic_params = default_params
    
    # 使用动态参数执行测试
    # ...
```

## 高级功能

### 1. 缓存策略

```python
# 使用缓存的数据源
cached_data = get_test_data_from_db(
    sql="SELECT * FROM large_dataset",
    db_type='mysql',
    env='test',
    cache_key='large_dataset_cache'
)
```

### 2. 多环境支持

```python
# 根据环境加载不同的数据源
environments = ['dev', 'test', 'prod']
for env in environments:
    data = get_test_data_from_db(
        sql=f"SELECT * FROM test_cases WHERE env = '{env}'",
        db_type='mysql',
        env=env
    )
```

### 3. 错误处理和回退

```python
def load_test_data_with_fallback():
    try:
        # 尝试从数据库加载
        return get_test_data_from_db("SELECT * FROM test_cases", 'mysql', 'test')
    except Exception as e:
        # 回退到文件数据源
        return read_test_data('caseparams/test_chat_gateway.yaml')
```

## 配置示例

### 1. 数据库表结构示例

```sql
-- 测试用例表
CREATE TABLE test_cases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(50) NOT NULL,
    description TEXT,
    url VARCHAR(255),
    method VARCHAR(10),
    params JSON,
    expected_result JSON,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表
CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- 测试场景表
CREATE TABLE test_scenarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    test_name VARCHAR(100),
    category VARCHAR(50),
    input_data JSON,
    expected_result JSON,
    status ENUM('active', 'inactive') DEFAULT 'active'
);
```

### 2. Redis键值示例

```python
# 测试配置
set_redis_value('test:config:timeout', '30', env='test')
set_redis_value('test:config:retries', '3', env='test')

# 动态参数
set_redis_value('test:dynamic:user_id', '123', env='test')
set_redis_value('test:dynamic:session_id', 'abc123', env='test')

# 缓存数据
set_redis_value('test:cache:user_profiles', json.dumps(user_profiles), env='test', expire=3600)
```

## 最佳实践

### 1. 数据源选择
- **静态数据**: 使用文件数据源
- **动态数据**: 使用数据库数据源
- **配置数据**: 使用Redis数据源
- **混合场景**: 使用混合数据源

### 2. 性能优化
- 使用缓存减少数据库查询
- 批量处理大量数据
- 合理设置缓存过期时间

### 3. 错误处理
- 实现数据源回退机制
- 记录详细的错误日志
- 提供默认测试数据

### 4. 维护性
- 使用有意义的缓存键名
- 定期清理过期缓存
- 监控数据源连接状态

## 故障排除

### 1. 数据库连接失败
- 检查数据库配置是否正确
- 确认数据库服务是否运行
- 验证网络连接

### 2. Redis连接失败
- 检查Redis服务是否运行
- 验证Redis配置
- 确认网络连接

### 3. 数据格式错误
- 检查SQL查询语法
- 验证JSON格式
- 确认字段映射

### 4. 缓存问题
- 清理过期缓存
- 检查缓存键名
- 验证缓存配置

## 扩展开发

### 1. 添加新的数据源类型
```python
class CustomDataSource:
    def __init__(self, config):
        self.config = config
    
    def load_data(self):
        # 实现数据加载逻辑
        pass
```

### 2. 自定义缓存策略
```python
def custom_cache_strategy(data, cache_key, ttl):
    # 实现自定义缓存逻辑
    pass
```

### 3. 数据转换器
```python
def data_transformer(raw_data, target_format):
    # 实现数据格式转换
    pass
```

## 总结

动态数据源功能为测试框架提供了强大的数据管理能力，支持多种数据源类型，实现了测试数据的灵活配置和动态加载。通过合理使用这些功能，可以大大提高测试的灵活性和可维护性。 