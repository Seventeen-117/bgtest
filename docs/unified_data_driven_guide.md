# 统一数据驱动测试框架使用指南

## 🎯 框架概述

统一数据驱动测试框架整合了三种数据驱动方式：
1. **文件数据驱动** - JSON/YAML/CSV文件管理
2. **数据库数据驱动** - 大规模数据库数据
3. **动态生成驱动** - pytest_generate_tests钩子

## 🏗️ 架构设计

### 核心组件

```
DataDrivenFramework
├── 数据加载器 (load_test_data)
├── 数据处理器 (process_test_data)
├── 动态生成器 (dynamic_generators)
├── 装饰器 (data_driven, parametrize_from_source)
└── pytest钩子 (pytest_generate_tests)
```

### 支持的数据源

| 数据源类型 | 格式 | 示例 |
|------------|------|------|
| 文件数据 | YAML/JSON/CSV | `caseparams/test_data.yaml` |
| 数据库数据 | db://格式 | `db://mysql/test/SELECT * FROM test_cases` |
| Redis数据 | redis://格式 | `redis://test:user:123` |
| 动态数据 | dynamic://格式 | `dynamic://sequential` |
| 混合数据 | 配置字典 | `{'base': 'file.yaml', 'dynamic': 'dynamic://random'}` |

## 📚 使用方式

### 1. 直接使用框架

```python
from common.data_driven_framework import data_driven_framework

# 加载文件数据
file_data = data_driven_framework.load_test_data('caseparams/test_data.yaml')

# 加载数据库数据
db_data = data_driven_framework.load_test_data('db://mysql/test/SELECT * FROM test_cases')

# 动态生成数据
dynamic_data = data_driven_framework.load_test_data('dynamic://sequential')
```

### 2. 使用装饰器

```python
from common.data_driven_framework import data_driven, parametrize_from_source

# 数据驱动装饰器
@data_driven('caseparams/test_data.yaml', processor='validate')
def test_api_with_data(test_data):
    # 测试逻辑
    pass

# 参数化装饰器
@parametrize_from_source('dynamic://sequential')
def test_api_with_dynamic_data(test_data):
    # 测试逻辑
    pass
```

### 3. 使用pytest钩子

```python
def test_with_hook(test_data):
    # 测试逻辑
    pass

# 设置数据源标记
test_with_hook.data_source = 'caseparams/test_data.yaml'
test_with_hook.data_type = 'file'
test_with_hook.processor = 'validate'
```

## 🔧 配置说明

### 数据源配置

#### 文件数据源
```yaml
# caseparams/test_data.yaml
- case_id: "TEST_001"
  description: "测试用例1"
  url: "https://api.example.com/test"
  method: "POST"
  params:
    message: "Hello"
  expected_result:
    code: 0
    msg: "success"
```

#### 数据库数据源
```python
# db://格式: db://数据库类型/环境/SQL查询?参数
db_config = "db://mysql/test/SELECT * FROM test_cases WHERE status = 'active' LIMIT 5?cache_key=active_cases"
```

#### 动态数据源
```python
# dynamic://格式: dynamic://生成器名称
dynamic_config = "dynamic://sequential"
# 或使用字典配置
dynamic_config = {
    'generator': 'sequential',
    'params': {'count': 10, 'base_url': 'https://api.example.com'}
}
```

### 数据处理器

#### 内置处理器

1. **validate** - 验证数据格式
```python
# 验证必需字段并添加默认值
data = data_driven_framework.process_test_data(raw_data, 'validate')
```

2. **add_timestamp** - 添加时间戳
```python
# 为每条数据添加时间戳
data = data_driven_framework.process_test_data(raw_data, 'add_timestamp')
```

#### 自定义处理器
```python
def custom_processor(data):
    for item in data:
        item['processed'] = True
        item['processor_name'] = 'custom'
    return data

# 注册自定义处理器
data_driven_framework.register_data_processor('custom', custom_processor)
```

### 动态生成器

#### 内置生成器

1. **sequential** - 顺序数据生成
```python
# 生成顺序测试数据
data = data_driven_framework.load_test_data('dynamic://sequential')
```

2. **random** - 随机数据生成
```python
# 生成随机测试数据
data = data_driven_framework.load_test_data('dynamic://random')
```

#### 自定义生成器
```python
def custom_generator(**params):
    count = params.get('count', 5)
    data = []
    for i in range(count):
        data.append({
            'case_id': f"custom_{i+1}",
            'url': f"https://api.example.com/test/{i+1}",
            'method': 'GET'
        })
    return data

# 注册自定义生成器
data_driven_framework.register_dynamic_generator('custom', custom_generator)
```

## 📊 混合数据源

### 配置方式
```python
mixed_config = {
    'base': 'caseparams/base_data.yaml',      # 基础数据
    'dynamic': 'dynamic://random',            # 动态数据
    'merge_strategy': 'cross_product'         # 合并策略
}

data = data_driven_framework.load_test_data(mixed_config, 'mixed')
```

### 合并策略

1. **append** - 简单追加
2. **cross_product** - 笛卡尔积合并
3. **custom** - 自定义合并逻辑

## 🚀 最佳实践

### 1. 数据组织

```
caseparams/
├── test_api_basic.yaml      # 基础API测试
├── test_api_advanced.yaml   # 高级API测试
├── test_performance.csv     # 性能测试数据
└── test_scenarios.json      # 场景测试数据
```

### 2. 测试用例结构

```python
class TestAPI:
    @data_driven('caseparams/test_api_basic.yaml', processor='validate')
    def test_api_basic(self, test_data):
        # 基础API测试
        pass
    
    @parametrize_from_source('dynamic://sequential')
    def test_api_dynamic(self, test_data):
        # 动态API测试
        pass
    
    def test_api_with_hook(self, test_data):
        # 钩子方式测试
        pass

# 设置钩子数据源
TestAPI.test_api_with_hook.data_source = 'caseparams/test_api_advanced.yaml'
```

### 3. 错误处理

```python
def test_with_error_handling():
    try:
        data = data_driven_framework.load_test_data('nonexistent_file.yaml')
        assert len(data) == 0, "不存在的文件应该返回空列表"
    except Exception as e:
        # 记录错误但不中断测试
        info(f"预期的错误: {e}")
```

### 4. 性能优化

```python
def test_performance():
    import time
    
    # 测试数据加载性能
    start_time = time.time()
    data = data_driven_framework.load_test_data('caseparams/large_dataset.yaml')
    load_time = time.time() - start_time
    
    assert load_time < 1.0, f"数据加载时间过长: {load_time:.2f}秒"
```

## 🔍 调试和监控

### 日志记录
```python
from common.log import info, error, debug

# 框架会自动记录数据加载和处理过程
info(f"加载了 {len(data)} 条测试数据")
error(f"数据加载失败: {e}")
```

### Allure集成
```python
import allure
from utils.allure_utils import attach_json

def test_with_allure(test_data):
    with allure.step("执行测试"):
        attach_json("测试数据", test_data)
        # 测试逻辑
```

### 性能监控
```python
def test_performance_monitoring():
    # 框架内置性能监控
    performance_metrics = data_driven_framework.get_performance_metrics()
    attach_json("性能指标", performance_metrics)
```

## ⚠️ 注意事项

1. **数据格式一致性** - 确保所有数据源返回相同格式的数据
2. **错误处理** - 合理处理数据加载失败的情况
3. **性能考虑** - 大数据量时考虑分批处理
4. **缓存策略** - 合理使用缓存避免重复加载
5. **环境隔离** - 不同环境使用不同的数据源配置

## 🔄 扩展开发

### 添加新的数据源类型
```python
def load_custom_data_source(source_config):
    # 自定义数据源加载逻辑
    pass

# 注册新的数据源类型
data_driven_framework.register_data_source('custom', load_custom_data_source)
```

### 添加新的数据处理器
```python
def custom_data_processor(data):
    # 自定义数据处理逻辑
    return processed_data

# 注册新的数据处理器
data_driven_framework.register_data_processor('custom', custom_data_processor)
```

### 添加新的动态生成器
```python
def custom_dynamic_generator(**params):
    # 自定义动态数据生成逻辑
    return generated_data

# 注册新的动态生成器
data_driven_framework.register_dynamic_generator('custom', custom_dynamic_generator)
```

## 📈 性能指标

| 操作 | 预期性能 | 说明 |
|------|----------|------|
| 文件数据加载 | < 1.0秒 | 1000条记录 |
| 数据库查询 | < 5.0秒 | 1000条记录 |
| 动态数据生成 | < 0.5秒 | 100条记录 |
| 混合数据加载 | < 2.0秒 | 基础+动态数据 |

## 🎉 总结

统一数据驱动测试框架提供了：

✅ **统一接口** - 三种数据驱动方式统一管理  
✅ **灵活配置** - 支持多种数据源和处理器  
✅ **易于扩展** - 支持自定义数据源和处理器  
✅ **性能优化** - 内置缓存和性能监控  
✅ **错误处理** - 完善的错误处理机制  
✅ **报告集成** - 与Allure等报告工具集成  

通过这个框架，你可以轻松实现复杂的数据驱动测试场景，提高测试效率和覆盖率。 