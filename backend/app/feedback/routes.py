from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Feedback, FeedbackReply, User, SystemNotification, FeedbackLike, FeedbackReplyLike
from ..extensions import db
from datetime import datetime, timedelta

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/', methods=['GET'])
@jwt_required()
def get_feedbacks():
    """获取所有反馈列表"""
    category = request.args.get('category')
    keyword = request.args.get('keyword')
    
    query = Feedback.query
    
    if category and category != 'all':
        query = query.filter_by(category=category)
        
    if keyword:
        query = query.filter(Feedback.title.contains(keyword) | Feedback.content.contains(keyword))
        
    feedbacks = query.order_by(Feedback.created_at.desc()).all()
    current_user_id = int(get_jwt_identity())
    
    result = []
    for f in feedbacks:
        reply_count = FeedbackReply.query.filter_by(feedback_id=f.id).count()
        last_reply = FeedbackReply.query.filter_by(feedback_id=f.id).order_by(FeedbackReply.created_at.desc()).first()
        like_count = FeedbackLike.query.filter_by(feedback_id=f.id).count()
        is_liked = FeedbackLike.query.filter_by(feedback_id=f.id, user_id=current_user_id).first() is not None
        
        result.append({
            'id': f.id,
            'title': f.title,
            'content': f.content[:100] + '...' if len(f.content) > 100 else f.content,
            'category': f.category,
            'user_id': f.user_id,
            'username': f.user.username,
            'avatar': f.user.avatar,
            'created_at': f.created_at.isoformat(),
            'view_count': f.view_count,
            'reply_count': reply_count,
            'last_reply_at': last_reply.created_at.isoformat() if last_reply else None,
            'like_count': like_count,
            'is_liked': is_liked
        })
        
    return jsonify(result), 200

@feedback_bp.route('/', methods=['POST'])
@jwt_required()
def create_feedback():
    """发布反馈 (管理员禁止)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if user.role == 'admin':
        return jsonify({'msg': '管理员不能发布反馈帖子'}), 403
        
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category', 'message')
    
    if not title or not content:
        return jsonify({'msg': '标题和内容不能为空'}), 400
        
    feedback = Feedback(
        title=title,
        content=content,
        category=category,
        user_id=current_user_id,
        created_at=datetime.utcnow() + timedelta(hours=8)
    )
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify({'msg': '发布成功', 'id': feedback.id}), 201

@feedback_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_feedback_detail(id):
    """获取反馈详情及回复"""
    feedback = Feedback.query.get_or_404(id)
    
    current_user_id = int(get_jwt_identity())

    # 增加浏览量
    feedback.view_count += 1
    db.session.commit()
    
    replies = FeedbackReply.query.filter_by(feedback_id=id).order_by(FeedbackReply.created_at.asc()).all()
    replies_data = []
    for r in replies:
        is_liked_reply = FeedbackReplyLike.query.filter_by(reply_id=r.id, user_id=current_user_id).first() is not None
        like_count_reply = FeedbackReplyLike.query.filter_by(reply_id=r.id).count()
        replies_data.append({
            'id': r.id,
            'content': r.content,
            'user_id': r.user_id,
            'username': r.user.username,
            'avatar': r.user.avatar,
            'role': r.user.role, # 用于前端标识管理员回复
            'created_at': r.created_at.isoformat(),
            'like_count': like_count_reply,
            'is_liked': is_liked_reply
        })
        
    is_liked = FeedbackLike.query.filter_by(feedback_id=id, user_id=current_user_id).first() is not None
    like_count = FeedbackLike.query.filter_by(feedback_id=id).count()

    return jsonify({
        'id': feedback.id,
        'title': feedback.title,
        'content': feedback.content,
        'category': feedback.category,
        'user_id': feedback.user_id,
        'username': feedback.user.username,
        'avatar': feedback.user.avatar,
        'created_at': feedback.created_at.isoformat(),
        'view_count': feedback.view_count,
        'replies': replies_data,
        'like_count': like_count,
        'is_liked': is_liked
    }), 200

@feedback_bp.route('/<int:id>/reply', methods=['POST'])
@jwt_required()
def create_reply(id):
    """回复反馈"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'msg': '回复内容不能为空'}), 400
        
    # Check if feedback exists
    feedback = Feedback.query.get_or_404(id)
    reply_user = User.query.get(current_user_id)
    
    reply = FeedbackReply(
        content=content,
        user_id=current_user_id,
        feedback_id=id,
        created_at=datetime.utcnow() + timedelta(hours=8)
    )
    db.session.add(reply)
    
    if feedback.user_id != current_user_id:
        notification = SystemNotification(
            user_id=feedback.user_id,
            title="您的反馈有新回复",
            content=f"用户 {reply_user.username} 回复了您的帖子: {feedback.title}",
            created_at=datetime.utcnow() + timedelta(hours=8)
        )
        db.session.add(notification)
        
    db.session.commit()
    
    # 获取最新回复数据返回，方便前端追加
    return jsonify({
        'msg': '回复成功',
        'data': {
            'id': reply.id,
            'content': reply.content,
            'user_id': reply.user_id,
            'username': reply_user.username,
            'avatar': reply_user.avatar,
            'role': reply_user.role,
            'created_at': reply.created_at.isoformat()
        }
    }), 201

@feedback_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_feedback(id):
    """删除反馈 (管理员或作者)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    feedback = Feedback.query.get_or_404(id)
    
    if user.role != 'admin' and feedback.user_id !=current_user_id:
        return jsonify({'msg': '无权限删除'}), 403
        
    db.session.delete(feedback)
    db.session.commit()
    return jsonify({'msg': '删除成功'}), 200

@feedback_bp.route('/reply/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_reply(id):
    """删除回复 (管理员或作者)"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    reply = FeedbackReply.query.get_or_404(id)
    
    if user.role != 'admin' and reply.user_id != current_user_id:
        return jsonify({'msg': '无权限删除'}), 403
        
    db.session.delete(reply)
    db.session.commit()
    return jsonify({'msg': '删除成功'}), 200

@feedback_bp.route('/<int:id>/like', methods=['POST'])
@jwt_required()
def toggle_like_feedback(id):
    """帖子点赞/取消"""
    current_user_id = int(get_jwt_identity())
    feedback = Feedback.query.get_or_404(id)
    
    like = FeedbackLike.query.filter_by(user_id=current_user_id, feedback_id=id).first()
    if like:
        db.session.delete(like)
        is_liked = False
    else:
        new_like = FeedbackLike(user_id=current_user_id, feedback_id=id)
        db.session.add(new_like)
        is_liked = True
        
    db.session.commit()
    like_count = FeedbackLike.query.filter_by(feedback_id=id).count()
    return jsonify({'is_liked': is_liked, 'like_count': like_count}), 200

@feedback_bp.route('/reply/<int:id>/like', methods=['POST'])
@jwt_required()
def toggle_like_reply(id):
    """回复点赞/取消"""
    current_user_id = int(get_jwt_identity())
    reply = FeedbackReply.query.get_or_404(id)
    
    like = FeedbackReplyLike.query.filter_by(user_id=current_user_id, reply_id=id).first()
    if like:
        db.session.delete(like)
        is_liked = False
    else:
        new_like = FeedbackReplyLike(user_id=current_user_id, reply_id=id)
        db.session.add(new_like)
        is_liked = True
        
    db.session.commit()
    like_count = FeedbackReplyLike.query.filter_by(reply_id=id).count()
    return jsonify({'is_liked': is_liked, 'like_count': like_count}), 200
