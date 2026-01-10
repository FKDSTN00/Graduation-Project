from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.models import Task, User
from datetime import datetime

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    """创建任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    title = data.get('title')
    if not title:
        return jsonify({'code': 400, 'msg': '任务标题不能为空'}), 400
        
    try:
        # 处理时间
        deadline = None
        if data.get('deadline'):
            deadline = datetime.strptime(data.get('deadline'), '%Y-%m-%d %H:%M')
            
        task = Task(
            title=title,
            priority=data.get('priority', 'Medium'),
            deadline=deadline,
            status=data.get('status', 'pending'),
            notes=data.get('notes', ''),
            related_docs=data.get('relatedDocs', []),  # 前端传 relatedDocs
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'code': 200, 
            'msg': '创建成功',
            'data': {
                'id': task.id,
                'title': task.title,
                'priority': task.priority,
                'deadline': task.deadline.strftime('%Y-%m-%d %H:%M') if task.deadline else '',
                'status': task.status,
                'notes': task.notes,
                'relatedDocs': task.related_docs,
                'created_at': task.created_at.timestamp() * 1000
            }
        })
    except Exception as e:
        print(e)
        return jsonify({'code': 500, 'msg': '创建失败'}), 500

@bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取用户任务"""
    user_id = get_jwt_identity()
    
    try:
        # 获取我创建的任务
        tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
        
        task_list = []
        for t in tasks:
            task_list.append({
                'id': t.id,
                'title': t.title,
                'priority': t.priority,
                'deadline': t.deadline.strftime('%Y-%m-%d %H:%M') if t.deadline else '',
                'status': t.status,
                'notes': t.notes,
                'relatedDocs': t.related_docs or [],
                'createdAt': int(t.created_at.timestamp() * 1000)
            })
            
        return jsonify(task_list)
    except Exception as e:
        print(e)
        return jsonify({'code': 500, 'msg': '获取失败'}), 500


@bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """更新任务"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'}), 404
        
    try:
        if 'title' in data:
            task.title = data['title']
        if 'priority' in data:
            task.priority = data['priority']
        if 'deadline' in data:
            if data['deadline']:
                 task.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M')
            else:
                 task.deadline = None
        if 'status' in data:
            task.status = data['status']
        if 'notes' in data:
            task.notes = data['notes']
        if 'relatedDocs' in data:
            task.related_docs = data['relatedDocs']
        
        db.session.commit()
        
        return jsonify({
            'code': 200, 
            'msg': '更新成功',
            'data': {
                'id': task.id,
                'status': task.status
            }
        })
    except Exception as e:
        print(e)
        return jsonify({'code': 500, 'msg': '更新失败'}), 500

@bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """删除任务"""
    user_id = get_jwt_identity()
    
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'}), 404
        
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '删除成功'})
    except Exception as e:
        return jsonify({'code': 500, 'msg': '删除失败'}), 500
