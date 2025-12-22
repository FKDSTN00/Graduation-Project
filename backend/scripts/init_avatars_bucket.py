#!/usr/bin/env python3
"""
MinIO Avatars 桶初始化脚本
确保 avatars 桶存在并设置为公开读取
"""

import sys
import os
sys.path.append(os.getcwd())

from minio import Minio
from minio.error import S3Error
import json

def init_avatars_bucket():
    """初始化 avatars 桶"""
    
    # MinIO 配置
    endpoint = os.environ.get('MINIO_ENDPOINT', 'minio:9000')
    access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')
    
    print(f"连接到 MinIO: {endpoint}")
    
    # 创建客户端
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )
    
    bucket_name = 'avatars'
    
    try:
        # 检查桶是否存在
        if client.bucket_exists(bucket_name):
            print(f"✅ 桶 '{bucket_name}' 已存在")
        else:
            # 创建桶
            client.make_bucket(bucket_name)
            print(f"✅ 创建桶 '{bucket_name}' 成功")
        
        # 设置桶策略为公开读取
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        client.set_bucket_policy(bucket_name, json.dumps(policy))
        print(f"✅ 设置桶 '{bucket_name}' 为公开读取")
        
        # 验证策略
        current_policy = client.get_bucket_policy(bucket_name)
        print(f"✅ 当前桶策略: {current_policy[:100]}...")
        
        # 列出桶中的文件
        objects = client.list_objects(bucket_name)
        file_count = sum(1 for _ in objects)
        print(f"✅ 桶中当前有 {file_count} 个文件")
        
        print("\n🎉 MinIO avatars 桶初始化完成！")
        print(f"📁 访问地址: http://localhost:9000/{bucket_name}/")
        
    except S3Error as e:
        print(f"❌ MinIO 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    init_avatars_bucket()
