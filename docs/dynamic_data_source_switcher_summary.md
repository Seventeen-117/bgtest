# 动态数据源切换功能总结

## 功能概述

我已经为你的项目实现了一个完整的动态数据源切换功能，允许你在测试用例中灵活地切换不同的数据源。这个功能特别适用于需要在同一个测试用例中使用多个数据源的场景。

## 实现的功能

### 1. 核心功能
- ✅ **多数据源支持**: 文件、数据库、Redis
- ✅ **简单配置格式**: 使用字符串配置，易于理解和使用
- ✅ **装饰器支持**: 使用 `@switch_data_source` 装饰器
- ✅ **上下文管理器**: 使用 `with_data_source()` 临时切换
- ✅ **自动缓存管理**: 支持数据缓存，提高性能
- ✅ **切换历史记录**: 记录所有数据源切换操作
- ✅ **错误处理**: 完善的错误处理和回退机制

### 2. 配置格式

#### 文件数据源
```python
"caseparams/test_chat_gateway.yaml"
"file://caseparams/test_chat_gateway.yaml"
```

#### 数据库数据源
```python
"db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' LIMIT 5?cache_key=active_cases"
```

#### Redis数据源
```python
"redis://test/test:user:123"
```

## 使用方法

### 1. 基础切换
```python
from common.dynamic_data_source_switcher import data_source_switcher, get_data_from_current_source

# 切换到文件数据源
success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
if success:
    data = get_data_from_current_source()
    print(f"获取到 {len(data)} 条数据")
```

### 2. 使用装饰器
```python
from common.dynamic_data_source_switcher import switch_data_source

@switch_data_source("caseparams/test_chat_gateway.yaml")
def test_with_file_data():
    data = get_data_from_current_source()
    assert len(data) > 0
```

### 3. 使用上下文管理器
```python
from common.dynamic_data_source_switcher import with_data_source

def test_temporary_switch():
    with with_data_source("db://mysql/test/SELECT * FROM test_cases LIMIT 3") as switcher:
        data = get_data_from_current_source()
        print(f"临时获取到 {len(data)} 条数据")
    # 数据源自动恢复
```

## 实际应用场景

### 场景1: 多环境测试
```python
def test_multi_environment():
    environments = ['dev', 'test', 'prod']
    
    for env in environments:
        db_config = f"db://mysql/{env}/SELECT * FROM test_cases WHERE env = '{env}'"
        success = data_source_switcher.switch_to(db_config)
        
        if success:
            data = get_data_from_current_source()
            # 执行环境特定的测试
            for test_case in data:
                # 测试逻辑
                pass
```

### 场景2: 数据源组合
```python
def test_data_combination():
    # 从文件获取基础配置
    data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
    base_config = get_data_from_current_source()
    
    # 从数据库获取动态数据
    data_source_switcher.switch_to("db://mysql/test/SELECT user_id, username FROM users")
    dynamic_data = get_data_from_current_source()
    
    # 组合数据源
    combined_cases = []
    for base_case in base_config:
        for dynamic_case in dynamic_data:
            combined_case = base_case.copy()
            combined_case.update(dynamic_case)
            combined_cases.append(combined_case)
```

### 场景3: 缓存优化
```python
def test_with_cache():
    cached_config = "db://mysql/test/SELECT * FROM large_table?cache_key=large_data"
    success = data_source_switcher.switch_to(cached_config)
    
    if success:
        # 第一次获取（会缓存）
        data1 = get_data_from_current_source()
        
        # 第二次获取（从缓存）
        data2 = get_data_from_current_source()
        
        # 清除缓存
        data_source_switcher.clear_cache("large_data")
```

## 文件结构

### 新增文件
1. **`common/dynamic_data_source_switcher.py`** - 核心功能实现
2. **`testcase/test_dynamic_data_source_switcher.py`** - 完整测试用例
3. **`testcase/test_data_source_switcher_example.py`** - 使用示例
4. **`docs/dynamic_data_source_switcher_guide.md`** - 详细使用指南
5. **`docs/dynamic_data_source_switcher_summary.md`** - 功能总结

### 主要类和方法

#### DynamicDataSourceSwitcher 类
- `switch_to()` - 切换到指定数据源
- `get_data()` - 从当前数据源获取数据
- `execute_query()` - 在当前数据源上执行查询
- `temporary_switch()` - 临时切换数据源
- `get_switch_history()` - 获取切换历史
- `clear_cache()` - 清除缓存

#### 便捷函数
- `switch_data_source()` - 装饰器
- `with_data_source()` - 上下文管理器
- `get_current_data_source()` - 获取当前数据源
- `get_data_from_current_source()` - 从当前数据源获取数据
- `execute_query_on_current_source()` - 在当前数据源上执行查询

## 配置要求

### 1. 数据库配置
确保 `conf/database.yaml` 文件中配置了相应的数据库连接信息：

```yaml
database:
  mysql:
    dev:
      host: 127.0.0.1
      port: 3306
      user: dev_user
      password: dev_pass
      database: dev_db
    test:
      host: 192.168.1.100
      port: 3306
      user: test_user
      password: test_pass
      database: test_db
```

### 2. Redis配置
```yaml
database:
  redis:
    dev:
      host: 127.0.0.1
      port: 6379
      password: dev_redis_pass
      db: 0
    test:
      host: 192.168.1.100
      port: 6379
      password: test_redis_pass
      db: 1
```

## 测试验证

运行以下命令验证功能：

```bash
# 运行基础功能测试
python -m pytest testcase/test_data_source_switcher_example.py::TestDataSourceSwitcherExample::test_basic_usage_example -v -s

# 运行完整测试套件
python -m pytest testcase/test_dynamic_data_source_switcher.py -v -s

# 运行示例测试
python -m pytest testcase/test_data_source_switcher_example.py -v -s
```

## 优势

### 1. 灵活性
- 支持在同一个测试用例中使用多个数据源
- 可以动态切换数据源，无需重启测试
- 支持临时切换，自动恢复原数据源

### 2. 易用性
- 简单的字符串配置格式
- 提供装饰器和上下文管理器
- 与现有框架无缝集成

### 3. 性能优化
- 自动缓存管理
- 支持缓存键和TTL设置
- 减少重复数据查询

### 4. 错误处理
- 完善的错误处理机制
- 支持回退到备用数据源
- 详细的错误日志记录

### 5. 可维护性
- 切换历史记录
- 详细的日志输出
- 模块化设计

## 最佳实践

### 1. 数据源命名规范
```python
# 使用有意义的缓存键
"db://mysql/test/SELECT * FROM test_cases?cache_key=active_test_cases"

# 使用环境前缀
"redis://test/test:user:123"
```

### 2. 错误处理
```python
def safe_switch_data_source(config):
    try:
        success = data_source_switcher.switch_to(config)
        if not success:
            # 尝试回退
            fallback_success = data_source_switcher.switch_to("caseparams/fallback.yaml")
            if not fallback_success:
                raise Exception("所有数据源都不可用")
        return True
    except Exception as e:
        error(f"数据源切换异常: {e}")
        return False
```

### 3. 性能优化
```python
# 使用缓存减少重复查询
cached_config = "db://mysql/test/SELECT * FROM large_table?cache_key=large_data&ttl=3600"

# 批量处理数据
def process_data_in_batches(data, batch_size=100):
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        yield batch
```

### 4. 测试隔离
```python
def test_with_isolated_data_source():
    with with_data_source("db://mysql/test/SELECT * FROM test_cases LIMIT 10") as switcher:
        data = get_data_from_current_source()
        # 执行测试逻辑
        assert len(data) <= 10
```

## 总结

动态数据源切换功能为你的测试框架提供了强大的灵活性，允许你在测试过程中轻松切换不同的数据源。通过合理使用这个功能，你可以：

1. **提高测试灵活性**: 在同一个测试用例中使用多个数据源
2. **支持多环境测试**: 轻松切换不同环境的数据源
3. **实现复杂数据组合**: 组合不同数据源的数据
4. **优化测试性能**: 通过缓存减少重复查询
5. **增强错误处理**: 完善的错误处理和回退机制

这个功能与现有的数据驱动框架完全兼容，可以无缝集成到你的测试项目中。建议在实际使用中根据具体需求选择合适的切换方式，并遵循最佳实践来确保测试的稳定性和可靠性。 