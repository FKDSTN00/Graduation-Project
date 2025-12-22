import os

class Config:
    """
    应用配置类
    包含数据库、密钥、第三方服务连接等配置
    """
    # Flask 密钥，用于 session 等安全加密
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 数据库连接 URI
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT 密钥
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    # JWT token 过期时间（7天）
    from datetime import timedelta
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Elasticsearch 配置 (全文搜索)
    # 格式: http://user:password@host:port
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://elastic:elastic@localhost:9200'
    
    # MinIO 配置 (对象存储)
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT') or 'localhost:9000'
    # MinIO 外部访问地址（用于生成浏览器可访问的预签名 URL）
    MINIO_EXTERNAL_ENDPOINT = os.environ.get('MINIO_EXTERNAL_ENDPOINT') or 'localhost:9000'
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY') or 'minioadmin'
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY') or 'minioadmin'
    MINIO_SECURE = False
    
    # AI 模型 API 地址
    AI_API_URL = os.environ.get('AI_API_URL') or 'http://localhost:11434/v1'
    AI_MODEL_NAME = os.environ.get('AI_MODEL_NAME') or 'deepseek-r1:1.5b'
    
    # Redis 配置
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
