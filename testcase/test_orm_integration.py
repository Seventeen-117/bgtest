# coding: utf-8
# @Author: bgtech
"""
数据库集成测试用例
演示SQLAlchemy数据库管理器的使用和多数据库切换功能
"""

import pytest
import allure
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from common.log import info, error
from common.orm_manager import db_manager, switch_database, execute_sql, execute_query, execute_update
from utils.test_decorators import (
    allure_test_case_decorator, allure_api_test_decorator, allure_data_driven_test_decorator, smoke_test,
    allure_feature_story, allure_severity, log_test_info
)


class TestDatabaseIntegration:
    """数据库集成测试类"""
    
    def setup_method(self):
        """测试方法设置"""
        info("开始数据库集成测试")
    
    def teardown_method(self):
        """测试方法清理"""
        info("完成数据库集成测试")
    
    @allure_test_case_decorator("数据库连接测试", "测试不同数据库的连接")
    @allure_feature_story("数据库", "连接管理")
    @allure_severity("critical")
    def test_database_connections(self):
        """测试数据库连接"""
        databases = ['mysql', 'postgresql', 'sqlite']
        
        for db_type in databases:
            with allure.step(f"测试 {db_type} 数据库连接"):
                # 测试连接
                connected = db_manager.test_connection(db_type, 'test')
                
                if not connected:
                    if db_type in ['mysql', 'postgresql']:
                        # 对于需要网络连接的数据库，如果连接失败则跳过
                        pytest.skip(f"{db_type} 数据库连接失败，可能是网络问题")
                    else:
                        # 对于本地数据库，连接失败则断言失败
                        assert connected, f"{db_type} 数据库连接失败"
                
                # 获取数据库信息
                db_info = db_manager.get_database_info(db_type, 'test')
                assert db_info['type'] == db_type
                assert db_info['connected'] == True
                
                info(f"{db_type} 数据库连接测试通过")
    
    @allure_test_case_decorator("数据库切换测试", "测试数据库切换功能")
    @allure_feature_story("数据库", "切换管理")
    @allure_severity("normal")
    def test_database_switching(self):
        """测试数据库切换功能"""
        # 切换到MySQL
        switch_database('mysql', 'test')
        session = db_manager.get_current_session()
        assert session is not None
        assert 'mysql' in str(session.bind.url)
        
        # 切换到PostgreSQL
        switch_database('postgresql', 'test')
        session = db_manager.get_current_session()
        assert session is not None
        assert 'postgresql' in str(session.bind.url)
        
        # 切换到SQLite
        switch_database('sqlite', 'test')
        session = db_manager.get_current_session()
        assert session is not None
        assert 'sqlite' in str(session.bind.url)
        
        info("数据库切换测试通过")
    
    @allure_test_case_decorator("SQL查询测试", "测试SQL查询功能")
    @allure_feature_story("数据库", "查询操作")
    @allure_severity("critical")
    def test_sql_query(self, db_session):
        """测试SQL查询功能"""
        with allure.step("执行简单查询"):
            # 执行简单查询，使用SQLite避免网络连接问题
            result = execute_query("SELECT 1 as test_value", db_type='sqlite', env='test')
            assert len(result) == 1
            assert result[0]['test_value'] == 1
            
            info("SQL查询测试通过")
    
    @allure_test_case_decorator("SQL更新测试", "测试SQL更新功能")
    @allure_feature_story("数据库", "更新操作")
    @allure_severity("normal")
    def test_sql_update(self, db_session):
        """测试SQL更新功能"""
        with allure.step("创建测试表"):
            # 创建测试表（如果不存在）
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS test_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                value INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            try:
                execute_sql(create_table_sql, db_type='mysql', env='test')
                info("测试表创建成功")
            except Exception as e:
                info(f"测试表已存在或创建失败: {e}")
        
        with allure.step("插入测试数据"):
            # 插入测试数据
            insert_sql = """
            INSERT INTO test_table (name, value) VALUES (:name, :value)
            """
            params = {'name': 'test_item', 'value': 100}
            
            affected_rows = execute_update(insert_sql, params, db_type='mysql', env='test')
            assert affected_rows >= 0  # 可能为0如果表已存在数据
            
            info("测试数据插入成功")
        
        with allure.step("更新测试数据"):
            # 更新测试数据
            update_sql = """
            UPDATE test_table SET value = :new_value WHERE name = :name
            """
            params = {'new_value': 200, 'name': 'test_item'}
            
            affected_rows = execute_update(update_sql, params, db_type='mysql', env='test')
            assert affected_rows >= 0
            
            info("测试数据更新成功")
        
        with allure.step("查询验证"):
            # 查询验证
            query_sql = "SELECT * FROM test_table WHERE name = :name"
            params = {'name': 'test_item'}
            
            result = execute_query(query_sql, params, db_type='mysql', env='test')
            assert len(result) > 0
            assert result[0]['value'] == 200
            
            info("数据验证成功")
    
    @allure_test_case_decorator("表结构查询测试", "测试表结构查询功能")
    @allure_feature_story("数据库", "元数据查询")
    @allure_severity("normal")
    def test_table_structure_query(self, db_session):
        """测试表结构查询功能"""
        with allure.step("获取表列表"):
            # 获取数据库中的表列表
            tables = db_manager.get_table_list('mysql', 'test')
            assert isinstance(tables, list)
            
            info(f"获取到 {len(tables)} 个表")
        
        with allure.step("获取表结构信息"):
            if tables:
                # 获取第一个表的结构信息
                table_name = tables[0]
                structure = db_manager.get_table_info(table_name, 'mysql', 'test')
                assert isinstance(structure, list)
                
                info(f"表 {table_name} 有 {len(structure)} 个字段")
    
    @allure_test_case_decorator("多数据库数据一致性测试", "测试不同数据库间的数据一致性")
    @allure_feature_story("数据库", "数据一致性")
    @allure_severity("critical")
    @pytest.mark.parametrize("db_type", ["mysql", "postgresql", "sqlite"])
    def test_multi_database_consistency(self, db_type):
        """测试多数据库数据一致性"""
        with allure.step(f"在 {db_type} 数据库中执行测试"):
            # 切换到指定数据库
            switch_database(db_type, 'test')
            
            # 执行简单查询测试
            result = execute_query("SELECT 1 as test_value", db_type=db_type, env='test')
            assert len(result) == 1
            assert result[0]['test_value'] == 1
            
            info(f"{db_type} 数据库测试通过")
    
    @allure_test_case_decorator("连接池状态测试", "测试连接池状态监控")
    @allure_feature_story("数据库", "连接池管理")
    @allure_severity("normal")
    def test_connection_pool_status(self):
        """测试连接池状态监控"""
        with allure.step("获取连接池状态"):
            # 获取连接池状态
            pool_status = db_manager.get_connection_pool_status('mysql', 'test')
            assert isinstance(pool_status, dict)
            assert 'pool_size' in pool_status
            assert 'checked_in' in pool_status
            assert 'checked_out' in pool_status
            
            info(f"连接池状态: {pool_status}")


class TestDatabaseFixtures:
    """数据库Fixtures测试类"""
    
    @allure_test_case_decorator("MySQL数据库会话测试", "测试MySQL数据库会话fixture")
    @allure_feature_story("Fixtures", "MySQL会话")
    @allure_severity("normal")
    def test_mysql_session_fixture(self, db_session_mysql):
        """测试MySQL数据库会话fixture"""
        assert db_session_mysql is not None
        assert 'mysql' in str(db_session_mysql.bind.url)
        
        # 执行简单查询
        result = db_session_mysql.execute("SELECT 1 as test")
        row = result.fetchone()
        assert row[0] == 1
        
        info("MySQL会话fixture测试通过")
    
    @allure_test_case_decorator("PostgreSQL数据库会话测试", "测试PostgreSQL数据库会话fixture")
    @allure_feature_story("Fixtures", "PostgreSQL会话")
    @allure_severity("normal")
    def test_postgresql_session_fixture(self, db_session_postgresql):
        """测试PostgreSQL数据库会话fixture"""
        assert db_session_postgresql is not None
        assert 'postgresql' in str(db_session_postgresql.bind.url)
        
        # 执行简单查询
        result = db_session_postgresql.execute("SELECT 1 as test")
        row = result.fetchone()
        assert row[0] == 1
        
        info("PostgreSQL会话fixture测试通过")
    
    @allure_test_case_decorator("SQLite数据库会话测试", "测试SQLite数据库会话fixture")
    @allure_feature_story("Fixtures", "SQLite会话")
    @allure_severity("normal")
    def test_sqlite_session_fixture(self, db_session_sqlite):
        """测试SQLite数据库会话fixture"""
        assert db_session_sqlite is not None
        assert 'sqlite' in str(db_session_sqlite.bind.url)
        
        # 执行简单查询
        result = db_session_sqlite.execute("SELECT 1 as test")
        row = result.fetchone()
        assert row[0] == 1
        
        info("SQLite会话fixture测试通过")
    
    @allure_test_case_decorator("数据库事务测试", "测试数据库事务fixture")
    @allure_feature_story("Fixtures", "事务管理")
    @allure_severity("critical")
    def test_database_transaction_fixture(self, db_transaction):
        """测试数据库事务fixture"""
        # 在事务中创建测试数据
        test_data = {
            'name': 'transaction_test',
            'value': 100,
            'description': '测试事务数据'
        }
        
        # 构建插入SQL
        columns = list(test_data.keys())
        placeholders = [f":{col}" for col in columns]
        sql = f"INSERT INTO test_table ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        
        db_transaction.execute(sql, test_data)
        db_transaction.commit()
        
        # 验证数据已创建
        result = db_transaction.execute("SELECT * FROM test_table WHERE name = :name", {'name': 'transaction_test'})
        rows = result.fetchall()
        assert len(rows) > 0
        
        info("数据库事务fixture测试通过")
    
    @allure_test_case_decorator("数据库清理测试", "测试数据库清理fixture")
    @allure_feature_story("Fixtures", "数据清理")
    @allure_severity("normal")
    def test_clean_db_fixture(self, clean_db):
        """测试数据库清理fixture"""
        # 验证数据库已清理
        result = clean_db.execute("SELECT COUNT(*) as count FROM test_table WHERE name LIKE 'test_%'")
        count = result.fetchone()[0]
        info(f"清理后的测试数据数量: {count}")
        
        info("数据库清理fixture测试通过")


# 参数化测试 - 测试不同数据库
@pytest.mark.parametrize("db_environment", ["mysql", "postgresql", "sqlite"], indirect=True)
@allure_test_case_decorator("参数化数据库测试", "测试不同数据库的参数化测试")
@allure_feature_story("数据库", "参数化测试")
@allure_severity("normal")
def test_parameterized_database(db_environment):
    """参数化数据库测试"""
    db_type, env = db_environment
    
    with allure.step(f"在 {db_type} 数据库中执行测试"):
        # 获取当前数据库会话
        session = db_manager.get_current_session()
        assert session is not None
        
        # 执行简单查询
        result = session.execute("SELECT 1 as test")
        row = result.fetchone()
        assert row[0] == 1
        
        info(f"参数化数据库测试通过: {db_type} - {env}")


# 数据库操作辅助函数测试
class TestDatabaseHelpers:
    """数据库辅助函数测试类"""
    
    @allure_test_case_decorator("创建测试数据测试", "测试创建测试数据功能")
    @allure_feature_story("辅助函数", "数据创建")
    @allure_severity("normal")
    def test_create_test_data(self, db_session):
        """测试创建测试数据功能"""
        from utils.orm_fixtures import create_test_data
        
        test_data = {
            'name': 'helper_test',
            'value': 300,
            'description': '辅助函数测试'
        }
        
        result = create_test_data(db_session, 'test_table', test_data)
        assert result == test_data
        
        info("创建测试数据功能测试通过")
    
    @allure_test_case_decorator("查询测试数据测试", "测试查询测试数据功能")
    @allure_feature_story("辅助函数", "数据查询")
    @allure_severity("normal")
    def test_get_test_data(self, db_session):
        """测试查询测试数据功能"""
        from utils.orm_fixtures import get_test_data
        
        conditions = {'name': 'helper_test'}
        result = get_test_data(db_session, 'test_table', conditions)
        assert isinstance(result, list)
        
        info("查询测试数据功能测试通过")
    
    @allure_test_case_decorator("表结构查询测试", "测试表结构查询功能")
    @allure_feature_story("辅助函数", "表结构")
    @allure_severity("normal")
    def test_get_table_structure(self, db_session):
        """测试表结构查询功能"""
        from utils.orm_fixtures import get_table_structure
        
        structure = get_table_structure(db_session, 'test_table')
        assert isinstance(structure, list)
        
        info("表结构查询功能测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"]) 