#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQ工具类
支持RabbitMQ和RocketMQ的消息发送和消费
"""

import json
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from common.log import info, error, debug
from common.yaml_utils import load_yaml
import os

# 尝试导入RabbitMQ相关库
try:
    import pika
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    error("RabbitMQ驱动未安装，请运行: pip install pika")

# 尝试导入RocketMQ相关库
try:
    from rocketmq.client import Producer, PushConsumer, Message, ConsumeStatus
    ROCKETMQ_AVAILABLE = True
except ImportError:
    ROCKETMQ_AVAILABLE = False
    error("RocketMQ驱动未安装，请运行: pip install rocketmq-client-python")

class MQConnection(ABC):
    """MQ连接抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MQ连接
        :param config: MQ配置信息
        """
        self.config = config
        self.connection = None
        self._connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查连接状态"""
        pass

class RabbitMQConnection(MQConnection):
    """RabbitMQ连接类"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.channel = None
    
    def connect(self) -> bool:
        """建立RabbitMQ连接"""
        if not RABBITMQ_AVAILABLE:
            error("RabbitMQ驱动未安装，请运行: pip install pika")
            return False
        
        try:
            # 构建连接参数
            credentials = pika.PlainCredentials(
                self.config.get('username', 'guest'),
                self.config.get('password', 'guest')
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5672),
                virtual_host=self.config.get('virtual_host', '/'),
                credentials=credentials,
                connection_attempts=3,
                retry_delay=5,
                heartbeat_interval=self.config.get('heartbeat_interval', 600)
            )
            
            # 建立连接
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self._connected = True
            
            info(f"RabbitMQ连接成功: {self.config.get('host')}:{self.config.get('port')}")
            return True
            
        except Exception as e:
            error(f"RabbitMQ连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开RabbitMQ连接"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self._connected = False
            info("RabbitMQ连接已断开")
            return True
        except Exception as e:
            error(f"断开RabbitMQ连接失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查RabbitMQ连接状态"""
        return self._connected and self.connection and not self.connection.is_closed
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = 'direct', 
                        durable: bool = True, auto_delete: bool = False) -> bool:
        """
        声明交换机
        :param exchange_name: 交换机名称
        :param exchange_type: 交换机类型 (direct, fanout, topic)
        :param durable: 是否持久化
        :param auto_delete: 是否自动删除
        :return: 是否成功
        """
        try:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=durable,
                auto_delete=auto_delete
            )
            info(f"交换机声明成功: {exchange_name}")
            return True
        except Exception as e:
            error(f"交换机声明失败: {exchange_name}, 错误: {e}")
            return False
    
    def declare_queue(self, queue_name: str, durable: bool = True, 
                     auto_delete: bool = False, arguments: Dict = None) -> bool:
        """
        声明队列
        :param queue_name: 队列名称
        :param durable: 是否持久化
        :param auto_delete: 是否自动删除
        :param arguments: 队列参数
        :return: 是否成功
        """
        try:
            self.channel.queue_declare(
                queue=queue_name,
                durable=durable,
                auto_delete=auto_delete,
                arguments=arguments or {}
            )
            info(f"队列声明成功: {queue_name}")
            return True
        except Exception as e:
            error(f"队列声明失败: {queue_name}, 错误: {e}")
            return False
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str) -> bool:
        """
        绑定队列到交换机
        :param queue_name: 队列名称
        :param exchange_name: 交换机名称
        :param routing_key: 路由键
        :return: 是否成功
        """
        try:
            self.channel.queue_bind(
                queue=queue_name,
                exchange=exchange_name,
                routing_key=routing_key
            )
            info(f"队列绑定成功: {queue_name} -> {exchange_name} ({routing_key})")
            return True
        except Exception as e:
            error(f"队列绑定失败: {queue_name} -> {exchange_name}, 错误: {e}")
            return False
    
    def publish_message(self, exchange_name: str, routing_key: str, 
                       message: str, properties: Dict = None) -> bool:
        """
        发布消息
        :param exchange_name: 交换机名称
        :param routing_key: 路由键
        :param message: 消息内容
        :param properties: 消息属性
        :return: 是否成功
        """
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            # 构建消息属性
            message_properties = pika.BasicProperties(
                delivery_mode=2,  # 持久化消息
                content_type='application/json',
                **(properties or {})
            )
            
            # 发布消息
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=message,
                properties=message_properties
            )
            
            info(f"消息发布成功: {exchange_name} -> {routing_key}")
            return True
            
        except Exception as e:
            error(f"消息发布失败: {e}")
            return False
    
    def consume_message(self, queue_name: str, callback: Callable, 
                       auto_ack: bool = True) -> bool:
        """
        消费消息
        :param queue_name: 队列名称
        :param callback: 回调函数
        :param auto_ack: 是否自动确认
        :return: 是否成功
        """
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            # 设置消费者
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=auto_ack
            )
            
            info(f"开始消费消息: {queue_name}")
            self.channel.start_consuming()
            return True
            
        except Exception as e:
            error(f"消费消息失败: {e}")
            return False
    
    def stop_consuming(self):
        """停止消费"""
        try:
            if self.channel:
                self.channel.stop_consuming()
            info("停止消费消息")
        except Exception as e:
            error(f"停止消费失败: {e}")

class RocketMQConnection(MQConnection):
    """RocketMQ连接类"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.producer = None
        self.consumer = None
    
    def connect(self) -> bool:
        """建立RocketMQ连接"""
        if not ROCKETMQ_AVAILABLE:
            error("RocketMQ驱动未安装，请运行: pip install rocketmq-client-python")
            return False
        
        try:
            # 创建生产者
            self.producer = Producer(self.config.get('producer_group', 'test_producer_group'))
            self.producer.set_name_server_address(self.config.get('name_server', 'localhost:9876'))
            self.producer.start()
            
            self._connected = True
            info(f"RocketMQ连接成功: {self.config.get('name_server')}")
            return True
            
        except Exception as e:
            error(f"RocketMQ连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开RocketMQ连接"""
        try:
            if self.producer:
                self.producer.shutdown()
            if self.consumer:
                self.consumer.shutdown()
            self._connected = False
            info("RocketMQ连接已断开")
            return True
        except Exception as e:
            error(f"断开RocketMQ连接失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查RocketMQ连接状态"""
        return self._connected and self.producer is not None
    
    def send_message(self, topic: str, message: str, tags: str = None, 
                    keys: str = None, delay_level: int = 0) -> bool:
        """
        发送消息
        :param topic: 主题
        :param message: 消息内容
        :param tags: 标签
        :param keys: 消息键
        :param delay_level: 延迟级别
        :return: 是否成功
        """
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            # 创建消息
            msg = Message(topic)
            msg.set_body(message.encode('utf-8'))
            
            if tags:
                msg.set_tags(tags)
            if keys:
                msg.set_keys(keys)
            if delay_level > 0:
                msg.set_delay_time_level(delay_level)
            
            # 发送消息
            send_result = self.producer.send_sync(msg)
            
            info(f"消息发送成功: {topic} -> {send_result.msg_id}")
            return True
            
        except Exception as e:
            error(f"消息发送失败: {e}")
            return False
    
    def start_consumer(self, topic: str, callback: Callable, 
                      consumer_group: str = None, tags: str = "*") -> bool:
        """
        启动消费者
        :param topic: 主题
        :param callback: 回调函数
        :param consumer_group: 消费者组
        :param tags: 标签过滤
        :return: 是否成功
        """
        try:
            if not ROCKETMQ_AVAILABLE:
                error("RocketMQ驱动未安装")
                return False
            
            # 创建消费者
            group = consumer_group or self.config.get('consumer_group', 'test_consumer_group')
            self.consumer = PushConsumer(group)
            self.consumer.set_name_server_address(self.config.get('name_server', 'localhost:9876'))
            
            # 设置消费者配置
            consumer_config = self.config.get('consumer', {})
            if 'pull_batch_size' in consumer_config:
                self.consumer.set_pull_batch_size(consumer_config['pull_batch_size'])
            if 'pull_interval' in consumer_config:
                self.consumer.set_pull_interval(consumer_config['pull_interval'])
            
            # 注册消息监听器
            def message_handler(msg):
                try:
                    result = callback(msg)
                    return ConsumeStatus.CONSUME_SUCCESS
                except Exception as e:
                    error(f"消息处理失败: {e}")
                    return ConsumeStatus.RECONSUME_LATER
            
            self.consumer.subscribe(topic, tags)
            self.consumer.register_message_listener(message_handler)
            
            # 启动消费者
            self.consumer.start()
            info(f"消费者启动成功: {topic} ({tags})")
            return True
            
        except Exception as e:
            error(f"启动消费者失败: {e}")
            return False
    
    def stop_consumer(self):
        """停止消费者"""
        try:
            if self.consumer:
                self.consumer.shutdown()
            info("消费者已停止")
        except Exception as e:
            error(f"停止消费者失败: {e}")

class MQManager:
    """MQ管理器"""
    
    def __init__(self, config_file: str = 'conf/mq.yaml', env: str = 'dev'):
        """
        初始化MQ管理器
        :param config_file: 配置文件路径
        :param env: 环境 (dev, test, prod)
        """
        self.config_file = config_file
        self.env = env
        self.config = self._load_config()
        self.connections = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """加载MQ配置"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.config_file)
            config = load_yaml(config_path)
            return config.get('mq', {})
        except Exception as e:
            error(f"加载MQ配置失败: {e}")
            return {}
    
    def get_connection(self, mq_type: str = None) -> Optional[MQConnection]:
        """
        获取MQ连接
        :param mq_type: MQ类型 (rabbitmq, rocketmq)
        :return: MQ连接对象
        """
        mq_type = mq_type or self.config.get('default_type', 'rabbitmq')
        
        if mq_type in self.connections:
            return self.connections[mq_type]
        
        # 获取配置
        mq_config = self.config.get(mq_type, {}).get(self.env, {})
        if not mq_config:
            error(f"未找到 {mq_type} 的 {self.env} 环境配置")
            return None
        
        # 创建连接
        if mq_type == 'rabbitmq':
            connection = RabbitMQConnection(mq_config)
        elif mq_type == 'rocketmq':
            connection = RocketMQConnection(mq_config)
        else:
            error(f"不支持的MQ类型: {mq_type}")
            return None
        
        self.connections[mq_type] = connection
        return connection
    
    def send_message(self, mq_type: str, message: str, **kwargs) -> bool:
        """
        发送消息
        :param mq_type: MQ类型
        :param message: 消息内容
        :param kwargs: 其他参数
        :return: 是否成功
        """
        connection = self.get_connection(mq_type)
        if not connection:
            return False
        
        if mq_type == 'rabbitmq':
            exchange = kwargs.get('exchange', 'test_exchange')
            routing_key = kwargs.get('routing_key', 'test_key')
            return connection.publish_message(exchange, routing_key, message)
        elif mq_type == 'rocketmq':
            topic = kwargs.get('topic', 'test_topic')
            tags = kwargs.get('tags')
            keys = kwargs.get('keys')
            delay_level = kwargs.get('delay_level', 0)
            return connection.send_message(topic, message, tags, keys, delay_level)
        
        return False
    
    def consume_message(self, mq_type: str, callback: Callable, **kwargs) -> bool:
        """
        消费消息
        :param mq_type: MQ类型
        :param callback: 回调函数
        :param kwargs: 其他参数
        :return: 是否成功
        """
        connection = self.get_connection(mq_type)
        if not connection:
            return False
        
        if mq_type == 'rabbitmq':
            queue = kwargs.get('queue', 'test_queue')
            auto_ack = kwargs.get('auto_ack', True)
            return connection.consume_message(queue, callback, auto_ack)
        elif mq_type == 'rocketmq':
            topic = kwargs.get('topic', 'test_topic')
            consumer_group = kwargs.get('consumer_group')
            tags = kwargs.get('tags', '*')
            return connection.start_consumer(topic, callback, consumer_group, tags)
        
        return False
    
    def disconnect_all(self):
        """断开所有连接"""
        for mq_type, connection in self.connections.items():
            try:
                connection.disconnect()
            except Exception as e:
                error(f"断开 {mq_type} 连接失败: {e}")

# 便捷函数
def send_rabbitmq_message(message: str, exchange: str = 'test_exchange', 
                         routing_key: str = 'test_key', env: str = 'dev') -> bool:
    """
    发送RabbitMQ消息的便捷函数
    :param message: 消息内容
    :param exchange: 交换机名称
    :param routing_key: 路由键
    :param env: 环境
    :return: 是否成功
    """
    manager = MQManager(env=env)
    return manager.send_message('rabbitmq', message, exchange=exchange, routing_key=routing_key)

def send_rocketmq_message(message: str, topic: str = 'test_topic', 
                         tags: str = None, env: str = 'dev') -> bool:
    """
    发送RocketMQ消息的便捷函数
    :param message: 消息内容
    :param topic: 主题
    :param tags: 标签
    :param env: 环境
    :return: 是否成功
    """
    manager = MQManager(env=env)
    return manager.send_message('rocketmq', message, topic=topic, tags=tags)

def consume_rabbitmq_message(callback: Callable, queue: str = 'test_queue', 
                           env: str = 'dev') -> bool:
    """
    消费RabbitMQ消息的便捷函数
    :param callback: 回调函数
    :param queue: 队列名称
    :param env: 环境
    :return: 是否成功
    """
    manager = MQManager(env=env)
    return manager.consume_message('rabbitmq', callback, queue=queue)

def consume_rocketmq_message(callback: Callable, topic: str = 'test_topic', 
                           tags: str = '*', env: str = 'dev') -> bool:
    """
    消费RocketMQ消息的便捷函数
    :param callback: 回调函数
    :param topic: 主题
    :param tags: 标签
    :param env: 环境
    :return: 是否成功
    """
    manager = MQManager(env=env)
    return manager.consume_message('rocketmq', callback, topic=topic, tags=tags)

# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("MQ工具类测试")
    print("=" * 60)
    
    # 创建MQ管理器
    manager = MQManager()
    
    # 测试发送消息
    test_message = json.dumps({
        "id": 1,
        "content": "测试消息",
        "timestamp": time.time()
    })
    
    print("\n1. 测试RabbitMQ消息发送:")
    success = manager.send_message('rabbitmq', test_message)
    print(f"发送结果: {'成功' if success else '失败'}")
    
    print("\n2. 测试RocketMQ消息发送:")
    success = manager.send_message('rocketmq', test_message)
    print(f"发送结果: {'成功' if success else '失败'}")
    
    print("\n✓ MQ工具类测试完成！") 