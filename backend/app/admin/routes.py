from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models.models import User, Document, Folder
from ..extensions import db
from ..utils.minio_service import delete_file_by_url

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    """简易管理员校验装饰器"""
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get_or_404(current_user_id)
        if current_user.role != 'admin':
            return jsonify({'msg': '权限不足，仅管理员可操作'}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.order_by(User.id.asc()).all()
    result = []
    for u in users:
        status = 'banned' if u.role == 'banned' else 'normal'
        result.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'department': u.department,
            'role': u.role,
            'status': status
        })
    return jsonify(result), 200


@admin_bp.route('/users/<int:user_id>/ban', methods=['PUT'])
@admin_required
def ban_user(user_id):
    data = request.get_json() or {}
    ban = data.get('ban', True)
    user = User.query.get_or_404(user_id)
    user.role = 'banned' if ban else 'user'
    db.session.commit()
    return jsonify({'msg': '操作成功', 'status': 'banned' if ban else 'normal'}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # 删除用户的文档及附件
    docs = Document.query.filter_by(owner_id=user.id).all()
    for doc in docs:
        if doc.attachments:
            for url in doc.attachments:
                try:
                    delete_file_by_url(url)
                except Exception as exc:  # 删除附件失败不阻塞
                    print(f'删除附件失败 {url}: {exc}')
        db.session.delete(doc)

    db.session.delete(user)
    db.session.commit()
    return jsonify({'msg': '用户已删除'}), 200


@admin_bp.route('/users/<int:user_id>/docs', methods=['GET'])
@admin_required
def user_docs(user_id):
    # 管理员查看指定用户文档，不区分隐私/公开，仅列表信息
    docs = Document.query.filter_by(owner_id=user_id, is_deleted=False).order_by(Document.updated_at.desc()).all()
    results = []
    folder_map = {f.id: f.name for f in Folder.query.filter_by(owner_id=user_id)}
    for doc in docs:
        results.append({
            'id': doc.id,
            'title': doc.title,
            'folder': folder_map.get(doc.folder_id) if doc.folder_id else None,
            'updated_at': doc.updated_at,
            'created_at': doc.created_at,
            'is_pinned': doc.is_pinned
        })
    return jsonify(results), 200
@admin_bp.route('/tasks', methods=['GET'])
@admin_required
def list_all_tasks():
    """获取所有用户的待处理和进行中任务，按用户分组"""
    from ..models.models import Task
    from collections import defaultdict
    
    # 筛选状态不为 completed 的任务
    tasks = Task.query.filter(Task.status != 'completed').all()
    
    # 按用户分组
    user_tasks = defaultdict(list)
    for t in tasks:
        user_tasks[t.user_id].append({
            'id': t.id,
            'title': t.title,
            'notes': t.notes,
            'status': t.status,
            'priority': t.priority,
            'deadline': t.deadline.strftime('%Y-%m-%d %H:%M') if t.deadline else '',
            'created_at': t.created_at
        })
    
    # 构建结果，按用户名排序
    results = []
    for user_id, tasks_list in user_tasks.items():
        user = User.query.get(user_id)
        if user:
            # 按截止时间升序排列任务
            sorted_tasks = sorted(tasks_list, key=lambda x: x['deadline'] if x['deadline'] else 'z')
            results.append({
                'user_id': user.id,
                'username': user.username,
                'avatar': user.avatar,
                'tasks': sorted_tasks
            })
    
    # 按用户名排序
    results.sort(key=lambda x: x['username'])
    
    return jsonify(results), 200

@admin_bp.route('/monitor/docs', methods=['POST'])
@admin_required
def monitor_documents():
    """根据关键词监控文档内容"""
    import re
    
    data = request.get_json()
    keywords = data.get('keywords', [])
    
    if not keywords:
        return jsonify([]), 200
    
    # 查询所有非删除的文档
    docs = Document.query.filter_by(is_deleted=False).all()
    
    def strip_html_tags(text):
        """去除HTML标签，保留纯文本"""
        if not text:
            return ''
        # 移除所有HTML标签
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    flagged_docs = []
    for doc in docs:
        if not doc.content:
            continue
        
        # 清理HTML标签，获取纯文本
        clean_content = strip_html_tags(doc.content)
        
        # 检查文档内容是否包含任何关键词（OR关系）
        matched_keywords = []
        content_lower = clean_content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            # 提取包含关键词的内容片段
            snippet = ''
            for keyword in matched_keywords[:1]:  # 只显示第一个匹配的关键词片段
                idx = content_lower.find(keyword.lower())
                if idx != -1:
                    start = max(0, idx - 30)
                    end = min(len(clean_content), idx + len(keyword) + 30)
                    snippet = '...' + clean_content[start:end] + '...'
                    break
            
            flagged_docs.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,  # 完整内容用于预览
                'username': doc.owner.username if doc.owner else 'Unknown',
                'user_id': doc.owner_id,
                'snippet': snippet,
                'matched_keywords': matched_keywords,
                'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': doc.updated_at.strftime('%Y-%m-%d %H:%M')
            })
    
    # 按更新时间倒序排列
    flagged_docs.sort(key=lambda x: x['updated_at'], reverse=True)
    
    return jsonify(flagged_docs), 200
