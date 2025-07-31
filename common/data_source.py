# coding: utf-8
# @Author: bgtech
import os
import sys
import importlib
from typing import Dict, Any, List, Optional, Union
from common.config import get_config
from common.log import info, error, debug

class DataSourceManager:
    """数据源管理器，支持动态加载多种数据源"""
    
    def __init__(self):
        self._connections = {}
        self._data_cache = {}
        self._db_config = get_config('database')
        
    def get_database_config(self, db_type: str = None, env: str = 'test') -> Dict[str, Any]:
        """
        获取数据库配置
        :param db_type: 数据库类型 (mysql, postgresql, redis, sqlite)
        :param env: 环境 (dev, test, prod)
        :return: 数据库配置字典
        """
        if not self._db_config:
            error("数据库配置未找到")
            return {}
            
        if db_type is None:
            db_type = self._db_config.get('default_type', 'mysql')
            
        db_config = self._db_config.get(db_type, {})
        env_config = db_config.get(env, {})
        
        if not env_config:
            error(f"未找到数据库配置: {db_type}.{env}")
            return {}
            
        return env_config
    
    def get_connection(self, db_type: str = None, env: str = 'test'):
        """
        获取数据库连接
        :param db_type: 数据库类型
        :param env: 环境
        :return: 数据库连接对象
        """
        connection_key = f"{db_type}_{env}"
        
        if connection_key in self._connections:
            return self._connections[connection_key]
            
        config = self.get_database_config(db_type, env)
        if not config:
            return None
            
        try:
            if db_type == 'mysql':
                conn = self._create_mysql_connection(config)
            elif db_type == 'postgresql':
                conn = self._create_postgresql_connection(config)
            elif db_type == 'redis':
                conn = self._create_redis_connection(config)
            elif db_type == 'sqlite':
                conn = self._create_sqlite_connection(config)
            else:
                error(f"不支持的数据库类型: {db_type}")
                return None
                
            if conn:
                self._connections[connection_key] = conn
                info(f"成功创建数据库连接: {connection_key}")
                
            return conn
            
        except Exception as e:
            error(f"创建数据库连接失败: {e}")
            return None
    
    def _create_mysql_connection(self, config: Dict[str, Any]):
        """创建MySQL连接"""
        try:
            import pymysql
            return pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset=config.get('charset', 'utf8mb4'),
                autocommit=config.get('autocommit', True)
            )
        except ImportError:
            error("pymysql未安装，请运行: pip install pymysql")
            return None
        except Exception as e:
            error(f"MySQL连接失败: {e}")
            return None
    
    def _create_postgresql_connection(self, config: Dict[str, Any]):
        """创建PostgreSQL连接"""
        try:
            import psycopg2
            return psycopg2.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database']
            )
        except ImportError:
            error("psycopg2未安装，请运行: pip install psycopg2-binary")
            return None
        except Exception as e:
            error(f"PostgreSQL连接失败: {e}")
            return None
    
    def _create_redis_connection(self, config: Dict[str, Any]):
        """创建Redis连接"""
        try:
            import redis
            return redis.Redis(
                host=config['host'],
                port=config['port'],
                password=config.get('password'),
                db=config.get('db', 0),
                decode_responses=True
            )
        except ImportError:
            error("redis未安装，请运行: pip install redis")
            return None
        except Exception as e:
            error(f"Redis连接失败: {e}")
            return None
    
    def _create_sqlite_connection(self, config: Dict[str, Any]):
        """创建SQLite连接"""
        try:
            import sqlite3
            db_path = config['database']
            if not os.path.isabs(db_path):
                # 相对于项目根目录
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(project_root, db_path)
            return sqlite3.connect(db_path)
        except Exception as e:
            error(f"SQLite连接失败: {e}")
            return None
    
    def query_data(self, sql: str, db_type: str = None, env: str = 'test', 
                   params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        :param sql: SQL语句
        :param db_type: 数据库类型
        :param env: 环境
        :param params: 查询参数
        :return: 查询结果
        """
        conn = self.get_connection(db_type, env)
        if not conn:
            return []
            
        try:
            if db_type == 'mysql':
                return self._query_mysql(conn, sql, params)
            elif db_type == 'postgresql':
                return self._query_postgresql(conn, sql, params)
            elif db_type == 'sqlite':
                return self._query_sqlite(conn, sql, params)
            else:
                error(f"不支持的数据库类型: {db_type}")
                return []
        except Exception as e:
            error(f"查询数据失败: {e}")
            return []
    
    def _query_mysql(self, conn, sql: str, params: Dict[str, Any] = None):
        """MySQL查询"""
        import pymysql
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
    
    def _query_postgresql(self, conn, sql: str, params: Dict[str, Any] = None):
        """PostgreSQL查询"""
        import psycopg2.extras
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    
    def _query_sqlite(self, conn, sql: str, params: Dict[str, Any] = None):
        """SQLite查询"""
        with conn.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_redis_data(self, key: str, env: str = 'test') -> Any:
        """
        获取Redis数据
        :param key: Redis键
        :param env: 环境
        :return: Redis数据
        """
        conn = self.get_connection('redis', env)
        if not conn:
            return None
            
        try:
            return conn.get(key)
        except Exception as e:
            error(f"获取Redis数据失败: {e}")
            return None
    
    def set_redis_data(self, key: str, value: Any, env: str = 'test', 
                       expire: int = None) -> bool:
        """
        设置Redis数据
        :param key: Redis键
        :param value: 值
        :param env: 环境
        :param expire: 过期时间（秒）
        :return: 是否成功
        """
        conn = self.get_connection('redis', env)
        if not conn:
            return False
            
        try:
            conn.set(key, value)
            if expire:
                conn.expire(key, expire)
            return True
        except Exception as e:
            error(f"设置Redis数据失败: {e}")
            return False
    
    def load_test_data_from_db(self, sql: str, db_type: str = None, 
                              env: str = 'test', cache_key: str = None) -> List[Dict[str, Any]]:
        """
        从数据库加载测试数据
        :param sql: 查询SQL
        :param db_type: 数据库类型
        :param env: 环境
        :param cache_key: 缓存键
        :return: 测试数据列表
        """
        if cache_key and cache_key in self._data_cache:
            debug(f"使用缓存数据: {cache_key}")
            return self._data_cache[cache_key]
            
        data = self.query_data(sql, db_type, env)
        
        if cache_key:
            self._data_cache[cache_key] = data
            debug(f"缓存数据: {cache_key} ({len(data)} 条)")
            
        return data
    
    def close_all_connections(self):
        """关闭所有数据库连接"""
        for key, conn in self._connections.items():
            try:
                conn.close()
                info(f"关闭数据库连接: {key}")
            except Exception as e:
                error(f"关闭数据库连接失败 {key}: {e}")
        self._connections.clear()
        self._data_cache.clear()

# 全局数据源管理器实例
data_source_manager = DataSourceManager()

# 便捷函数
def get_db_data(sql: str, db_type: str = None, env: str = 'test', 
                params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    获取数据库数据的便捷函数
    """
    return data_source_manager.query_data(sql, db_type, env, params)

def get_test_data_from_db(sql: str, db_type: str = None, env: str = 'test', 
                          cache_key: str = None) -> List[Dict[str, Any]]:
    """
    从数据库获取测试数据的便捷函数
    """
    return data_source_manager.load_test_data_from_db(sql, db_type, env, cache_key)

def get_redis_value(key: str, env: str = 'test') -> Any:
    """
    获取Redis值的便捷函数
    """
    return data_source_manager.get_redis_data(key, env)

def set_redis_value(key: str, value: Any, env: str = 'test', expire: int = None) -> bool:
    """
    设置Redis值的便捷函数
    """
    return data_source_manager.set_redis_data(key, value, env, expire) 