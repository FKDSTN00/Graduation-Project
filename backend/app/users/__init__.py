from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from ..models.models import User
from ..extensions import db
from ..utils.minio_service import upload_file_to_minio, delete_file_by_url

users_bp = Blueprint('users', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户资料"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'department': user.department,
        'role': user.role,
        'avatar': user.avatar
    }), 200

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户资料"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    # 更新用户名
    if 'username' in data and data['username']:
        # 检查用户名是否已被使用
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user and existing_user.id != current_user_id:
            return jsonify({'msg': '用户名已被使用'}), 400
        user.username = data['username']
    
    # 更新头像URL（如果是通过上传接口获得的URL）
    if 'avatar' in data:
        user.avatar = data['avatar']
    
    # 更新部门
    if 'department' in data:
        user.department = data['department']
    
    try:
        db.session.commit()
        return jsonify({
            'msg': '资料更新成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'avatar': user.avatar,
                'department': user.department,
                'role': user.role
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '更新失败', 'error': str(e)}), 500

@users_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """上传头像到 MinIO"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'msg': '没有上传文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'msg': '文件名为空'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'msg': '不支持的文件格式，仅支持: png, jpg, jpeg, gif, webp'}), 400
    
    try:
        # 保存旧头像 URL，用于后续删除
        old_avatar_url = user.avatar
        
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"avatars/{current_user_id}_{uuid.uuid4().hex}.{ext}"
        
        # 上传到 MinIO
        file_url = upload_file_to_minio(file, filename, 'avatars')
        
        # 更新用户头像URL
        user.avatar = file_url
        db.session.commit()
        
        # 删除旧头像（如果存在）
        if old_avatar_url:
            try:
                delete_file_by_url(old_avatar_url)
            except Exception as e:
                # 删除失败不影响主流程，只记录日志
                print(f"删除旧头像失败: {e}")
        
        return jsonify({
            'msg': '头像上传成功',
            'avatar_url': file_url
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '上传失败', 'error': str(e)}), 500

@users_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改密码"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({'msg': '请提供旧密码和新密码'}), 400
    
    # 验证旧密码
    if not user.check_password(old_password):
        return jsonify({'msg': '旧密码错误'}), 400
    
    # 验证新密码长度
    if len(new_password) < 6:
        return jsonify({'msg': '新密码长度不能少于6位'}), 400
    
    try:
        user.set_password(new_password)
        db.session.commit()
        return jsonify({'msg': '密码修改成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '修改失败', 'error': str(e)}), 500
