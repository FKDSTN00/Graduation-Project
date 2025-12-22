from app.extensions import db, redis_client
from app.models.models import Schedule, Meeting, SystemNotification, User
from datetime import datetime, timedelta

def check_notifications(app):
    """检查并生成通知"""
    # 获取 Redis 锁，防止多 Worker 并发执行
    # timeout=50s，任务每分钟执行一次
    if not redis_client:
        return # Redis 未初始化
        
    lock = redis_client.lock("scheduler_lock", timeout=50)
    if not lock.acquire(blocking=False):
        return

    try:
        with app.app_context():
            now = datetime.now()
            
            # 获取所有用户（用于发送全员通知）
            all_users = User.query.all()

            # 1. 检查日程
            schedules = Schedule.query.filter(
                Schedule.remind_minutes > 0,
                Schedule.is_notified == False
            ).all()
            
            for s in schedules:
                notify_time = s.start_time - timedelta(minutes=s.remind_minutes)
                if notify_time <= now:
                    # 创建通知 - 发送给所有用户
                    title = f"日程提醒: {s.title}"
                    time_str = s.start_time.strftime('%Y-%m-%d %H:%M')
                    content = f"日程【{s.title}】将于 {time_str} 开始。"
                    
                    for user in all_users:
                        # 可选：如果不需要通知管理员自己，可以加 if user.role != 'admin':
                        notification = SystemNotification(
                            user_id=user.id,
                            title=title,
                            content=content,
                            type='schedule'
                        )
                        db.session.add(notification)
                    
                    s.is_notified = True
            
            # 2. 检查会议
            meetings = Meeting.query.filter(
                Meeting.remind_minutes > 0,
                Meeting.is_notified == False
            ).all()
            
            for m in meetings:
                notify_time = m.start_time - timedelta(minutes=m.remind_minutes)
                if notify_time <= now:
                    title = f"会议提醒: {m.title}"
                    time_str = m.start_time.strftime('%Y-%m-%d %H:%M')
                    content = f"会议【{m.title}】将于 {time_str} 开始。"
                    
                    # 同样发送给所有用户（视为全员会议）
                    for user in all_users:
                        notification = SystemNotification(
                            user_id=user.id,
                            title=title,
                            content=content,
                            type='meeting'
                        )
                        db.session.add(notification)
                    
                    m.is_notified = True
            
            try:
                db.session.commit()
            except Exception as e:
                print(f"Error checking notifications: {e}")
                db.session.rollback()
    finally:
        try:
            lock.release()
        except:
            pass
