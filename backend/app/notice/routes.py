from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Notice, Vote, User
from ..extensions import db
from datetime import datetime, timedelta

notice_bp = Blueprint('notice', __name__)

@notice_bp.route('/', methods=['GET'])
@jwt_required()
def get_notices():
    """获取所有公告"""
    # 获取所有公告
    notices = Notice.query.all()
    
    # 排序：先按时间降序，再按重要性（重要排前面）
    # Python的sort是稳定的。
    # 1. 按照时间降序排序
    notices.sort(key=lambda x: x.created_at, reverse=True)
    # 2. 按照等级排序（important为0，normal为1），稳定排序会保持时间相对顺序
    notices.sort(key=lambda x: 0 if x.level == 'important' else 1)
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'content': n.content,
        'level': n.level or 'normal',
        'created_at': n.created_at.isoformat(),
        'author': n.author.username if n.author else 'Unknown'
    } for n in notices]), 200

@notice_bp.route('/', methods=['POST'])
@jwt_required()
def create_notice():
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'No permission'}), 403
    
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Missing title or content'}), 400
    
    level = data.get('level', 'normal')
    if level not in ['normal', 'important']:
        level = 'normal'

    notice = Notice(
        title=data['title'],
        content=data['content'],
        level=level,
        author_id=current_user_id,
        created_at=datetime.utcnow() + timedelta(hours=8)
    )
    db.session.add(notice)
    db.session.commit()
    return jsonify({'message': '公告创建成功'}), 201

@notice_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_notice(id):
    notice = Notice.query.get_or_404(id)
    return jsonify({
        'id': notice.id,
        'title': notice.title,
        'content': notice.content,
        'level': notice.level or 'normal',
        'created_at': notice.created_at.isoformat(),
        'author': notice.author.username if notice.author else 'Unknown'
    }), 200

@notice_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_notice(id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'No permission'}), 403
    
    notice = Notice.query.get_or_404(id)
    data = request.get_json()
    
    if 'title' in data: notice.title = data['title']
    if 'content' in data: notice.content = data['content']
    if 'level' in data: 
        if data['level'] in ['normal', 'important']:
           notice.level = data['level']
    
    db.session.commit()
    return jsonify({'message': '公告更新成功'}), 200

@notice_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_notice(id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'No permission'}), 403
        
    notice = Notice.query.get_or_404(id)
    db.session.delete(notice)
    db.session.commit()
    return jsonify({'message': '公告删除成功'}), 200

from ..models.models import Notice, Vote, VoteRecord, User

# ... (Previous notice routes remain unchanged, just append new routes)

# ==================== 投票管理 ====================

@notice_bp.route('/votes', methods=['GET'])
@jwt_required()
def get_votes():
    """获取投票列表"""
    current_user_id = int(get_jwt_identity())
    votes = Vote.query.order_by(Vote.created_at.desc()).all()
    
    result = []
    for v in votes:
        # Check if user has voted
        record = VoteRecord.query.filter_by(vote_id=v.id, user_id=current_user_id).first()
        user_voted_key = record.option_key if record else None
        
        # Calculate stats
        total_count = VoteRecord.query.filter_by(vote_id=v.id).count()
        options_stats = []
        if v.options:
            for opt in v.options:
                count = VoteRecord.query.filter_by(vote_id=v.id, option_key=opt['key']).count()
                options_stats.append({
                    'key': opt['key'],
                    'label': opt['label'],
                    'count': count,
                    'percent': round((count / total_count * 100), 1) if total_count > 0 else 0
                })
        
        result.append({
            'id': v.id,
            'title': v.title,
            'created_at': v.created_at.isoformat() if v.created_at else None,
            'end_time': v.end_time.isoformat() if v.end_time else None,
            'options': options_stats,
            'total_count': total_count,
            'user_voted_key': user_voted_key,
            'is_active': (v.end_time is None or v.end_time > datetime.utcnow() + timedelta(hours=8))
        })
        
    return jsonify(result), 200

@notice_bp.route('/votes', methods=['POST'])
@jwt_required()
def create_vote():
    """发起投票 (管理员)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'No permission'}), 403
        
    data = request.get_json()
    title = data.get('title')
    options = data.get('options') # List of {key, label}
    end_time_str = data.get('end_time')
    
    if not title or not options:
        return jsonify({'error': 'Missing title or options'}), 400
        
    end_time = None
    if end_time_str:
        try:
            # Frontend sends local time string, allow generic parsing or ISO
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
        except:
            pass
            
    vote = Vote(
        title=title,
        options=options,
        created_by=current_user_id,
        end_time=end_time,
        created_at=datetime.utcnow() + timedelta(hours=8)
    )
    db.session.add(vote)
    db.session.commit()
    
    return jsonify({'message': '投票创建成功', 'id': vote.id}), 201

@notice_bp.route('/votes/<int:id>/submit', methods=['POST'])
@jwt_required()
def submit_vote(id):
    """提交投票"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    option_key = data.get('option_key')
    
    vote = Vote.query.get_or_404(id)
    
    # Check deadline
    now = datetime.utcnow() + timedelta(hours=8)
    if vote.end_time and vote.end_time < now:
        return jsonify({'error': '投票已结束'}), 400
        
    # Check if already voted
    existing = VoteRecord.query.filter_by(vote_id=id, user_id=current_user_id).first()
    if existing:
        return jsonify({'error': '您已投过票'}), 400
        
    # Check option validity
    valid_keys = [opt['key'] for opt in vote.options]
    if option_key not in valid_keys:
        return jsonify({'error': '无效选项'}), 400
        
    record = VoteRecord(
        vote_id=id,
        user_id=current_user_id,
        option_key=option_key,
        created_at=now
    )
    db.session.add(record)
    db.session.commit()
    
    return jsonify({'message': '投票成功'}), 200

@notice_bp.route('/votes/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_vote(id):
    """删除投票 (管理员)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'No permission'}), 403
        
    vote = Vote.query.get_or_404(id)
    db.session.delete(vote)
    db.session.commit()
    return jsonify({'message': '投票删除成功'}), 200
