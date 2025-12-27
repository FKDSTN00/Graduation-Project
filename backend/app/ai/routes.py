from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from ..models.models import AISession, AIMessage, User
from ..extensions import db
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    """获取所有会话列表"""
    current_user_id = get_jwt_identity()
    sessions = AISession.query.filter_by(user_id=current_user_id)\
        .order_by(AISession.is_pinned.desc(), AISession.updated_at.desc())\
        .all()
    
    return jsonify([{
        'id': s.id,
        'title': s.title or '新对话',
        'is_pinned': s.is_pinned,
        'updated_at': s.updated_at,
        'created_at': s.created_at
    } for s in sessions])

@ai_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """创建新会话"""
    current_user_id = get_jwt_identity()
    session = AISession(user_id=current_user_id, title='新对话')
    db.session.add(session)
    db.session.commit()
    return jsonify({'id': session.id, 'title': session.title})

@ai_bp.route('/sessions/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_session(id):
    """删除会话"""
    current_user_id = get_jwt_identity()
    session = AISession.query.filter_by(id=id, user_id=current_user_id).first_or_404()
    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@ai_bp.route('/sessions/<int:id>', methods=['PUT'])
@jwt_required()
def update_session(id):
    """更新会话（重命名/置顶）"""
    current_user_id = get_jwt_identity()
    session = AISession.query.filter_by(id=id, user_id=current_user_id).first_or_404()
    data = request.get_json()
    
    if 'title' in data:
        session.title = data['title']
    if 'is_pinned' in data:
        session.is_pinned = data['is_pinned']
        
    session.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': '更新成功'})

@ai_bp.route('/sessions/<int:id>/messages', methods=['GET'])
@jwt_required()
def get_messages(id):
    """获取会话消息历史"""
    current_user_id = get_jwt_identity()
    # 验证权限
    session = AISession.query.filter_by(id=id, user_id=current_user_id).first_or_404()
    messages = session.messages.order_by(AIMessage.created_at.asc()).all()
    
    return jsonify([{
        'role': m.role,
        'content': m.content,
        'created_at': m.created_at
    } for m in messages])

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """发送消息并获取 AI 回复"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    session_id = data.get('session_id')
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({'error': '内容不能为空'}), 400
        
    # 如果没有 session_id，创建一个新的
    if not session_id:
        session = AISession(user_id=current_user_id, title=prompt[:20])
        db.session.add(session)
        db.session.commit()
        session_id = session.id
    else:
        session = AISession.query.filter_by(id=session_id, user_id=current_user_id).first_or_404()
        session.updated_at = datetime.utcnow()
    
    # 保存用户消息
    user_msg = AIMessage(session_id=session_id, role='user', content=prompt)
    db.session.add(user_msg)
    db.session.commit() # 立即提交用户消息，防止 AI 超时导致消息丢失
    
    # 构造历史消息上下文 (最近 10 条，避免 token 超限)
    history_msgs = session.messages.order_by(AIMessage.created_at.desc()).limit(10).all()
    history_msgs.reverse() # 按时间正序
    
    messages_payload = [{"role": m.role, "content": m.content} for m in history_msgs]
    messages_payload.append({"role": "user", "content": prompt})
    
    try:
        # 调用 Ollama
        api_url = current_app.config.get('AI_API_URL', 'http://ollama:11434/v1')
        model = current_app.config.get('AI_MODEL_NAME', 'deepseek-r1:1.5b')
        
        response = requests.post(
            f"{api_url}/chat/completions",
            json={
                "model": model,
                "messages": messages_payload,
                "stream": False # 暂时不流式，简化实现
            },
            timeout=60
        )
        
        if response.status_code == 200:
            ai_content = response.json()['choices'][0]['message']['content']
            
            # 保存 AI 回复
            ai_msg = AIMessage(session_id=session_id, role='assistant', content=ai_content)
            db.session.add(ai_msg)
            
            # 自动总结标题 (如果是第一条消息)
            if session.messages.count() <= 2:
                 # 简单用前20个字作为标题，后续可以调用 AI 总结
                 session.title = prompt[:30]

            db.session.commit()
            
            return jsonify({
                'session_id': session_id,
                'role': 'assistant',
                'content': ai_content,
                'title': session.title
            })
        else:
            return jsonify({'error': f'AI 服务响应错误: {response.text}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
