#!/usr/bin/env python3
"""
Elasticsearch 索引初始化脚本
Initialize Elasticsearch index for documents
"""

import requests
import json
import sys
import os
import time

# 从环境变量获取配置，默认使用 docker service name
ES_URL = os.environ.get('ELASTICSEARCH_URL') or "http://localhost:9200"
ES_USER = os.environ.get('ELASTIC_USER') or "elastic"
ES_PASSWORD = os.environ.get('ELASTIC_PASSWORD') or "elastic"
INDEX_NAME = "documents"

# 索引映射配置
INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "integer"},
            "title": {
                "type": "text",
                "analyzer": "ik_max_word",  # 支持中文分词（需要安装 ik 插件）
                "search_analyzer": "ik_smart"
            },
            "content": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart"
            },
            "owner_id": {"type": "integer"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "tags": {"type": "keyword"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}

def check_es_connection():
    """检查 Elasticsearch 连接"""
    global ES_URL
    
    print(f"🔄 正在尝试连接 {ES_URL} ...")
    
    # 简单的重试机制
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(ES_URL, timeout=5)
            if response.status_code == 200:
                print(f"✅ Elasticsearch 服务运行正常: {ES_URL}")
                return True
        except Exception as e:
            print(f"⚠️ 连接尝试 {i+1}/{max_retries} 失败: {e}")
            if i < max_retries - 1:
                time.sleep(2)
    
    print(f"❌ 无法连接到 Elasticsearch")
    return False

def delete_index_if_exists():
    """删除已存在的索引（可选）"""
    try:
        response = requests.get(f"{ES_URL}/{INDEX_NAME}")
        if response.status_code == 200:
            print(f"⚠️  索引 '{INDEX_NAME}' 已存在，正在删除...")
            delete_response = requests.delete(f"{ES_URL}/{INDEX_NAME}")
            if delete_response.status_code == 200:
                print(f"✅ 已删除旧索引 '{INDEX_NAME}'")
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def create_index():
    """创建文档索引"""
    try:
        response = requests.put(
            f"{ES_URL}/{INDEX_NAME}",
            headers={"Content-Type": "application/json"},
            data=json.dumps(INDEX_MAPPING)
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ 索引 '{INDEX_NAME}' 创建成功！")
            return True
        else:
            print(f"❌ 创建索引失败: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 创建索引时发生错误: {e}")
        return False

def verify_index():
    """验证索引创建"""
    try:
        response = requests.get(f"{ES_URL}/{INDEX_NAME}")
        if response.status_code == 200:
            print(f"✅ 索引验证通过")
            return True
        else:
            print(f"❌ 索引验证失败")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 验证索引时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Elasticsearch 初始化脚本")
    print("=" * 60)
    
    if not check_es_connection():
        sys.exit(1)
    
    delete_index_if_exists()
    
    if not create_index():
        sys.exit(1)
    
    if not verify_index():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ Elasticsearch 初始化完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
