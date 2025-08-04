# 增强版数据源切换器使用指南

## 概述

增强版数据源切换器是对原有动态数据源切换功能的全面优化，提供了以下增强功能：

- ✅ **性能优化**: LRU缓存、连接池管理
- ✅ **错误处理**: 重试机制、回退策略
- ✅ **监控诊断**: 性能指标收集、健康检查
- ✅ **线程安全**: 并发安全的数据源切换
- ✅ **流式API**: 链式调用接口

## 快速开始

### 1. 基础使用

```python
from common.enhanced_data_source_switcher import enhanced_data_source_switcher

# 切换到文件数据源
success = enhanced_data_source_switcher.switch_to("caseparams/test_chat_gateway.yaml")
if success:
    data = enhanced_data_source_switcher.get_data()
    print(f"获取到 {len(data)} 条数据")
```

### 2. 流式API使用

```python
from common.fluent_data_source_switcher import from_file, from_database

# 链式调用
data = (from_file("caseparams/test_chat_gateway.yaml")
        .with_cache("test_cache", 1800)
        .execute())

# 数据库数据源
data = (from_database("mysql", "test")
        .with_sql("SELECT * FROM test_cases LIMIT 10")
        .with_cache("db_cache", 3600)
        .execute())
```

## 核心功能

### 1. 性能优化

#### LRU缓存
```python
from common.enhanced_data_source_switcher import EnhancedDataSourceSwitcher, CacheConfig

# 自定义缓存配置
cache_config = CacheConfig(max_size=200, ttl=7200, enable_lru=True)
switcher = EnhancedDataSourceSwitcher(cache_config=cache_config)

# 使用缓存
switcher.switch_to("caseparams/test_data.yaml")
data1 = switcher.get_data(cache_key="my_cache")
data2 = switcher.get_data(cache_key="my_cache")  # 从缓存获取
```

#### 连接池管理
```python
# 连接池自动管理，无需手动配置
switcher = EnhancedDataSourceSwitcher()

# 多次切换使用相同的连接池
switcher.switch_to("db://mysql/test/SELECT 1")
switcher.switch_to("db://mysql/test/SELECT 2")
# 连接会被复用
```

### 2. 错误处理和重试

#### 重试机制
```python
from common.enhanced_data_source_switcher import RetryConfig

# 配置重试策略
retry_config = RetryConfig(
    max_retries=3,
    backoff_factor=2.0,
    initial_delay=1.0,
    max_delay=60.0
)
switcher = EnhancedDataSourceSwitcher(retry_config=retry_config)

# 带重试的数据获取
data = switcher.get_data()  # 自动重试失败的操作
```

#### 回退策略
```python
# 主要配置 + 回退配置
primary_config = "db://mysql/test/SELECT * FROM users"
fallback_configs = [
    "caseparams/fallback_users.yaml",
    "db://mysql/dev/SELECT * FROM users"
]

success = switcher.switch_to_with_fallback(primary_config, fallback_configs)
```

### 3. 监控和诊断

#### 性能指标
```python
# 获取性能指标
metrics = switcher.get_metrics()
print(f"切换次数: {metrics['switch_count']}")
print(f"成功率: {metrics['success_rate']:.2%}")
print(f"平均切换时间: {metrics['avg_switch_time']:.4f}s")
print(f"缓存命中率: {metrics['cache_hit_rate']:.2%}")
```

#### 健康检查
```python
# 健康检查自动执行
success = switcher.switch_to("caseparams/test_data.yaml")
# 如果文件不存在，健康检查会阻止切换
```

### 4. 线程安全

#### 并发使用
```python
import threading

def worker(worker_id):
    switcher = EnhancedDataSourceSwitcher()
    success = switcher.switch_to("caseparams/test_data.yaml")
    data = switcher.get_data()
    print(f"Worker {worker_id}: {len(data)} 条数据")

# 多线程安全使用
threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### 5. 流式API

#### 基础链式调用
```python
from common.fluent_data_source_switcher import from_file, from_database, from_redis

# 文件数据源
data = (from_file("caseparams/test_data.yaml")
        .with_cache("file_cache", 1800)
        .execute())

# 数据库数据源
data = (from_database("mysql", "test")
        .with_sql("SELECT * FROM test_cases WHERE status = 'active'")
        .with_cache("db_cache", 3600)
        .execute())

# Redis数据源
data = (from_redis("test")
        .with_key("test:user:123")
        .with_cache("redis_cache", 1800)
        .execute())
```

#### 高级配置
```python
# 重试配置
data = (from_file("caseparams/test_data.yaml")
        .with_retry(max_retries=3, backoff_factor=1.5)
        .with_cache("retry_cache")
        .execute())

# 回退配置
data = (from_file("caseparams/test_data.yaml")
        .with_fallback("caseparams/fallback.yaml", "db://mysql/test/SELECT 1")
        .with_cache("fallback_cache")
        .execute())
```

#### 临时切换
```python
# 使用上下文管理器
with from_file("caseparams/test_data.yaml").temporary() as switcher:
    data = switcher.execute()
    # 数据源会在退出时自动恢复
```

## 配置选项

### 1. 重试配置

```python
@dataclass
class RetryConfig:
    max_retries: int = 3          # 最大重试次数
    backoff_factor: float = 2.0    # 退避因子
    initial_delay: float = 1.0     # 初始延迟（秒）
    max_delay: float = 60.0        # 最大延迟（秒）
```

### 2. 缓存配置

```python
@dataclass
class CacheConfig:
    max_size: int = 100           # 最大缓存项数
    ttl: int = 3600               # 缓存时间（秒）
    enable_lru: bool = True       # 启用LRU策略
```

## 最佳实践

### 1. 性能优化

```python
# 使用有意义的缓存键
switcher.switch_to("db://mysql/test/SELECT * FROM large_table?cache_key=large_data&ttl=7200")

# 批量处理数据
def process_data_in_batches(data, batch_size=100):
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        yield batch
```

### 2. 错误处理

```python
def safe_data_source_switch(config, fallback_configs=None):
    """安全的数据源切换"""
    try:
        if fallback_configs:
            success = switcher.switch_to_with_fallback(config, fallback_configs)
        else:
            success = switcher.switch_to(config)
        
        if not success:
            raise Exception("数据源切换失败")
        
        return switcher.get_data()
    except Exception as e:
        error(f"数据源操作失败: {e}")
        return []
```

### 3. 监控和告警

```python
def monitor_data_source_performance():
    """监控数据源性能"""
    metrics = switcher.get_metrics()
    
    # 检查成功率
    if metrics['success_rate'] < 0.9:
        warn(f"数据源成功率过低: {metrics['success_rate']:.2%}")
    
    # 检查平均响应时间
    if metrics['avg_switch_time'] > 1.0:
        warn(f"数据源响应时间过长: {metrics['avg_switch_time']:.4f}s")
    
    # 检查缓存命中率
    if metrics['cache_hit_rate'] < 0.5:
        warn(f"缓存命中率过低: {metrics['cache_hit_rate']:.2%}")
```

### 4. 测试用例

```python
def test_data_source_switcher():
    """测试数据源切换器"""
    switcher = EnhancedDataSourceSwitcher()
    
    # 测试文件数据源
    success = switcher.switch_to("caseparams/test_data.yaml")
    assert success, "文件数据源切换失败"
    
    data = switcher.get_data()
    assert len(data) > 0, "数据获取失败"
    
    # 测试缓存功能
    data1 = switcher.get_data(cache_key="test_cache")
    data2 = switcher.get_data(cache_key="test_cache")
    assert data1 == data2, "缓存功能异常"
    
    # 测试指标收集
    metrics = switcher.get_metrics()
    assert metrics['switch_count'] > 0, "指标收集失败"
```

## 故障排除

### 1. 常见问题

#### 导入错误
```python
# 错误: ImportError: cannot import name 'warn' from 'common.log'
# 解决: 确保 common/log.py 中包含 warn 函数
```

#### 连接失败
```python
# 检查数据库配置
# 确保 conf/database.yaml 配置正确
# 检查网络连接
```

#### 缓存问题
```python
# 清除缓存
switcher.clear_cache()  # 清除所有缓存
switcher.clear_cache("specific_key")  # 清除特定缓存
```

### 2. 性能调优

```python
# 调整缓存大小
cache_config = CacheConfig(max_size=500, ttl=7200)
switcher = EnhancedDataSourceSwitcher(cache_config=cache_config)

# 调整重试策略
retry_config = RetryConfig(max_retries=5, backoff_factor=1.5)
switcher = EnhancedDataSourceSwitcher(retry_config=retry_config)
```

### 3. 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger('common.enhanced_data_source_switcher').setLevel(logging.DEBUG)

# 查看操作历史
history = switcher.get_switch_history()
for entry in history:
    print(f"时间: {entry['timestamp']}, 配置: {entry['config']}")

# 查看性能指标
metrics = switcher.get_metrics()
print(f"性能指标: {metrics}")
```

## 总结

增强版数据源切换器提供了企业级的性能和可靠性，通过以下特性显著提升了数据源管理的效率：

1. **高性能**: LRU缓存、连接池复用
2. **高可靠**: 重试机制、回退策略、健康检查
3. **易监控**: 详细的性能指标和错误日志
4. **易使用**: 流式API、链式调用
5. **线程安全**: 并发环境下的安全使用

这些优化使得数据源切换功能更加稳定、高效和易用，特别适合大规模测试环境和企业级应用。 