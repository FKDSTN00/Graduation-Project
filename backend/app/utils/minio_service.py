from minio import Minio
from minio.error import S3Error
from flask import current_app
import io

def get_minio_client():
    """获取 MinIO 客户端"""
    return Minio(
        current_app.config['MINIO_ENDPOINT'],
        access_key=current_app.config['MINIO_ACCESS_KEY'],
        secret_key=current_app.config['MINIO_SECRET_KEY'],
        secure=current_app.config.get('MINIO_SECURE', False)
    )

def upload_file_to_minio(file, object_name, bucket_name='avatars'):
    """
    上传文件到 MinIO
    
    Args:
        file: 文件对象（FileStorage）
        object_name: 对象名称（路径）
        bucket_name: 桶名称
    
    Returns:
        str: 文件访问URL
    """
    try:
        client = get_minio_client()
        
        # 确保桶存在
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            # 设置桶为公开读取
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
            import json
            client.set_bucket_policy(bucket_name, json.dumps(policy))
        
        # 读取文件内容
        file_data = file.read()
        file_size = len(file_data)
        
        # 上传文件
        client.put_object(
            bucket_name,
            object_name,
            io.BytesIO(file_data),
            file_size,
            content_type=file.content_type
        )
        
        # 返回文件URL
        # 使用相对路径，由 nginx 代理到 MinIO
        # 这样移动端和 PC 端都能正确访问
        from flask import request
        
        # 优先使用环境变量配置的公网地址
        public_url = current_app.config.get('MINIO_PUBLIC_URL')
        if public_url:
            return f"{public_url}/{bucket_name}/{object_name}"
        
        # 否则使用请求的 host（通过 nginx 代理）
        if request:
            # 使用 /minio 路径，由 nginx 反向代理到 minio:9000
            host = request.host
            scheme = 'https' if request.is_secure else 'http'
            return f"{scheme}://{host}/minio/{bucket_name}/{object_name}"
        
        # 后备方案：使用 localhost（仅用于开发环境）
        return f"http://localhost:9000/{bucket_name}/{object_name}"
        
    except S3Error as e:
        raise Exception(f"MinIO 上传失败: {str(e)}")
    except Exception as e:
        raise Exception(f"文件上传失败: {str(e)}")

def delete_file_from_minio(object_name, bucket_name='avatars'):
    """
    从 MinIO 删除文件
    
    Args:
        object_name: 对象名称（路径）
        bucket_name: 桶名称
    """
    try:
        client = get_minio_client()
        client.remove_object(bucket_name, object_name)
    except S3Error as e:
        raise Exception(f"MinIO 删除失败: {str(e)}")

def extract_object_path_from_url(url):
    """
    从 MinIO URL 中提取对象路径和桶名
    
    Args:
        url: MinIO 文件 URL，例如 http://localhost:9000/avatars/1_abc.jpg
    
    Returns:
        tuple: (bucket_name, object_name) 或 (None, None)
    """
    if not url:
        return None, None
    
    try:
        # 解析 URL
        parts = url.split('/')
        
        # 检查是否是新格式（包含 /minio/ 路径）
        if '/minio/' in url:
            # 新格式: http://host/minio/bucket/path/to/file.jpg
            try:
                minio_index = parts.index('minio')
                if len(parts) > minio_index + 2:
                    bucket_name = parts[minio_index + 1]
                    object_name = '/'.join(parts[minio_index + 2:])
                    return bucket_name, object_name
            except ValueError:
                pass
        else:
            # 旧格式: http://localhost:9000/bucket/path/to/file.jpg
            if len(parts) >= 5:
                bucket_name = parts[3]
                object_name = '/'.join(parts[4:])
                return bucket_name, object_name
    except Exception as e:
        print(f"解析 MinIO URL 失败: {url}, 错误: {e}")
        pass
    
    return None, None

def delete_file_by_url(url):
    """
    通过 URL 删除 MinIO 文件
    
    Args:
        url: MinIO 文件 URL
    """
    bucket_name, object_name = extract_object_path_from_url(url)
    if bucket_name and object_name:
        delete_file_from_minio(object_name, bucket_name)
