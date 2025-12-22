#!/usr/bin/env python3
"""
MinIO 对象存储初始化脚本
Initialize MinIO buckets and policies
"""

from minio import Minio
from minio.error import S3Error
import sys
import os
import time

# MinIO 配置
# 注意：在 Docker 网络内部，我们使用 service name (minio) 而不是 localhost
# 端口是 9000 (API 端口)
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT_INTERNAL') or "minio:9000"
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY') or "minioadmin"
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY') or "minioadmin"
MINIO_SECURE = False

# 需要创建的 bucket 列表
BUCKETS = [
    {
        "name": "documents",
        "description": "文档附件存储"
    },
    {
        "name": "images",
        "description": "图片存储"
    },
    {
        "name": "videos",
        "description": "视频存储"
    },
    {
        "name": "avatars",
        "description": "用户头像"
    }
]

def create_minio_client():
    """创建 MinIO 客户端"""
    print(f"🔄 正在连接 MinIO: {MINIO_ENDPOINT} ...")
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        # 尝试列出 bucket 来验证连接
        client.list_buckets()
        print(f"✅ 已连接到 MinIO 服务")
        return client
    except Exception as e:
        print(f"❌ 连接 MinIO 失败: {e}")
        return None

def create_bucket(client, bucket_name, description):
    """创建存储桶"""
    try:
        if client.bucket_exists(bucket_name):
            print(f"⚠️  存储桶 '{bucket_name}' 已存在 - {description}")
            return True
        
        client.make_bucket(bucket_name)
        print(f"✅ 已创建存储桶 '{bucket_name}' - {description}")
        
        # 设置公开读策略
        if bucket_name in ["documents", "images", "avatars"]:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                    }
                ]
            }
            import json
            client.set_bucket_policy(bucket_name, json.dumps(policy))
            print(f"   └─ 已设置 '{bucket_name}' 为公开读取权限")
        
        return True
    except S3Error as e:
        print(f"❌ 创建存储桶 '{bucket_name}' 失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("MinIO 对象存储初始化脚本")
    print("=" * 60)
    
    client = create_minio_client()
    if not client:
        sys.exit(1)
    
    print(f"\n🚀 正在创建 {len(BUCKETS)} 个存储桶...")
    success_count = 0
    for bucket in BUCKETS:
        if create_bucket(client, bucket["name"], bucket["description"]):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ MinIO 初始化完成！成功创建 {success_count}/{len(BUCKETS)} 个存储桶")
    print("=" * 60)

if __name__ == "__main__":
    main()
