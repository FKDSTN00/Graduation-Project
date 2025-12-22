from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Notice, Vote, User
from ..extensions import db
from datetime import datetime

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
        author_id=current_user_id
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

@notice_bp.route('/vote', methods=['POST'])
@jwt_required()
def create_vote():
    """发起投票 (Placeholder from previous code)"""
    return jsonify({"msg": "投票功能暂未完整实现"}), 201
