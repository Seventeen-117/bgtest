# 动态数据源切换使用指南

## 概述

动态数据源切换功能允许你在测试用例中灵活地切换不同的数据源，包括文件、数据库、Redis等。这个功能特别适用于需要在同一个测试用例中使用多个数据源的场景。

## 功能特性

- ✅ 支持多种数据源类型（文件、数据库、Redis）
- ✅ 简单的字符串配置格式
- ✅ 装饰器和上下文管理器支持
- ✅ 自动缓存管理
- ✅ 切换历史记录
- ✅ 错误处理和验证
- ✅ 与现有框架无缝集成

## 数据源配置格式

### 1. 文件数据源

```python
# 直接文件路径
"caseparams/test_chat_gateway.yaml"

# 或使用file://前缀
"file://caseparams/test_chat_gateway.yaml"
```

### 2. 数据库数据源

```python
# 格式: db://type/env/sql?params
"db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' LIMIT 5?cache_key=active_cases"
```

参数说明：
- `type`: 数据库类型（mysql, postgresql, sqlite）
- `env`: 环境（dev, test, prod）
- `sql`: SQL查询语句
- `cache_key`: 缓存键（可选）

### 3. Redis数据源

```python
# 格式: redis://env/key
"redis://test/test:user:123"
```

参数说明：
- `env`: 环境（dev, test, prod）
- `key`: Redis键名

## 使用方法

### 1. 基础切换

```python
from common.dynamic_data_source_switcher import data_source_switcher, get_data_from_current_source

# 切换到文件数据源
success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
if success:
    data = get_data_from_current_source()
    print(f"获取到 {len(data)} 条数据")

# 切换到数据库数据源
success = data_source_switcher.switch_to("db://mysql/test/SELECT * FROM test_cases LIMIT 5")
if success:
    data = get_data_from_current_source()
    print(f"从数据库获取到 {len(data)} 条数据")
```

### 2. 使用装饰器

```python
from common.dynamic_data_source_switcher import switch_data_source

@switch_data_source("caseparams/test_chat_gateway.yaml")
def test_with_file_data():
    """使用文件数据源的测试"""
    data = get_data_from_current_source()
    assert len(data) > 0

@switch_data_source("db://mysql/test/SELECT * FROM test_cases WHERE status = 'active'")
def test_with_db_data():
    """使用数据库数据源的测试"""
    data = get_data_from_current_source()
    assert len(data) > 0
```

### 3. 使用上下文管理器

```python
from common.dynamic_data_source_switcher import with_data_source

def test_temporary_switch():
    """临时切换数据源"""
    # 记录原始数据源
    original_data = get_data_from_current_source()
    
    # 临时切换到数据库数据源
    with with_data_source("db://mysql/test/SELECT * FROM test_cases LIMIT 3") as switcher:
        db_data = get_data_from_current_source()
        print(f"临时获取到 {len(db_data)} 条数据库数据")
    
    # 数据源已自动恢复
    restored_data = get_data_from_current_source()
    assert restored_data == original_data
```

### 4. 执行查询

```python
from common.dynamic_data_source_switcher import execute_query_on_current_source

# 切换到数据库数据源
data_source_switcher.switch_to("db://mysql/test/SELECT 1 as test")

# 执行查询
result = execute_query_on_current_source("SELECT COUNT(*) as count FROM test_cases")
print(f"查询结果: {result}")

# 切换到Redis数据源
data_source_switcher.switch_to("redis://test/test:user:123")

# 执行Redis查询
result = execute_query_on_current_source("GET test:user:123")
print(f"Redis查询结果: {result}")
```

## 实际应用场景

### 场景1: 多环境测试

```python
def test_multi_environment():
    """多环境数据源测试"""
    environments = ['dev', 'test', 'prod']
    
    for env in environments:
        # 切换到对应环境的数据源
        db_config = f"db://mysql/{env}/SELECT * FROM test_cases WHERE env = '{env}'"
        success = data_source_switcher.switch_to(db_config)
        
        if success:
            data = get_data_from_current_source()
            print(f"环境 {env} 获取到 {len(data)} 条测试用例")
            
            # 执行环境特定的测试
            for test_case in data:
                # 执行测试逻辑
                pass
```

### 场景2: 数据源组合测试

```python
def test_data_source_combination():
    """数据源组合测试"""
    # 从文件获取基础配置
    data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
    base_config = get_data_from_current_source()
    
    # 从数据库获取动态数据
    data_source_switcher.switch_to("db://mysql/test/SELECT user_id, username FROM users WHERE is_active = 1")
    dynamic_data = get_data_from_current_source()
    
    # 组合数据源
    combined_test_cases = []
    for base_case in base_config:
        for dynamic_case in dynamic_data:
            combined_case = base_case.copy()
            combined_case.update(dynamic_case)
            combined_test_cases.append(combined_case)
    
    print(f"生成了 {len(combined_test_cases)} 个组合测试用例")
```

### 场景3: 缓存策略测试

```python
def test_cache_strategy():
    """缓存策略测试"""
    # 使用缓存的数据源
    cached_config = "db://mysql/test/SELECT * FROM large_dataset?cache_key=large_data&ttl=3600"
    success = data_source_switcher.switch_to(cached_config)
    
    if success:
        # 第一次获取（会缓存）
        start_time = time.time()
        data1 = get_data_from_current_source()
        first_time = time.time() - start_time
        
        # 第二次获取（从缓存）
        start_time = time.time()
        data2 = get_data_from_current_source()
        second_time = time.time() - start_time
        
        print(f"首次获取耗时: {first_time:.4f}秒")
        print(f"缓存获取耗时: {second_time:.4f}秒")
        print(f"性能提升: {((first_time - second_time) / first_time * 100):.2f}%")
```

### 场景4: 错误处理和回退

```python
def test_error_handling_and_fallback():
    """错误处理和回退机制"""
    # 尝试切换到可能不存在的数据库
    success = data_source_switcher.switch_to("db://invalid_db/test/SELECT * FROM test_cases")
    
    if not success:
        # 回退到文件数据源
        fallback_success = data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
        
        if fallback_success:
            data = get_data_from_current_source()
            print(f"使用回退数据源获取到 {len(data)} 条数据")
        else:
            raise Exception("所有数据源都不可用")
```

## 高级功能

### 1. 切换历史记录

```python
# 获取切换历史
history = data_source_switcher.get_switch_history()
for record in history:
    print(f"时间: {record['timestamp']}, 数据源: {record['config']['name']}")
```

### 2. 缓存管理

```python
# 清除特定缓存
data_source_switcher.clear_cache("test_cache")

# 清除所有缓存
data_source_switcher.clear_cache()
```

### 3. 获取当前数据源信息

```python
current_config = data_source_switcher.get_current_data_source()
if current_config:
    print(f"当前数据源类型: {current_config['type']}")
    print(f"当前数据源名称: {current_config['name']}")
```

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

确保Redis配置正确：

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
    """安全的数据源切换"""
    try:
        success = data_source_switcher.switch_to(config)
        if not success:
            # 记录错误并尝试回退
            error(f"无法切换到数据源: {config}")
            return False
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
        # 处理批次数据
        yield batch
```

### 4. 测试隔离

```python
def test_with_isolated_data_source():
    """使用隔离的数据源进行测试"""
    # 使用上下文管理器确保测试隔离
    with with_data_source("db://mysql/test/SELECT * FROM test_cases LIMIT 10") as switcher:
        data = get_data_from_current_source()
        # 执行测试逻辑
        assert len(data) <= 10
```

## 常见问题

### Q1: 如何处理数据源连接失败？

A1: 使用错误处理和回退机制：

```python
def robust_data_source_switch(primary_config, fallback_config):
    """健壮的数据源切换"""
    success = data_source_switcher.switch_to(primary_config)
    if not success:
        success = data_source_switcher.switch_to(fallback_config)
        if not success:
            raise Exception("所有数据源都不可用")
```

### Q2: 如何优化大数据量查询的性能？

A2: 使用分页和缓存：

```python
# 分页查询
"db://mysql/test/SELECT * FROM large_table LIMIT 1000 OFFSET 0?cache_key=page_1"

# 使用索引优化查询
"db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' AND created_at > '2024-01-01'"
```

### Q3: 如何确保数据一致性？

A3: 使用事务和版本控制：

```python
# 使用事务确保数据一致性
with data_source_switcher.temporary_switch("db://mysql/test/SELECT * FROM test_cases") as switcher:
    # 在事务中执行操作
    result = execute_query_on_current_source("BEGIN")
    # 执行测试逻辑
    result = execute_query_on_current_source("COMMIT")
```

## 总结

动态数据源切换功能为测试框架提供了强大的灵活性，允许你在测试过程中轻松切换不同的数据源。通过合理使用这个功能，你可以：

1. 提高测试的灵活性和可维护性
2. 支持多环境测试
3. 实现复杂的数据源组合
4. 优化测试性能
5. 增强错误处理能力

建议在实际使用中根据具体需求选择合适的切换方式，并遵循最佳实践来确保测试的稳定性和可靠性。 