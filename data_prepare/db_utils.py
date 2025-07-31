import pymysql

# 数据库连接工具

def get_connection(host, port, user, password, database):
    """
    获取数据库连接
    :param host: 数据库主机地址
    :param port: 端口号
    :param user: 用户名
    :param password: 密码
    :param database: 数据库名
    :return: pymysql连接对象
    """
    return pymysql.connect(host=host, port=port, user=user, password=password, database=database)


def query(sql, conn):
    """
    执行SQL查询
    :param sql: SQL语句
    :param conn: 数据库连接对象
    :return: 查询结果（元组列表）
    """
    with conn.cursor() as cursor:
        cursor.execute(sql)
        return cursor.fetchall()

# 示例用法：
# conn = get_connection('localhost', 3306, 'user', 'pass', 'testdb')
# result = query('SELECT * FROM users', conn)
# print(result)
# conn.close() 