import json
from flask import current_app
from ..extensions import redis_client

class RedisService:
    OFFLINE_DOCS_KEY = "offline_docs"

    @staticmethod
    def get_client():
        """获取 Redis 客户端"""
        return redis_client

    @staticmethod
    def save_offline_document(user_id, doc_data):
        """当数据库离线时保存文档到 Redis 列表"""
        try:
            client = RedisService.get_client()
            # 添加时间戳和用户ID到数据
            doc_data['owner_id'] = user_id
            doc_data['is_offline'] = True
            
            # 使用列表存储离线文档
            client.rpush(RedisService.OFFLINE_DOCS_KEY, json.dumps(doc_data))
            return True
        except Exception as e:
            print(f"保存到 Redis 失败: {e}")
            return False

    @staticmethod
    def get_offline_documents(limit=10):
        """从 Redis 获取离线文档"""
        try:
            client = RedisService.get_client()
            # 获取指定范围的项目
            items = client.lrange(RedisService.OFFLINE_DOCS_KEY, 0, limit - 1)
            return [json.loads(item) for item in items]
        except Exception as e:
            print(f"从 Redis 获取失败: {e}")
            return []

    @staticmethod
    def remove_offline_documents(count):
        """从 Redis 移除已处理的文档"""
        try:
            client = RedisService.get_client()
            client.lpop(RedisService.OFFLINE_DOCS_KEY, count)
            return True
        except Exception as e:
            print(f"从 Redis 移除失败: {e}")
            return False
