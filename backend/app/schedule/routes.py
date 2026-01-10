from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Schedule, Meeting, User, SystemNotification, Role
from ..extensions import db
from datetime import datetime
import calendar

schedule_bp = Blueprint('schedule', __name__)

def check_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'admin'

@schedule_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_events():
    """获取所有日程和会议（可按时间范围筛选）"""
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    # is_admin = (current_user.role == 'admin') # Not strictly needed for query logic now
    
    current_app.logger.info(f"Schedule Query - User ID: {current_user_id}, Name: {current_user.username}")

    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # 构建查询
    from sqlalchemy import or_
    
    
    # Logic:
    # 1. Admin/Public events (created by admin) are visible to everyone
    # 2. Private events (created by user/manager) are visible ONLY to creator
    
    # Schedule Filter
    # Must join Role to filter by creator's role code
    schedule_query = Schedule.query.join(User).outerjoin(Role).filter(
        or_(
            Schedule.user_id == current_user_id,
            Role.code == 'admin'
        )
    )
    
    # Meeting Filter
    meeting_query = Meeting.query.join(User, Meeting.organizer_id == User.id).outerjoin(Role).filter(
        or_(
            Meeting.organizer_id == current_user_id,
            Role.code == 'admin'
        )
    )

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # 结束日期包含当天
            end_date = end_date.replace(hour=23, minute=59, second=59)
            
            schedule_query = schedule_query.filter(Schedule.start_time >= start_date, Schedule.start_time <= end_date)
            meeting_query = meeting_query.filter(Meeting.start_time >= start_date, Meeting.start_time <= end_date)
        except ValueError:
            return jsonify({'error': '日期格式错误，应为 YYYY-MM-DD'}), 400

    schedules = schedule_query.all()
    meetings = meeting_query.all()

    events = []
    
    for s in schedules:
        events.append({
            'id': s.id,
            'type': 'schedule',
            'title': s.title,
            'description': s.description,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat(),
            'remind_minutes': s.remind_minutes,
            'user_id': s.user_id,
            'user_name': s.user.username if s.user else 'Unknown'
        })
        
    for m in meetings:
        organizer = User.query.get(m.organizer_id)
        events.append({
            'id': m.id,
            'type': 'meeting',
            'title': m.title,
            'description': m.description,
            'start_time': m.start_time.isoformat(),
            'end_time': m.end_time.isoformat(),
            'remind_minutes': m.remind_minutes,
            'organizer_id': m.organizer_id,
            'organizer_name': organizer.username if organizer else 'Unknown',
            'meeting_link': m.meeting_link,
            'attendees': m.attendees
        })
    
    # 按开始时间排序
    events.sort(key=lambda x: x['start_time'])
    
    return jsonify(events), 200

# ----------------- 日程管理 -----------------

@schedule_bp.route('/schedules', methods=['POST'])
@jwt_required()
def create_schedule():
    """创建日程（开放给所有用户，仅自己可见）"""
    current_user_id = get_jwt_identity()
    # 移除管理员权限检查，允许所有登录用户创建
        
    data = request.get_json()
    try:
        new_schedule = Schedule(
            title=data['title'],
            description=data.get('description', ''),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            user_id=current_user_id,
            remind_minutes=int(data.get('remind_minutes', 0))
        )
        db.session.add(new_schedule)
        db.session.commit()
        return jsonify({'message': '日程创建成功', 'id': new_schedule.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@schedule_bp.route('/schedules/<int:id>', methods=['PUT'])
@jwt_required()
def update_schedule(id):
    current_user_id = int(get_jwt_identity())
    schedule = Schedule.query.get_or_404(id)
    
    # 权限检查
    current_user_id = int(current_user_id)
    current_user = User.query.get(current_user_id)
    creator = schedule.user
    
    if creator.role == 'admin':
        # 管理员创建的公共日程：仅管理员可修改
        if current_user.role != 'admin':
            return jsonify({'error': '只有管理员可以修改公共日程'}), 403
    else:
        # 用户创建的私有日程：仅本人可修改
        if schedule.user_id != current_user_id:
             return jsonify({'error': '无权限'}), 403

    data = request.get_json()
    
    try:
        if 'title' in data:
            schedule.title = data['title']
        if 'description' in data:
            schedule.description = data['description']
        if 'start_time' in data:
            schedule.start_time = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data:
            schedule.end_time = datetime.fromisoformat(data['end_time'])
        if 'remind_minutes' in data:
            schedule.remind_minutes = int(data['remind_minutes'])
            # 如果更新了提醒时间，重置通知状态
            schedule.is_notified = False
            
        db.session.commit()
        return jsonify({'message': '日程更新成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@schedule_bp.route('/schedules/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_schedule(id):
    current_user_id = int(get_jwt_identity())
    schedule = Schedule.query.get_or_404(id)
    
    # 权限检查
    current_user_id = int(current_user_id)
    current_user = User.query.get(current_user_id)
    creator = schedule.user
    
    if creator.role == 'admin':
        if current_user.role != 'admin':
            return jsonify({'error': '只有管理员可以删除公共日程'}), 403
    else:
        if schedule.user_id != current_user_id:
             return jsonify({'error': '无权限'}), 403
         
    db.session.delete(schedule)
    db.session.commit()
    return jsonify({'message': '日程删除成功'}), 200

# ----------------- 会议管理 (仅管理员) -----------------

@schedule_bp.route('/meetings', methods=['POST'])
@jwt_required()
def create_meeting():
    current_user_id = get_jwt_identity()
    # 允许所有用户创建会议
    # if not check_admin(current_user_id):
    #     return jsonify({'error': '无权限'}), 403
        
    data = request.get_json()
    try:
        new_meeting = Meeting(
            title=data['title'],
            description=data.get('description', ''),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            organizer_id=current_user_id,
            remind_minutes=int(data.get('remind_minutes', 0)),
            meeting_link=data.get('meeting_link', ''),
            attendees=data.get('attendees', []) # ID列表
        )
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({'message': '会议创建成功', 'id': new_meeting.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@schedule_bp.route('/meetings/<int:id>', methods=['PUT'])
@jwt_required()
def update_meeting(id):
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    meeting = Meeting.query.get_or_404(id)
    
    # 权限检查
    # 注意：Meeting 模型可能没有直接的 relationship 到 User (需确认)，但 routes.py 前面 join user 表明有 relationship 或者手动 join
    # 假设 Meeting.organizer_id 是外键，但我们需要 Role。
    # 根据 lines 89 `organizer = User.query.get(m.organizer_id)`，我们可以手动 fetch。
    
    organizer = User.query.get(meeting.organizer_id)
    if organizer.role == 'admin':
        if current_user.role != 'admin':
            return jsonify({'error': '只有管理员可以修改公共会议'}), 403
    else:
        if meeting.organizer_id != current_user_id:
             return jsonify({'error': '无权限'}), 403
    data = request.get_json()
    
    try:
        if 'title' in data:
            meeting.title = data['title']
        if 'description' in data:
            meeting.description = data['description']
        if 'start_time' in data:
            meeting.start_time = datetime.fromisoformat(data['start_time'])
        if 'end_time' in data:
            meeting.end_time = datetime.fromisoformat(data['end_time'])
        if 'remind_minutes' in data:
            meeting.remind_minutes = int(data['remind_minutes'])
            meeting.is_notified = False
        if 'meeting_link' in data:
            meeting.meeting_link = data['meeting_link']
        if 'attendees' in data:
            meeting.attendees = data['attendees']
            
        db.session.commit()
        return jsonify({'message': '会议更新成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@schedule_bp.route('/meetings/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_meeting(id):
    current_user_id = int(get_jwt_identity())
    current_user = User.query.get(current_user_id)
    meeting = Meeting.query.get_or_404(id)
    
    organizer = User.query.get(meeting.organizer_id)
    if organizer.role == 'admin':
        if current_user.role != 'admin':
            return jsonify({'error': '只有管理员可以删除公共会议'}), 403
    else:
        if meeting.organizer_id != current_user_id:
             return jsonify({'error': '无权限'}), 403
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({'message': '会议删除成功'}), 200


