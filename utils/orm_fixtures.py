# coding: utf-8
# @Author: bgtech
"""
pytest 数据库 fixtures
提供数据库会话、事务管理和数据库切换的fixtures
"""

import pytest
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from common.log import info, error
from common.orm_manager import db_manager, get_db_session, switch_database


@pytest.fixture(scope="session")
def db_engine():
    """
    数据库引擎fixture
    会话级别，在整个测试会话期间保持
    """
    info("初始化数据库引擎")
    yield db_manager
    # 测试会话结束时关闭所有连接
    db_manager.close_all_connections()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    数据库会话fixture
    函数级别，每个测试函数都会获得新的会话
    """
    # 默认使用MySQL测试环境
    session = get_db_session('mysql', 'test')
    if not session:
        # 如果MySQL不可用，尝试SQLite
        session = get_db_session('sqlite', 'test')
    
    if not session:
        pytest.skip("无法获取数据库会话")
    
    info(f"创建数据库会话: {session.bind.url}")
    
    try:
        yield session
    finally:
        session.close()
        info("关闭数据库会话")


@pytest.fixture(scope="function")
def db_session_mysql(db_engine):
    """
    MySQL数据库会话fixture
    """
    session = get_db_session('mysql', 'test')
    if not session:
        pytest.skip("MySQL数据库不可用")
    
    info("创建MySQL数据库会话")
    
    try:
        yield session
    finally:
        session.close()
        info("关闭MySQL数据库会话")


@pytest.fixture(scope="function")
def db_session_postgresql(db_engine):
    """
    PostgreSQL数据库会话fixture
    """
    session = get_db_session('postgresql', 'test')
    if not session:
        pytest.skip("PostgreSQL数据库不可用")
    
    info("创建PostgreSQL数据库会话")
    
    try:
        yield session
    finally:
        session.close()
        info("关闭PostgreSQL数据库会话")


@pytest.fixture(scope="function")
def db_session_sqlite(db_engine):
    """
    SQLite数据库会话fixture
    """
    session = get_db_session('sqlite', 'test')
    if not session:
        pytest.skip("SQLite数据库不可用")
    
    info("创建SQLite数据库会话")
    
    try:
        yield session
    finally:
        session.close()
        info("关闭SQLite数据库会话")


@pytest.fixture(scope="function")
def db_transaction(db_session):
    """
    数据库事务fixture
    提供事务支持，测试失败时自动回滚
    """
    # 开始事务
    transaction = db_session.begin_nested()
    
    try:
        yield db_session
        # 提交事务
        transaction.commit()
        info("数据库事务提交成功")
    except Exception as e:
        # 回滚事务
        transaction.rollback()
        error(f"数据库事务回滚: {e}")
        raise
    finally:
        # 关闭事务
        transaction.close()


@pytest.fixture(scope="function")
def clean_db(db_session):
    """
    清理数据库fixture
    测试前清理数据，测试后恢复
    """
    # 保存原始数据（可选）
    original_data = {}
    
    try:
        # 清理测试数据（这里可以根据实际需要清理特定表）
        # 例如：清理测试相关的表
        test_tables = ['test_data', 'api_logs', 'temp_data']
        for table in test_tables:
            try:
                db_session.execute(f"DELETE FROM {table} WHERE environment = 'test'")
            except:
                pass  # 表可能不存在
        
        db_session.commit()
        info("数据库清理完成")
        
        yield db_session
        
    finally:
        # 恢复数据（可选）
        if original_data:
            for table, data in original_data.items():
                for row in data:
                    # 这里可以根据需要恢复数据
                    pass
            db_session.commit()
            info("数据库数据恢复完成")


@pytest.fixture(scope="session")
def setup_database():
    """
    设置数据库fixture
    会话级别，验证数据库连接
    """
    info("开始设置数据库")
    
    # 测试数据库连接
    databases = ['mysql', 'postgresql', 'sqlite']
    connected = False
    
    for db_type in databases:
        if db_manager.test_connection(db_type, 'test'):
            connected = True
            info(f"数据库连接成功: {db_type}")
            break
    
    if not connected:
        pytest.skip("无法连接到任何数据库")
    
    info("数据库设置完成")
    yield
    info("数据库设置结束")


@pytest.fixture(scope="function")
def db_switch_mysql():
    """
    切换到MySQL数据库
    """
    switch_database('mysql', 'test')
    yield
    # 可以在这里添加清理逻辑


@pytest.fixture(scope="function")
def db_switch_postgresql():
    """
    切换到PostgreSQL数据库
    """
    switch_database('postgresql', 'test')
    yield
    # 可以在这里添加清理逻辑


@pytest.fixture(scope="function")
def db_switch_sqlite():
    """
    切换到SQLite数据库
    """
    switch_database('sqlite', 'test')
    yield
    # 可以在这里添加清理逻辑


@pytest.fixture(scope="function")
def db_environment(request):
    """
    动态数据库环境fixture
    根据测试参数选择数据库
    """
    # 从测试参数中获取数据库类型
    db_type = getattr(request, 'param', 'mysql')
    env = 'test'
    
    switch_database(db_type, env)
    info(f"切换到数据库: {db_type} - {env}")
    
    yield db_type, env


# 数据库操作辅助函数
def create_test_data(session: Session, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建测试数据
    :param session: 数据库会话
    :param table_name: 表名
    :param data: 数据字典
    :return: 插入的数据
    """
    # 构建插入SQL
    columns = list(data.keys())
    values = list(data.values())
    placeholders = [f":{col}" for col in columns]
    
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    
    try:
        result = session.execute(sql, data)
        session.commit()
        info(f"成功插入测试数据到表 {table_name}")
        return data
    except Exception as e:
        session.rollback()
        error(f"插入测试数据失败: {e}")
        raise


def get_test_data(session: Session, table_name: str, conditions: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    获取测试数据
    :param session: 数据库会话
    :param table_name: 表名
    :param conditions: 查询条件
    :return: 查询结果
    """
    sql = f"SELECT * FROM {table_name}"
    params = {}
    
    if conditions:
        where_clauses = []
        for key, value in conditions.items():
            where_clauses.append(f"{key} = :{key}")
            params[key] = value
        sql += f" WHERE {' AND '.join(where_clauses)}"
    
    try:
        result = session.execute(sql, params)
        return [dict(row._mapping) for row in result]
    except Exception as e:
        error(f"查询测试数据失败: {e}")
        return []


def update_test_data(session: Session, table_name: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> int:
    """
    更新测试数据
    :param session: 数据库会话
    :param table_name: 表名
    :param data: 更新数据
    :param conditions: 更新条件
    :return: 影响的行数
    """
    set_clauses = [f"{key} = :{key}" for key in data.keys()]
    where_clauses = [f"{key} = :where_{key}" for key in conditions.keys()]
    
    sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    
    # 合并参数
    params = {**data, **{f"where_{k}": v for k, v in conditions.items()}}
    
    try:
        result = session.execute(sql, params)
        session.commit()
        return result.rowcount
    except Exception as e:
        session.rollback()
        error(f"更新测试数据失败: {e}")
        raise


def delete_test_data(session: Session, table_name: str, conditions: Dict[str, Any] = None) -> int:
    """
    删除测试数据
    :param session: 数据库会话
    :param table_name: 表名
    :param conditions: 删除条件
    :return: 影响的行数
    """
    sql = f"DELETE FROM {table_name}"
    params = {}
    
    if conditions:
        where_clauses = []
        for key, value in conditions.items():
            where_clauses.append(f"{key} = :{key}")
            params[key] = value
        sql += f" WHERE {' AND '.join(where_clauses)}"
    
    try:
        result = session.execute(sql, params)
        session.commit()
        return result.rowcount
    except Exception as e:
        session.rollback()
        error(f"删除测试数据失败: {e}")
        raise


def cleanup_test_data(session: Session):
    """
    清理测试数据
    :param session: 数据库会话
    """
    try:
        # 清理测试相关的表
        test_tables = ['test_data', 'api_logs', 'temp_data']
        for table in test_tables:
            try:
                session.execute(f"DELETE FROM {table} WHERE environment = 'test'")
            except:
                pass  # 表可能不存在
        
        session.commit()
        info("测试数据清理完成")
    except Exception as e:
        session.rollback()
        error(f"清理测试数据失败: {e}")
        raise


def get_table_structure(session: Session, table_name: str) -> List[Dict[str, Any]]:
    """
    获取表结构信息
    :param session: 数据库会话
    :param table_name: 表名
    :return: 表结构信息
    """
    try:
        # 获取数据库类型
        db_url = str(session.bind.url)
        
        if 'mysql' in db_url:
            sql = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = :table_name
            ORDER BY ORDINAL_POSITION
            """
        elif 'postgresql' in db_url:
            sql = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                '' as column_comment
            FROM information_schema.columns 
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
        elif 'sqlite' in db_url:
            sql = "PRAGMA table_info(:table_name)"
        else:
            error(f"不支持的数据库类型: {db_url}")
            return []
        
        result = session.execute(sql, {'table_name': table_name})
        return [dict(row._mapping) for row in result]
        
    except Exception as e:
        error(f"获取表结构信息失败: {e}")
        return [] 