# coding: utf-8
# @Author: bgtech

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
import json
from datetime import datetime
import sqlite3
import os

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入数据库驱动
try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    logger.warning("MySQL驱动未安装，MySQL功能不可用")

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False
    logger.warning("PostgreSQL驱动未安装，PostgreSQL功能不可用")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis驱动未安装，Redis功能不可用")

# 导入配置相关模块
try:
    from common.yaml_utils import load_yaml
    from common.interface_config import get_env_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logger.warning("配置模块不可用，无法从配置文件获取数据库连接信息")

class DatabaseConnection(ABC):
    """
    数据库连接抽象基类
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        初始化数据库连接
        :param connection_params: 连接参数
        """
        self.connection_params = connection_params
        self.connection = None
        self.cursor = None
    
    @abstractmethod
    def connect(self) -> bool:
        """
        建立数据库连接
        :return: 连接是否成功
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """
        断开数据库连接
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        执行查询语句
        :param query: SQL查询语句
        :param params: 查询参数
        :return: 查询结果
        """
        pass
    
    @abstractmethod
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行更新语句
        :param query: SQL更新语句
        :param params: 更新参数
        :return: 影响的行数
        """
        pass
    
    @abstractmethod
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行插入语句
        :param query: SQL插入语句
        :param params: 插入参数
        :return: 插入的行数
        """
        pass
    
    @abstractmethod
    def execute_delete(self, query: str, params: Optional[Tuple] = None) -> int:
        """
        执行删除语句
        :param query: SQL删除语句
        :param params: 删除参数
        :return: 删除的行数
        """
        pass

class MySQLConnection(DatabaseConnection):
    """
    MySQL数据库连接类
    """
    
    def connect(self) -> bool:
        """建立MySQL连接"""
        if not MYSQL_AVAILABLE:
            raise ImportError("MySQL驱动未安装，请运行: pip install pymysql")
        
        try:
            self.connection = pymysql.connect(
                host=self.connection_params.get('host'),
                port=self.connection_params.get('port'),
                user=self.connection_params.get('user'),
                password=self.connection_params.get('password'),
                database=self.connection_params.get('database'),
                charset=self.connection_params.get('charset'),
                autocommit=self.connection_params.get('autocommit')
            )
            self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
            logger.info("MySQL连接成功")
            return True
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开MySQL连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("MySQL连接已断开")
        except Exception as e:
            logger.error(f"MySQL断开连接失败: {e}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行MySQL查询"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"MySQL查询失败: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行MySQL更新"""
        try:
            rows_affected = self.cursor.execute(query, params)
            self.connection.commit()
            return rows_affected
        except Exception as e:
            self.connection.rollback()
            logger.error(f"MySQL更新失败: {e}")
            raise
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行MySQL插入"""
        try:
            rows_affected = self.cursor.execute(query, params)
            self.connection.commit()
            return rows_affected
        except Exception as e:
            self.connection.rollback()
            logger.error(f"MySQL插入失败: {e}")
            raise
    
    def execute_delete(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行MySQL删除"""
        try:
            rows_affected = self.cursor.execute(query, params)
            self.connection.commit()
            return rows_affected
        except Exception as e:
            self.connection.rollback()
            logger.error(f"MySQL删除失败: {e}")
            raise

class PostgreSQLConnection(DatabaseConnection):
    """
    PostgreSQL数据库连接类
    """
    
    def connect(self) -> bool:
        """建立PostgreSQL连接"""
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL驱动未安装，请运行: pip install psycopg2-binary")
        
        try:
            self.connection = psycopg2.connect(
                host=self.connection_params.get('host'),
                port=self.connection_params.get('port'),
                user=self.connection_params.get('user'),
                password=self.connection_params.get('password'),
                database=self.connection_params.get('database'),
                autocommit=self.connection_params.get('autocommit')
            )
            self.cursor = self.connection.cursor()
            logger.info("PostgreSQL连接成功")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开PostgreSQL连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("PostgreSQL连接已断开")
        except Exception as e:
            logger.error(f"PostgreSQL断开连接失败: {e}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行PostgreSQL查询"""
        try:
            self.cursor.execute(query, params)
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"PostgreSQL查询失败: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行PostgreSQL更新"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"PostgreSQL更新失败: {e}")
            raise
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行PostgreSQL插入"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"PostgreSQL插入失败: {e}")
            raise
    
    def execute_delete(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行PostgreSQL删除"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"PostgreSQL删除失败: {e}")
            raise

class RedisConnection(DatabaseConnection):
    """
    Redis数据库连接类
    """
    
    def connect(self) -> bool:
        """建立Redis连接"""
        if not REDIS_AVAILABLE:
            raise ImportError("Redis驱动未安装，请运行: pip install redis")
        
        try:
            self.connection = redis.Redis(
                host=self.connection_params.get('host'),
                port=self.connection_params.get('port'),
                password=self.connection_params.get('password'),
                db=self.connection_params.get('db'),
                decode_responses=True
            )
            # 测试连接
            self.connection.ping()
            logger.info("Redis连接成功")
            return True
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开Redis连接"""
        try:
            if self.connection:
                self.connection.close()
            logger.info("Redis连接已断开")
        except Exception as e:
            logger.error(f"Redis断开连接失败: {e}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行Redis查询（模拟）"""
        try:
            # Redis没有传统SQL查询，这里返回连接信息
            return [{"status": "connected", "info": self.connection.info()}]
        except Exception as e:
            logger.error(f"Redis查询失败: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行Redis更新（模拟）"""
        try:
            # Redis更新操作
            return 1
        except Exception as e:
            logger.error(f"Redis更新失败: {e}")
            raise
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行Redis插入（模拟）"""
        try:
            # Redis插入操作
            return 1
        except Exception as e:
            logger.error(f"Redis插入失败: {e}")
            raise
    
    def execute_delete(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行Redis删除（模拟）"""
        try:
            # Redis删除操作
            return 1
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            raise

class SQLiteConnection(DatabaseConnection):
    """
    SQLite数据库连接类
    """
    
    def connect(self) -> bool:
        """建立SQLite连接"""
        try:
            self.connection = sqlite3.connect(
                self.connection_params.get('database'),
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            logger.info("SQLite连接成功")
            return True
        except Exception as e:
            logger.error(f"SQLite连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SQLite连接"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("SQLite连接已断开")
        except Exception as e:
            logger.error(f"SQLite断开连接失败: {e}")
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """执行SQLite查询"""
        try:
            self.cursor.execute(query, params or ())
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"SQLite查询失败: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行SQLite更新"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"SQLite更新失败: {e}")
            raise
    
    def execute_insert(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行SQLite插入"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"SQLite插入失败: {e}")
            raise
    
    def execute_delete(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行SQLite删除"""
        try:
            self.cursor.execute(query, params or ())
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            logger.error(f"SQLite删除失败: {e}")
            raise

class RequestDB:
    """
    数据库操作工具类
    支持MySQL、PostgreSQL、Redis、SQLite等多种数据库类型
    """
    
    def __init__(self, db_type: str = None, connection_params: Dict[str, Any] = None, 
                 env: str = None, config_file: str = 'conf/database.yaml'):
        """
        初始化数据库操作工具
        :param db_type: 数据库类型 (mysql, postgresql, redis, sqlite)
        :param connection_params: 连接参数
        :param env: 环境名称 (dev, test, prod)
        :param config_file: 配置文件路径
        """
        self.config_file = config_file
        self.env = env or self._get_current_env()
        self.db_type = db_type or self._get_default_db_type()
        self.connection_params = connection_params or self._get_db_config()
        self.db_connection = self._create_connection()
    
    def _get_current_env(self) -> str:
        """
        获取当前环境
        :return: 当前环境名称
        """
        if CONFIG_AVAILABLE:
            try:
                env_config = get_env_config()
                return env_config.get('current', 'dev')
            except:
                pass
        return 'dev'
    
    def _get_default_db_type(self) -> str:
        """
        获取默认数据库类型
        :return: 默认数据库类型
        """
        if CONFIG_AVAILABLE:
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                config_path = os.path.join(base_dir, self.config_file)
                if os.path.exists(config_path):
                    config_data = load_yaml(config_path)
                    return config_data.get('database', {}).get('default_type', 'mysql')
            except:
                pass
        return 'mysql'
    
    def _get_db_config(self) -> Dict[str, Any]:
        """
        从配置文件获取数据库连接配置
        :return: 数据库连接配置
        """
        if not CONFIG_AVAILABLE:
            logger.warning("配置模块不可用，使用默认配置")
            return self._get_default_config()
        
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, self.config_file)
            
            if not os.path.exists(config_path):
                logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
                return self._get_default_config()
            
            config_data = load_yaml(config_path)
            database_config = config_data.get('database', {})
            
            # 获取指定数据库类型的配置
            db_config = database_config.get(self.db_type, {})
            if not db_config:
                logger.warning(f"未找到数据库类型 {self.db_type} 的配置，使用默认配置")
                return self._get_default_config()
            
            # 获取指定环境的配置
            env_config = db_config.get(self.env, {})
            if not env_config:
                logger.warning(f"未找到环境 {self.env} 的配置，使用默认配置")
                return self._get_default_config()
            
            logger.info(f"从配置文件加载数据库配置: {self.db_type} - {self.env}")
            return env_config
            
        except Exception as e:
            logger.error(f"加载数据库配置失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认数据库配置
        :return: 默认配置
        """
        if not CONFIG_AVAILABLE:
            return self._get_fallback_config()
        
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, self.config_file)
            
            if not os.path.exists(config_path):
                logger.warning(f"配置文件不存在: {config_path}，使用fallback配置")
                return self._get_fallback_config()
            
            config_data = load_yaml(config_path)
            database_config = config_data.get('database', {})
            
            # 获取指定数据库类型的配置
            db_config = database_config.get(self.db_type, {})
            if not db_config:
                logger.warning(f"未找到数据库类型 {self.db_type} 的配置，使用fallback配置")
                return self._get_fallback_config()
            
            # 尝试获取dev环境的配置作为默认配置
            default_config = db_config.get('dev', {})
            if not default_config:
                # 如果没有dev环境，尝试获取第一个可用的环境配置
                available_envs = list(db_config.keys())
                if available_envs:
                    default_config = db_config[available_envs[0]]
                    logger.info(f"使用环境 {available_envs[0]} 的配置作为默认配置")
                else:
                    logger.warning(f"数据库类型 {self.db_type} 没有可用的环境配置，使用fallback配置")
                    return self._get_fallback_config()
            
            logger.info(f"从配置文件加载默认配置: {self.db_type}")
            return default_config
            
        except Exception as e:
            logger.error(f"加载默认配置失败: {e}，使用fallback配置")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """
        获取fallback配置（当配置文件不可用时使用）
        :return: fallback配置
        """
        if self.db_type == 'mysql':
            return {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'test_db',
                'charset': 'utf8mb4',
                'autocommit': True
            }
        elif self.db_type == 'postgresql':
            return {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': '',
                'database': 'test_db',
                'autocommit': True
            }
        elif self.db_type == 'redis':
            return {
                'host': 'localhost',
                'port': 6379,
                'password': None,
                'db': 0
            }
        elif self.db_type == 'sqlite':
            return {
                'database': 'test.db'
            }
        else:
            return {}
    
    def _create_connection(self) -> DatabaseConnection:
        """
        创建数据库连接
        :return: 数据库连接对象
        """
        if self.db_type == 'mysql':
            return MySQLConnection(self.connection_params)
        elif self.db_type == 'postgresql':
            return PostgreSQLConnection(self.connection_params)
        elif self.db_type == 'redis':
            return RedisConnection(self.connection_params)
        elif self.db_type == 'sqlite':
            return SQLiteConnection(self.connection_params)
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")
    
    def connect(self) -> bool:
        """
        建立数据库连接
        :return: 连接是否成功
        """
        return self.db_connection.connect()
    
    def disconnect(self):
        """
        断开数据库连接
        """
        self.db_connection.disconnect()
    
    def query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        执行查询操作 (Read)
        :param sql: SQL查询语句
        :param params: 查询参数
        :return: 查询结果
        """
        return self.db_connection.execute_query(sql, params)
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        执行插入操作 (Create)
        :param table: 表名
        :param data: 插入数据
        :return: 插入的行数
        """
        if self.db_type == 'redis':
            return self._redis_insert(table, data)
        else:
            return self._sql_insert(table, data)
    
    def update(self, table: str, data: Dict[str, Any], condition: str, params: Optional[Tuple] = None) -> int:
        """
        执行更新操作 (Update)
        :param table: 表名
        :param data: 更新数据
        :param condition: 更新条件
        :param params: 条件参数
        :return: 更新的行数
        """
        if self.db_type == 'redis':
            return self._redis_update(table, data, condition)
        else:
            return self._sql_update(table, data, condition, params)
    
    def delete(self, table: str, condition: str, params: Optional[Tuple] = None) -> int:
        """
        执行删除操作 (Delete)
        :param table: 表名
        :param condition: 删除条件
        :param params: 条件参数
        :return: 删除的行数
        """
        if self.db_type == 'redis':
            return self._redis_delete(table, condition)
        else:
            return self._sql_delete(table, condition, params)
    
    def _sql_insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        SQL插入操作
        """
        columns = ', '.join(data.keys())
        if self.db_type == 'sqlite':
            placeholders = ', '.join(['?'] * len(data))
        else:
            placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.db_connection.execute_insert(sql, tuple(data.values()))
    
    def _sql_update(self, table: str, data: Dict[str, Any], condition: str, params: Optional[Tuple] = None) -> int:
        """
        SQL更新操作
        """
        if self.db_type == 'sqlite':
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        else:
            set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        all_params = tuple(data.values()) + (params or ())
        return self.db_connection.execute_update(sql, all_params)
    
    def _sql_delete(self, table: str, condition: str, params: Optional[Tuple] = None) -> int:
        """
        SQL删除操作
        """
        sql = f"DELETE FROM {table} WHERE {condition}"
        return self.db_connection.execute_delete(sql, params)
    
    def _redis_insert(self, key: str, data: Dict[str, Any]) -> int:
        """
        Redis插入操作
        """
        try:
            if isinstance(data, dict):
                self.db_connection.connection.hmset(key, data)
            else:
                self.db_connection.connection.set(key, json.dumps(data))
            return 1
        except Exception as e:
            logger.error(f"Redis插入失败: {e}")
            raise
    
    def _redis_update(self, key: str, data: Dict[str, Any], condition: str) -> int:
        """
        Redis更新操作
        """
        try:
            if self.db_connection.connection.exists(key):
                if isinstance(data, dict):
                    self.db_connection.connection.hmset(key, data)
                else:
                    self.db_connection.connection.set(key, json.dumps(data))
                return 1
            return 0
        except Exception as e:
            logger.error(f"Redis更新失败: {e}")
            raise
    
    def _redis_delete(self, key: str, condition: str) -> int:
        """
        Redis删除操作
        """
        try:
            if self.db_connection.connection.exists(key):
                self.db_connection.connection.delete(key)
                return 1
            return 0
        except Exception as e:
            logger.error(f"Redis删除失败: {e}")
            raise
    
    def execute_raw_sql(self, sql: str, params: Optional[Tuple] = None) -> Union[List[Dict], int]:
        """
        执行原始SQL语句
        :param sql: SQL语句
        :param params: 参数
        :return: 查询结果或影响行数
        """
        sql_upper = sql.strip().upper()
        if sql_upper.startswith('SELECT'):
            return self.db_connection.execute_query(sql, params)
        elif sql_upper.startswith('INSERT'):
            return self.db_connection.execute_insert(sql, params)
        elif sql_upper.startswith('UPDATE'):
            return self.db_connection.execute_update(sql, params)
        elif sql_upper.startswith('DELETE'):
            return self.db_connection.execute_delete(sql, params)
        else:
            return self.db_connection.execute_query(sql, params)
    
    def get_table_info(self, table: str) -> List[Dict]:
        """
        获取表结构信息
        :param table: 表名
        :return: 表结构信息
        """
        if self.db_type == 'mysql':
            sql = f"DESCRIBE {table}"
        elif self.db_type == 'postgresql':
            sql = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """
            return self.query(sql, (table,))
        elif self.db_type == 'sqlite':
            sql = f"PRAGMA table_info({table})"
        else:
            return []
        
        return self.query(sql)
    
    def get_tables(self) -> List[str]:
        """
        获取所有表名
        :return: 表名列表
        """
        if self.db_type == 'mysql':
            sql = "SHOW TABLES"
        elif self.db_type == 'postgresql':
            sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """
        elif self.db_type == 'sqlite':
            sql = "SELECT name FROM sqlite_master WHERE type='table'"
        else:
            return []
        
        result = self.query(sql)
        if self.db_type == 'mysql':
            return [list(row.values())[0] for row in result]
        else:
            return [row['table_name'] if 'table_name' in row else row['name'] for row in result]

# 便捷函数
def create_db_connection(db_type: str = None, env: str = None, **kwargs) -> RequestDB:
    """
    创建数据库连接的便捷函数
    :param db_type: 数据库类型
    :param env: 环境名称
    :param kwargs: 连接参数
    :return: 数据库操作对象
    """
    return RequestDB(db_type=db_type, env=env, connection_params=kwargs)

def get_db_connection(db_type: str = None, env: str = None) -> RequestDB:
    """
    从配置文件获取数据库连接的便捷函数
    :param db_type: 数据库类型
    :param env: 环境名称
    :return: 数据库操作对象
    """
    return RequestDB(db_type=db_type, env=env)

# 使用示例
if __name__ == "__main__":
    try:
        # 测试从配置文件获取数据库连接
        print("测试从配置文件获取数据库连接...")
        
        # 方式1：使用便捷函数，自动从配置文件获取配置
        db = get_db_connection('mysql', 'dev')
        if db.connect():
            print(f"MySQL连接成功 - 环境: {db.env}, 类型: {db.db_type}")
            result = db.query("SELECT 1 as test")
            print(f"查询结果: {result}")
            db.disconnect()
        
        # 方式2：指定环境，自动获取配置
        db2 = RequestDB(env='test')
        if db2.connect():
            print(f"数据库连接成功 - 环境: {db2.env}, 类型: {db2.db_type}")
            result = db2.query("SELECT 1 as test")
            print(f"查询结果: {result}")
            db2.disconnect()
        
        # 方式3：指定数据库类型和环境
        db3 = RequestDB(db_type='sqlite', env='dev')
        if db3.connect():
            print(f"SQLite连接成功 - 环境: {db3.env}, 类型: {db3.db_type}")
            result = db3.query("SELECT 1 as test")
            print(f"查询结果: {result}")
            db3.disconnect()
        
        # 方式4：手动指定连接参数（覆盖配置文件）
        custom_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'custom_user',
            'password': 'custom_pass',
            'database': 'custom_db'
        }
        db4 = RequestDB('mysql', custom_config, 'dev')
        print(f"自定义配置 - 环境: {db4.env}, 类型: {db4.db_type}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
