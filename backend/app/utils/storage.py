from minio import Minio
from flask import current_app
from datetime import timedelta
import io

class StorageClient:
    def __init__(self):
        self.client = None
        self.bucket = 'file-center'

    def init_app(self, app):
        """初始化 MinIO 客户端"""
        endpoint = app.config.get('MINIO_ENDPOINT', 'localhost:9000')
        external_endpoint = app.config.get('MINIO_EXTERNAL_ENDPOINT', 'localhost:9000')
        access_key = app.config.get('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = app.config.get('MINIO_SECRET_KEY', 'minioadmin')
        secure = app.config.get('MINIO_SECURE', False)
        
        self.endpoint = endpoint
        self.external_endpoint = external_endpoint
        self.secure = secure
        
        # 内部操作客户端（用于上传、删除等）
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region='us-east-1' # 显式指定 region，避免自动探测
        )
        
        # 外部访问客户端（用于生成预签名 URL）
        self.external_client = Minio(
            external_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region='us-east-1' # 显式指定 region，确保离线从生成签名，不发起网络请求
        )
        
        # 确保存储桶存在
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_data, object_name, content_type=None):
        """上传文件"""
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        # 获取文件大小
        file_data.seek(0, 2)
        size = file_data.tell()
        file_data.seek(0)
        
        self.client.put_object(
            self.bucket,
            object_name,
            file_data,
            size,
            content_type=content_type
        )
        return size

    def get_presigned_url(self, object_name, original_filename=None):
        """获取预签名下载/预览链接"""
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        # 设置响应头，支持中文文件名下载
        response_headers = {}
        if original_filename:
            from urllib.parse import quote
            import os
            encoded_filename = quote(original_filename)
            
            # 获取文件扩展名
            _, ext = os.path.splitext(original_filename)
            ext = ext.lower()
            
            # 根据文件类型设置 Content-Type
            content_type = None
            if ext == '.txt':
                content_type = 'text/plain; charset=utf-8'
            elif ext == '.html' or ext == '.htm':
                content_type = 'text/html; charset=utf-8'
            elif ext == '.css':
                content_type = 'text/css; charset=utf-8'
            elif ext == '.js':
                content_type = 'application/javascript; charset=utf-8'
            elif ext == '.json':
                content_type = 'application/json; charset=utf-8'
            elif ext == '.xml':
                content_type = 'application/xml; charset=utf-8'
            
            response_headers = {
                'response-content-disposition': f'inline; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            }
            
            # 如果需要设置 Content-Type，添加到响应头
            if content_type:
                response_headers['response-content-type'] = content_type

        return self.external_client.get_presigned_url(
            "GET",
            self.bucket,
            object_name,
            expires=timedelta(hours=2),
            response_headers=response_headers
        )

    def get_download_url(self, object_name, original_filename=None):
        """获取强制下载链接（使用 attachment）"""
        if not self.client:
            raise Exception("MinIO client not initialized")
        
        response_headers = {}
        if original_filename:
            from urllib.parse import quote
            encoded_filename = quote(original_filename)
            response_headers = {
                'response-content-disposition': f'attachment; filename="{encoded_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            }

        return self.external_client.get_presigned_url(
            "GET",
            self.bucket,
            object_name,
            expires=timedelta(hours=2),
            response_headers=response_headers
        )

    def delete_file(self, object_name):
        """删除文件"""
        if not self.client:
            raise Exception("MinIO client not initialized")
            
        self.client.remove_object(self.bucket, object_name)

storage_client = StorageClient()
