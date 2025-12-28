from flask import Flask

try:
    from elasticsearch import Elasticsearch
except ImportError:  # pragma: no cover - 开发环境下可选依赖
    Elasticsearch = None

from .config import Config
from .extensions import db, jwt, socketio, migrate, cors

def create_app(config_class=Config):
    """
    创建 Flask 应用实例
    :param config_class: 配置类
    :return: Flask app
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化项目依赖的核心扩展（数据库、JWT、SocketIO、迁移、跨域）
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    from .extensions import mail
    mail.init_app(app)
    
    # 初始化 Redis 客户端，供需要缓存或队列的模块使用
    from redis import Redis
    from . import extensions
    extensions.redis_client = Redis.from_url(app.config['REDIS_URL'])

    # 初始化 Elasticsearch 客户端，若外部依赖不可用则降级为空
    es_url = app.config.get('ELASTICSEARCH_URL')
    if Elasticsearch and es_url:
        try:
            extensions.es = Elasticsearch(es_url)
            if not extensions.es.ping():
                app.logger.warning('Elasticsearch ping failed: %s', es_url)
        except Exception as exc:  # pylint: disable=broad-except
            app.logger.warning('Unable to initialize Elasticsearch: %s', exc)
            extensions.es = None
    else:
        extensions.es = None

    # 注册蓝图，将各业务模块的路由挂载到统一的 /api 前缀下
    from .auth import auth_bp
    from .docs import docs_bp
    from .schedule import schedule_bp
    from .approval import approval_bp
    from .notice import notice_bp

    from .ai import ai_bp
    from .users import users_bp
    from .privacy import privacy_bp
    from .admin import admin_bp
    from .tasks.routes import bp as tasks_bp
    from .knowledge import knowledge_bp

    # 注册各功能模块的蓝图，并设置 URL 前缀
    app.register_blueprint(auth_bp, url_prefix='/api/auth')       # 认证模块
    app.register_blueprint(users_bp, url_prefix='/api/users')     # 用户管理
    app.register_blueprint(admin_bp, url_prefix='/api/admin')     # 管理员
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')     # 任务管理
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')  # 知识库
    app.register_blueprint(docs_bp, url_prefix='/api/docs')       # 文档管理
    app.register_blueprint(schedule_bp, url_prefix='/api/schedule') # 日程会议
    app.register_blueprint(approval_bp, url_prefix='/api/approval') # 审批流程
    app.register_blueprint(notice_bp, url_prefix='/api/notice')     # 公告投票

    app.register_blueprint(ai_bp, url_prefix='/api/ai')             # AI 助手
    app.register_blueprint(privacy_bp, url_prefix='/api/privacy')   # 隐私空间
    
    from .files import files_bp
    app.register_blueprint(files_bp, url_prefix='/api/files')       # 文件中心
    
    from .feedback.routes import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback') # 留言反馈

    from .utils.storage import storage_client
    storage_client.init_app(app)
    
    # 启动后台同步线程，将 Redis 中的离线文档回写数据库
    # 启动后台同步线程
    from .sync import start_sync_worker
    start_sync_worker(app)
    
    # 初始化并启动定时任务调度器
    try:
        from flask_apscheduler import APScheduler
        from .tasks.scheduler import check_notifications
        
        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        
        @scheduler.task('interval', id='check_notifications', minutes=1)
        def job_check_notifications():
            check_notifications(app)
            
        print("✅ Scheduler started.")
    except ImportError:
        print("⚠️ Flask-APScheduler not installed, skipping scheduler.")
    except Exception as e:
        print(f"⚠️ Scheduler start failed: {e}")

    return app
