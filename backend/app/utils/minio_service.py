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
        # 统一返回相对路径，由前端拼接或浏览器自动处理
        # 格式: /minio/{bucket_name}/{object_name}
        # 这样无论是在 PC (localhost) 还是移动端 (IP)，只要访问的前端地址是对的，
        # 这个相对路径就能正确通过 nginx 代理到 MinIO
        
        return f"/minio/{bucket_name}/{object_name}"
        
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

def delete_images_from_content(content):
    """
    从文档内容(HTML/Markdown)中提取并删除 MinIO 图片
    """
    if not content:
        return

    import re
    # 提取 URL 的正则
    # 1. HTML img src
    html_pattern = r'<img[^>]+src="([^">]+)"'
    # 2. Markdown ![...](url)
    md_pattern = r'!\[.*?\]\((.*?)\)'
    
    urls = set()
    urls.update(re.findall(html_pattern, content))
    urls.update(re.findall(md_pattern, content))
    
    for url in urls:
        # 只处理属于本系统 MinIO documents 桶的图片
        # 路径通常包含 /minio/documents/ 或 /documents/
        if '/documents/' in url:
            try:
                delete_file_by_url(url)
            except Exception as e:
                print(f"从内容删除图片失败 {url}: {e}")

