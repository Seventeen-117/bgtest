# conftest.py 优化指南

## 概述

本项目已经创建了一个全面优化的 `conftest.py` 文件，整合了原有的功能并添加了更多实用的 fixtures 和 hooks。这个文件位于项目根目录，为整个测试框架提供了强大的支持。

## 主要特性

### 1. 配置和初始化
- **pytest_configure**: 自动注册自定义标记
- **pytest_sessionstart/pytest_sessionfinish**: 会话级别的开始和结束处理
- **自动创建必要目录**: report、log、temp 等

### 2. 核心 Fixtures

#### HTTP 客户端
```python
@pytest.fixture(scope="session")
def http_client():
    """全局HTTP客户端fixture"""
```

**使用示例:**
```python
def test_api_call(http_client):
    response = http_client.get("/api/users")
    assert response.status_code == 200
```

#### Allure 工具
```python
@pytest.fixture(scope="session")
def allure_utils():
    """Allure工具类fixture"""
```

**使用示例:**
```python
def test_with_allure(allure_utils):
    allure_utils.attach_text("测试数据", "测试信息")
```

#### 测试配置
```python
@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
```

**使用示例:**
```python
def test_with_config(test_config):
    base_url = test_config['base_url']
    timeout = test_config['timeout']
```

### 3. 测试数据 Fixtures

#### 文件数据加载
```python
@pytest.fixture(scope="session")
def test_data():
    """测试数据fixture"""
```

**使用示例:**
```python
def test_with_file_data(test_data):
    data = test_data("caseparams/test_data.yaml")
    for item in data:
        # 处理测试数据
        pass
```

#### 数据库连接
```python
@pytest.fixture(scope="session")
def db_connection():
    """数据库连接fixture"""
```

**使用示例:**
```python
def test_with_db_data(db_connection):
    sql = "SELECT * FROM users WHERE status = 'active'"
    users = db_connection(sql, db_type="mysql", env="test")
    assert len(users) > 0
```

### 4. 环境相关 Fixtures

#### 环境信息
```python
@pytest.fixture(scope="session")
def environment():
    """环境信息fixture"""
```

**使用示例:**
```python
def test_environment_specific(environment):
    env_name = environment['name']
    base_url = environment['base_url']
    # 根据环境执行不同的测试逻辑
```

#### 测试环境设置
```python
@pytest.fixture(scope="session")
def test_environment():
    """测试环境设置fixture"""
```

**使用示例:**
```python
def test_with_environment(test_environment):
    # 环境已自动设置
    # 临时文件会在测试结束后自动清理
    pass
```

### 5. 日志和监控 Fixtures

#### 测试日志
```python
@pytest.fixture(scope="function")
def test_logger():
    """测试日志fixture"""
```

**使用示例:**
```python
def test_with_logging(test_logger):
    test_logger.info("开始测试")
    test_logger.error("测试错误")
```

#### API 监控
```python
@pytest.fixture(scope="function")
def api_monitor():
    """API监控fixture"""
```

**使用示例:**
```python
def test_api_performance(api_monitor, http_client):
    response = http_client.get("/api/users")
    # 监控数据会自动收集并附加到Allure报告
```

### 6. 断言和验证 Fixtures

#### 断言工具
```python
@pytest.fixture(scope="function")
def assertion_utils():
    """断言工具fixture"""
```

**使用示例:**
```python
def test_with_assertions(assertion_utils):
    assertion_utils.assert_status_code(200)
    assertion_utils.assert_response_contains("success")
```

#### 响应验证
```python
@pytest.fixture(scope="function")
def response_validator():
    """响应验证fixture"""
```

**使用示例:**
```python
def test_response_validation(response_validator, http_client):
    response = http_client.get("/api/users")
    validated_response = response_validator(response, expected_status=200)
```

### 7. 测试生命周期 Fixtures

#### 自动设置和清理
```python
@pytest.fixture(scope="function", autouse=True)
def test_setup_teardown(request):
    """测试设置和清理fixture"""
```

**功能:**
- 自动记录测试开始和结束时间
- 自动计算测试执行时长
- 自动记录测试结果

## Allure 增强功能

### 1. 自动报告生成
- 自动捕获测试结果
- 自动附加响应数据到失败测试
- 自动附加测试数据到报告

### 2. 性能监控
- 自动检测慢速测试（超过5秒）
- 自动记录测试执行时间
- 自动生成性能报告

### 3. 错误处理
- 自动捕获和记录异常
- 自动附加异常堆栈到报告
- 自动记录错误详情

## 自定义标记

项目预定义了以下自定义标记：

```python
@pytest.mark.slow          # 慢速测试
@pytest.mark.integration   # 集成测试
@pytest.mark.unit          # 单元测试
@pytest.mark.api           # API测试
@pytest.mark.ui            # UI测试
@pytest.mark.smoke         # 冒烟测试
@pytest.mark.regression    # 回归测试
```

**使用示例:**
```python
@pytest.mark.api
@pytest.mark.smoke
def test_user_login(http_client):
    # API冒烟测试
    pass

@pytest.mark.slow
def test_large_data_processing():
    # 慢速测试
    pass
```

## 工具函数

### 1. 路径工具
```python
def get_test_data_path(filename: str) -> str:
    """获取测试数据文件路径"""
```

### 2. 报告工具
```python
def create_test_report(test_name: str, data: Dict[str, Any]) -> str:
    """创建测试报告"""
```

### 3. 日志工具
```python
def log_test_info(message: str):
    """记录测试信息"""

def log_test_error(message: str, error: Exception = None):
    """记录测试错误"""
```

### 4. Allure 工具
```python
def attach_test_data_to_allure(data: Dict[str, Any], name: str = "测试数据"):
    """将测试数据附加到Allure"""
```

## 配置验证

系统会自动验证必要的配置项：

- `interface.base_url`
- `interface.timeout`
- `log.level`

如果缺少必要配置，系统会给出警告。

## 使用最佳实践

### 1. 测试类结构
```python
import pytest
import allure

@allure.feature("用户管理")
class TestUserManagement:
    
    @pytest.mark.api
    @pytest.mark.smoke
    def test_user_login(self, http_client, test_data):
        """用户登录测试"""
        # 使用fixtures
        data = test_data("caseparams/login_data.yaml")
        
        for login_data in data:
            with allure.step(f"测试登录: {login_data['username']}"):
                response = http_client.post("/api/login", json_data=login_data)
                assert response.status_code == 200
```

### 2. 数据驱动测试
```python
@pytest.mark.parametrize("user_data", [
    {"username": "user1", "password": "pass1"},
    {"username": "user2", "password": "pass2"}
])
def test_user_creation(self, http_client, user_data):
    """用户创建测试"""
    response = http_client.post("/api/users", json_data=user_data)
    assert response.status_code == 201
```

### 3. 数据库测试
```python
def test_user_data_consistency(self, db_connection, http_client):
    """测试用户数据一致性"""
    # 从数据库获取用户数据
    db_users = db_connection("SELECT * FROM users", "mysql", "test")
    
    # 从API获取用户数据
    api_response = http_client.get("/api/users")
    api_users = api_response.json()
    
    # 验证数据一致性
    assert len(db_users) == len(api_users)
```

### 4. 环境特定测试
```python
def test_environment_specific_feature(self, environment, http_client):
    """环境特定功能测试"""
    if environment['name'] == 'prod':
        # 生产环境特定测试
        response = http_client.get("/api/health")
        assert response.status_code == 200
    else:
        # 测试环境特定测试
        response = http_client.get("/api/debug")
        assert response.status_code == 200
```

## 迁移指南

### 从旧版本迁移

1. **删除旧的 conftest.py 文件**
   ```bash
   rm execution/conftest.py
   rm utils/conftest.py
   ```

2. **更新测试文件**
   - 移除对旧 fixtures 的直接引用
   - 使用新的 fixture 名称
   - 更新导入语句

3. **更新配置文件**
   - 确保 `conf/` 目录下的配置文件包含必要的信息
   - 检查环境变量设置

### 兼容性说明

- 新的 conftest.py 向后兼容大部分现有测试
- 原有的 HTTP 工具类仍然可用
- Allure 功能完全兼容

## 故障排除

### 常见问题

1. **ImportError: No module named 'xxx'**
   - 检查项目结构是否正确
   - 确保所有依赖已安装

2. **Fixture not found**
   - 检查 fixture 名称是否正确
   - 确保 conftest.py 在正确位置

3. **配置错误**
   - 检查 `conf/` 目录下的配置文件
   - 验证环境变量设置

### 调试技巧

1. **启用详细日志**
   ```bash
   pytest -v -s --log-cli-level=DEBUG
   ```

2. **查看可用 fixtures**
   ```bash
   pytest --fixtures
   ```

3. **查看配置信息**
   ```bash
   pytest --setup-show
   ```

## 总结

优化后的 `conftest.py` 提供了：

- **统一的配置管理**
- **强大的 fixtures 支持**
- **完整的 Allure 集成**
- **自动化的测试生命周期管理**
- **丰富的工具函数**
- **完善的错误处理和监控**

这个文件为整个测试框架提供了坚实的基础，使得测试编写更加简洁、维护更加容易、功能更加强大。 