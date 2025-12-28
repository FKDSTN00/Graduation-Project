from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Schedule, Meeting, User, SystemNotification
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
    is_admin = (current_user.role == 'admin')
    
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # 构建查询
    from sqlalchemy import or_
    
    if is_admin:
        # 管理员：只能看到管理员自己创建的
        schedule_query = Schedule.query.filter_by(user_id=current_user_id)
    else:
        # 普通用户：能获取自己创建的日程 AND 管理员创建的日程
        # 需要联表查询 User 表来找到管理员创建的日程
        schedule_query = Schedule.query.join(User).filter(
            or_(
                Schedule.user_id == current_user_id,
                User.role == 'admin'
            )
        )
    
    # 会议方面，通常参与者都可见，或者管理员可见所有？
    # 用户需求只提到了“日程”，对于“会议”暂保持原有逻辑（或者也仅看跟自己相关的）
    # 为保持一致性并避免数据泄露，会议也仅展示跟自己相关的（作为组织者或参与者）
    # 但会议模型中 attendees 是 JSON，筛选较复杂。
    # 暂时保持会议逻辑不变（管理员看所有，普通用户看自己？），但用户特别强调了“日程”。
    # 鉴于“日程”是私有的，在这里我们先严格限制 schedule。
    
    meeting_query = Meeting.query
    if not is_admin:
        # 普通用户：能看到自己组织的会议 OR 管理员组织的会议
        meeting_query = meeting_query.join(User, Meeting.organizer_id == User.id).filter(
            or_(
                Meeting.organizer_id == current_user_id,
                User.role == 'admin'
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
    
    # 仅创建者可修改
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
    
    # 仅创建者可删除
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
    if not check_admin(current_user_id):
        return jsonify({'error': '无权限'}), 403
        
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
    current_user_id = get_jwt_identity()
    if not check_admin(current_user_id):
        return jsonify({'error': '无权限'}), 403
        
    meeting = Meeting.query.get_or_404(id)
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
    current_user_id = get_jwt_identity()
    if not check_admin(current_user_id):
        return jsonify({'error': '无权限'}), 403
        
    meeting = Meeting.query.get_or_404(id)
    db.session.delete(meeting)
    db.session.commit()
    return jsonify({'message': '会议删除成功'}), 200
