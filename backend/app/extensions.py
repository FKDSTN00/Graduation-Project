from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_cors import CORS

# 初始化数据库 ORM，用于管理 SQLAlchemy 会话与模型
db = SQLAlchemy()

# 初始化 JWT 认证管理器，负责颁发与校验访问令牌
jwt = JWTManager()

# 初始化 SocketIO，使前端可以通过 WebSocket 进行实时通信
socketio = SocketIO(cors_allowed_origins="*")

# 初始化数据库迁移工具，统一管理 schema 的升级回滚
migrate = Migrate()

# 初始化跨域资源共享 (CORS)，允许前端域名访问后端接口
cors = CORS()

# Redis 客户端占位符，真实实例在 create_app 中创建
redis_client = None

# Elasticsearch 客户端占位符，便于其他模块统一引用
es = None
