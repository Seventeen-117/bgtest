# coding: utf-8
# @Author: bgtech
"""
SQLAlchemy 数据库管理器
支持多数据库切换、会话管理和事务控制
专注于通过配置文件连接数据库
"""

import os
from typing import Dict, Any, Optional, List, Union
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from common.log import info, error, debug
from common.data_source import DataSourceManager


class DatabaseManager:
    """数据库管理器，支持多数据库切换"""
    
    def __init__(self):
        self._engines = {}
        self._sessions = {}
        self._data_source_manager = DataSourceManager()
        self._current_db_type = None
        self._current_env = 'test'
        
    def get_database_url(self, db_type: str, env: str = 'test') -> str:
        """
        根据数据库类型和环境生成数据库URL
        :param db_type: 数据库类型 (mysql, postgresql, sqlite)
        :param env: 环境 (dev, test, prod)
        :return: 数据库URL
        """
        config = self._data_source_manager.get_database_config(db_type, env)
        if not config:
            error(f"未找到数据库配置: {db_type} - {env}")
            return None
            
        try:
            if db_type == 'mysql':
                return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config.get('charset', 'utf8mb4')}"
            elif db_type == 'postgresql':
                return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
            elif db_type == 'sqlite':
                db_path = config['database']
                if not os.path.isabs(db_path):
                    # 相对路径转换为绝对路径
                    project_root = self._data_source_manager._config_manager.get_project_root()
                    db_path = os.path.join(project_root, db_path)
                return f"sqlite:///{db_path}"
            else:
                error(f"不支持的数据库类型: {db_type}")
                return None
                
        except Exception as e:
            error(f"生成数据库URL失败: {e}")
            return None
    
    def get_engine(self, db_type: str, env: str = 'test'):
        """
        获取数据库引擎
        :param db_type: 数据库类型
        :param env: 环境
        :return: SQLAlchemy引擎
        """
        engine_key = f"{db_type}_{env}"
        
        if engine_key in self._engines:
            return self._engines[engine_key]
            
        url = self.get_database_url(db_type, env)
        if not url:
            return None
            
        try:
            # 创建引擎，配置连接池
            engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # 设置为True可以看到SQL语句
            )
            
            self._engines[engine_key] = engine
            info(f"成功创建数据库引擎: {engine_key}")
            
            return engine
            
        except Exception as e:
            error(f"创建数据库引擎失败: {e}")
            return None
    
    def get_session(self, db_type: str, env: str = 'test') -> Optional[Session]:
        """
        获取数据库会话
        :param db_type: 数据库类型
        :param env: 环境
        :return: SQLAlchemy会话
        """
        session_key = f"{db_type}_{env}"
        
        if session_key in self._sessions:
            return self._sessions[session_key]
            
        engine = self.get_engine(db_type, env)
        if not engine:
            return None
            
        try:
            # 创建会话工厂
            SessionFactory = sessionmaker(bind=engine)
            session = SessionFactory()
            
            self._sessions[session_key] = session
            info(f"成功创建数据库会话: {session_key}")
            
            return session
            
        except Exception as e:
            error(f"创建数据库会话失败: {e}")
            return None
    
    @contextmanager
    def get_session_context(self, db_type: str, env: str = 'test'):
        """
        获取数据库会话上下文管理器
        :param db_type: 数据库类型
        :param env: 环境
        :yield: SQLAlchemy会话
        """
        session = self.get_session(db_type, env)
        if not session:
            raise Exception(f"无法获取数据库会话: {db_type} - {env}")
            
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def switch_database(self, db_type: str, env: str = 'test'):
        """
        切换数据库
        :param db_type: 数据库类型
        :param env: 环境
        """
        self._current_db_type = db_type
        self._current_env = env
        info(f"切换到数据库: {db_type} - {env}")
    
    def get_current_session(self) -> Optional[Session]:
        """
        获取当前数据库会话
        :return: SQLAlchemy会话
        """
        if not self._current_db_type:
            error("未设置当前数据库类型")
            return None
            
        return self.get_session(self._current_db_type, self._current_env)
    
    @contextmanager
    def get_current_session_context(self):
        """
        获取当前数据库会话上下文管理器
        :yield: SQLAlchemy会话
        """
        if not self._current_db_type:
            raise Exception("未设置当前数据库类型")
            
        with self.get_session_context(self._current_db_type, self._current_env) as session:
            yield session
    
    def execute_raw_sql(self, sql: str, params: Dict[str, Any] = None, 
                        db_type: str = None, env: str = 'test') -> List[Dict[str, Any]]:
        """
        执行原始SQL语句
        :param sql: SQL语句
        :param params: 参数
        :param db_type: 数据库类型
        :param env: 环境
        :return: 查询结果
        """
        if db_type is None:
            db_type = self._current_db_type
            
        with self.get_session_context(db_type, env) as session:
            try:
                result = session.execute(text(sql), params or {})
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                else:
                    return []
            except Exception as e:
                error(f"执行SQL失败: {e}")
                raise
    
    def execute_query(self, sql: str, params: Dict[str, Any] = None, 
                     db_type: str = None, env: str = 'test') -> List[Dict[str, Any]]:
        """
        执行查询SQL语句
        :param sql: 查询SQL语句
        :param params: 参数
        :param db_type: 数据库类型
        :param env: 环境
        :return: 查询结果
        """
        return self.execute_raw_sql(sql, params, db_type, env)
    
    def execute_update(self, sql: str, params: Dict[str, Any] = None, 
                      db_type: str = None, env: str = 'test') -> int:
        """
        执行更新SQL语句
        :param sql: 更新SQL语句
        :param params: 参数
        :param db_type: 数据库类型
        :param env: 环境
        :return: 影响的行数
        """
        if db_type is None:
            db_type = self._current_db_type
            
        with self.get_session_context(db_type, env) as session:
            try:
                result = session.execute(text(sql), params or {})
                return result.rowcount
            except Exception as e:
                error(f"执行更新SQL失败: {e}")
                raise
    
    def execute_insert(self, sql: str, params: Dict[str, Any] = None, 
                      db_type: str = None, env: str = 'test') -> int:
        """
        执行插入SQL语句
        :param sql: 插入SQL语句
        :param params: 参数
        :param db_type: 数据库类型
        :param env: 环境
        :return: 影响的行数
        """
        return self.execute_update(sql, params, db_type, env)
    
    def execute_delete(self, sql: str, params: Dict[str, Any] = None, 
                      db_type: str = None, env: str = 'test') -> int:
        """
        执行删除SQL语句
        :param sql: 删除SQL语句
        :param params: 参数
        :param db_type: 数据库类型
        :param env: 环境
        :return: 影响的行数
        """
        return self.execute_update(sql, params, db_type, env)
    
    def test_connection(self, db_type: str, env: str = 'test') -> bool:
        """
        测试数据库连接
        :param db_type: 数据库类型
        :param env: 环境
        :return: 连接是否成功
        """
        try:
            with self.get_session_context(db_type, env) as session:
                # 执行简单查询测试连接
                if db_type == 'mysql':
                    result = session.execute(text("SELECT 1"))
                elif db_type == 'postgresql':
                    result = session.execute(text("SELECT 1"))
                elif db_type == 'sqlite':
                    result = session.execute(text("SELECT 1"))
                else:
                    return False
                    
                result.fetchone()
                info(f"数据库连接测试成功: {db_type} - {env}")
                return True
                
        except Exception as e:
            error(f"数据库连接测试失败: {db_type} - {env}, 错误: {e}")
            return False
    
    def get_table_info(self, table_name: str, db_type: str = None, env: str = 'test') -> List[Dict[str, Any]]:
        """
        获取表结构信息
        :param table_name: 表名
        :param db_type: 数据库类型
        :param env: 环境
        :return: 表结构信息
        """
        if db_type is None:
            db_type = self._current_db_type
            
        try:
            if db_type == 'mysql':
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
            elif db_type == 'postgresql':
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
            elif db_type == 'sqlite':
                sql = "PRAGMA table_info(:table_name)"
            else:
                error(f"不支持的数据库类型: {db_type}")
                return []
            
            result = self.execute_query(sql, {'table_name': table_name}, db_type, env)
            info(f"获取表结构信息成功: {table_name}")
            return result
            
        except Exception as e:
            error(f"获取表结构信息失败: {e}")
            return []
    
    def get_table_list(self, db_type: str = None, env: str = 'test') -> List[str]:
        """
        获取数据库中的所有表名
        :param db_type: 数据库类型
        :param env: 环境
        :return: 表名列表
        """
        if db_type is None:
            db_type = self._current_db_type
            
        try:
            if db_type == 'mysql':
                sql = "SHOW TABLES"
            elif db_type == 'postgresql':
                sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                """
            elif db_type == 'sqlite':
                sql = "SELECT name FROM sqlite_master WHERE type='table'"
            else:
                error(f"不支持的数据库类型: {db_type}")
                return []
            
            result = self.execute_query(sql, db_type=db_type, env=env)
            table_names = []
            for row in result:
                table_name = list(row.values())[0]  # 获取第一个值作为表名
                table_names.append(table_name)
            
            info(f"获取表列表成功: {len(table_names)} 个表")
            return table_names
            
        except Exception as e:
            error(f"获取表列表失败: {e}")
            return []
    
    def get_database_info(self, db_type: str, env: str = 'test') -> Dict[str, Any]:
        """
        获取数据库信息
        :param db_type: 数据库类型
        :param env: 环境
        :return: 数据库信息
        """
        config = self._data_source_manager.get_database_config(db_type, env)
        if not config:
            return {}
            
        return {
            'type': db_type,
            'environment': env,
            'host': config.get('host'),
            'port': config.get('port'),
            'database': config.get('database'),
            'user': config.get('user'),
            'connected': self.test_connection(db_type, env),
            'tables': self.get_table_list(db_type, env)
        }
    
    def close_all_connections(self):
        """关闭所有数据库连接"""
        try:
            # 关闭所有会话
            for session in self._sessions.values():
                if session:
                    session.close()
            self._sessions.clear()
            
            # 关闭所有引擎
            for engine in self._engines.values():
                if engine:
                    engine.dispose()
            self._engines.clear()
            
            info("已关闭所有数据库连接")
            
        except Exception as e:
            error(f"关闭数据库连接失败: {e}")
    
    def get_connection_pool_status(self, db_type: str = None, env: str = 'test') -> Dict[str, Any]:
        """
        获取连接池状态
        :param db_type: 数据库类型
        :param env: 环境
        :return: 连接池状态信息
        """
        if db_type is None:
            db_type = self._current_db_type
            
        engine = self.get_engine(db_type, env)
        if not engine:
            return {}
            
        pool = engine.pool
        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'invalid': pool.invalid()
        }


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 便捷函数
def get_db_session(db_type: str = None, env: str = 'test') -> Optional[Session]:
    """
    获取数据库会话
    :param db_type: 数据库类型
    :param env: 环境
    :return: SQLAlchemy会话
    """
    if db_type:
        return db_manager.get_session(db_type, env)
    else:
        return db_manager.get_current_session()


def switch_database(db_type: str, env: str = 'test'):
    """
    切换数据库
    :param db_type: 数据库类型
    :param env: 环境
    """
    db_manager.switch_database(db_type, env)


def execute_sql(sql: str, params: Dict[str, Any] = None, 
                db_type: str = None, env: str = 'test') -> List[Dict[str, Any]]:
    """
    执行SQL语句
    :param sql: SQL语句
    :param params: 参数
    :param db_type: 数据库类型
    :param env: 环境
    :return: 查询结果
    """
    return db_manager.execute_raw_sql(sql, params, db_type, env)


def execute_query(sql: str, params: Dict[str, Any] = None, 
                 db_type: str = None, env: str = 'test') -> List[Dict[str, Any]]:
    """
    执行查询SQL语句
    :param sql: 查询SQL语句
    :param params: 参数
    :param db_type: 数据库类型
    :param env: 环境
    :return: 查询结果
    """
    return db_manager.execute_query(sql, params, db_type, env)


def execute_update(sql: str, params: Dict[str, Any] = None, 
                  db_type: str = None, env: str = 'test') -> int:
    """
    执行更新SQL语句
    :param sql: 更新SQL语句
    :param params: 参数
    :param db_type: 数据库类型
    :param env: 环境
    :return: 影响的行数
    """
    return db_manager.execute_update(sql, params, db_type, env)


def test_db_connection(db_type: str, env: str = 'test') -> bool:
    """
    测试数据库连接
    :param db_type: 数据库类型
    :param env: 环境
    :return: 连接是否成功
    """
    return db_manager.test_connection(db_type, env)


def get_table_info(table_name: str, db_type: str = None, env: str = 'test') -> List[Dict[str, Any]]:
    """
    获取表结构信息
    :param table_name: 表名
    :param db_type: 数据库类型
    :param env: 环境
    :return: 表结构信息
    """
    return db_manager.get_table_info(table_name, db_type, env)


def get_table_list(db_type: str = None, env: str = 'test') -> List[str]:
    """
    获取数据库中的所有表名
    :param db_type: 数据库类型
    :param env: 环境
    :return: 表名列表
    """
    return db_manager.get_table_list(db_type, env) 