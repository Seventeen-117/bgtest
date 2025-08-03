# SQLAlchemy ORM 集成指南

## 🎯 集成目标

将 SQLAlchemy ORM 集成到 pytest 测试框架中，结合现有的 `data_source.py` 数据库工具类，实现在执行测试用例时灵活选择切换数据库。

## 🏗️ 架构设计

### 核心组件

- **`common/orm_models.py`**: ORM 模型定义
- **`common/orm_manager.py`**: ORM 管理器
- **`utils/orm_fixtures.py`**: pytest ORM fixtures
- **`testcase/test_orm_integration.py`**: 集成测试用例

### 数据库支持

- ✅ **MySQL**: 通过 PyMySQL 驱动
- ✅ **PostgreSQL**: 通过 psycopg2 驱动  
- ✅ **SQLite**: 内置支持

## 📋 功能特性

### 核心功能

1. **多数据库切换**: 支持在测试运行时动态切换数据库
2. **ORM 模型**: 提供完整的 ORM 模型定义
3. **会话管理**: 自动管理数据库会话和连接池
4. **事务支持**: 提供事务管理和自动回滚
5. **Fixtures 集成**: 与 pytest fixtures 完美集成

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install SQLAlchemy>=2.0.0
```

### 2. 基本使用

#### 数据库切换

```python
from common.orm_manager import switch_database, get_orm_session

# 切换到MySQL
switch_database('mysql', 'test')
session = get_orm_session()

# 切换到PostgreSQL
switch_database('postgresql', 'test')
session = get_orm_session()
```

#### 使用 ORM 模型

```python
from common.orm_models import User, Order, Payment
from sqlalchemy.orm import Session

def test_user_operations(db_session: Session):
    # 创建用户
    user = User(
        username='test_user',
        email='test@example.com',
        password_hash='hashed_password',
        phone='13800138000',
        status=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # 查询用户
    found_user = db_session.query(User).filter(User.username == 'test_user').first()
    assert found_user is not None
```

#### 使用 Fixtures

```python
import pytest
from sqlalchemy.orm import Session

def test_with_mysql_session(db_session_mysql: Session):
    """使用MySQL数据库会话"""
    result = db_session_mysql.execute("SELECT 1 as test")
    assert result.fetchone()[0] == 1

def test_with_transaction(db_transaction: Session):
    """使用事务支持"""
    user = User(username='transaction_user', email='transaction@example.com')
    db_transaction.add(user)
    db_transaction.commit()
```

### 3. 高级用法

#### 参数化测试

```python
import pytest

@pytest.mark.parametrize("db_environment", ["mysql", "postgresql", "sqlite"], indirect=True)
def test_parameterized_database(db_environment):
    """参数化测试不同数据库"""
    db_type, env = db_environment
    
    session = orm_manager.get_current_session()
    result = session.execute("SELECT 1 as test")
    assert result.fetchone()[0] == 1
```

#### 原始 SQL 执行

```python
from common.orm_manager import execute_sql

def test_raw_sql():
    """执行原始SQL"""
    result = execute_sql("SELECT COUNT(*) as count FROM users", db_type='mysql', env='test')
    assert len(result) == 1
```

## 📊 可用 Fixtures

### 数据库会话 Fixtures

| Fixture | 描述 | 作用域 |
|---------|------|--------|
| `db_session` | 默认数据库会话 | function |
| `db_session_mysql` | MySQL数据库会话 | function |
| `db_session_postgresql` | PostgreSQL数据库会话 | function |
| `db_session_sqlite` | SQLite数据库会话 | function |

### 事务管理 Fixtures

| Fixture | 描述 | 作用域 |
|---------|------|--------|
| `db_transaction` | 数据库事务支持 | function |
| `clean_db` | 数据库清理 | function |

### 示例数据 Fixtures

| Fixture | 描述 | 作用域 |
|---------|------|--------|
| `sample_user` | 示例用户数据 | function |
| `sample_order` | 示例订单数据 | function |
| `sample_payment` | 示例支付数据 | function |
| `sample_test_data` | 示例测试数据 | function |

## 🗂️ ORM 模型

### 核心模型

#### User (用户表)
```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20))
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

#### Order (订单表)
```python
class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='CNY')
    status = Column(String(20), default='pending')
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

#### Payment (支付表)
```python
class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_no = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), default='pending')
    transaction_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

## 📝 最佳实践

### 1. 测试数据管理

```python
def test_with_clean_data(clean_db):
    """使用清理的数据库进行测试"""
    # 测试逻辑
    pass

def test_with_sample_data(sample_user, sample_order):
    """使用示例数据进行测试"""
    # 测试逻辑
    pass
```

### 2. 事务管理

```python
def test_with_transaction(db_transaction):
    """使用事务进行测试"""
    # 在事务中操作，失败时自动回滚
    pass
```

### 3. 多数据库测试

```python
@pytest.mark.parametrize("db_type", ["mysql", "postgresql", "sqlite"])
def test_multi_database(db_type):
    """测试多个数据库"""
    switch_database(db_type, 'test')
    # 测试逻辑
    pass
```

## 🎉 总结

通过 SQLAlchemy ORM 集成，我们实现了：

1. **✅ 多数据库支持**: 支持 MySQL、PostgreSQL、SQLite
2. **✅ 灵活切换**: 在测试运行时动态切换数据库
3. **✅ ORM 模型**: 提供完整的 ORM 模型定义
4. **✅ Fixtures 集成**: 与 pytest fixtures 完美集成
5. **✅ 事务管理**: 提供事务支持和自动回滚

现在您可以在测试用例中灵活使用 ORM，实现更强大的数据库操作和测试功能！ 