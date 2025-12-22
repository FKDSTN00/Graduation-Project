import time
import threading
from .extensions import db
from .models.models import Document
from .utils.redis_service import RedisService

def sync_worker(app):
    """后台线程：周期性地将 Redis 中离线缓存的文档写回数据库"""
    with app.app_context():
        print("同步线程启动，等待检测离线文档...")
        while True:
            try:
                # 探测数据库连接是否正常
                db.session.execute(db.text('SELECT 1'))
                
                # 从 Redis 中取出离线文档列表
                offline_docs = RedisService.get_offline_documents()
                
                if offline_docs:
                    print(f"检测到 {len(offline_docs)} 篇离线文档，开始同步...")
                    count = 0
                    for doc_data in offline_docs:
                        try:
                            doc = Document(
                                title=doc_data['title'],
                                content=doc_data['content'],
                                owner_id=doc_data['owner_id']
                            )
                            db.session.add(doc)
                            count += 1
                        except Exception as e:
                            print(f"创建文档对象失败: {e}")
                    
                    if count > 0:
                        try:
                            db.session.commit()
                            RedisService.remove_offline_documents(count)
                            print(f"成功同步 {count} 篇离线文档并清理缓存队列。")
                        except Exception as e:
                            db.session.rollback()
                            print(f"同步提交失败，已回滚: {e}")
                            
            except Exception as e:
                # 可能是数据库暂不可用等异常，此处忽略并等待下一轮
                # print(f"同步线程异常（数据库可能离线）: {e}")
                pass
                
            # 等待一段时间后再次检查，避免频繁占用资源
            time.sleep(10)

def start_sync_worker(app):
    """以守护线程启动同步任务，随应用生命周期运行"""
    thread = threading.Thread(target=sync_worker, args=(app,))
    thread.daemon = True
    thread.start()
