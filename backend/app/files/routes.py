from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import FileCenterFile, FileCenterFolder, User
from ..extensions import db
from ..utils.storage import storage_client
import uuid
import os
from datetime import datetime

files_bp = Blueprint('files', __name__)

@files_bp.route('/list', methods=['GET'])
@jwt_required()
def list_files():
    """获取指定文件夹下的文件和文件夹"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    parent_id = request.args.get('parent_id', type=int) # None 表示根目录
    
    # 文件夹
    folders_query = FileCenterFolder.query.filter_by(parent_id=parent_id)
    folders = folders_query.order_by(FileCenterFolder.created_at.desc()).all()
    
    # 文件
    files_query = FileCenterFile.query.filter_by(folder_id=parent_id)
    files = files_query.order_by(FileCenterFile.created_at.desc()).all()
    
    return jsonify({
        'folders': [{
            'id': f.id,
            'name': f.name,
            'creator': f.creator.username,
            'created_at': f.created_at.isoformat()
        } for f in folders],
        'files': [{
            'id': f.id,
            'name': f.name,
            'size': f.size,
            'type': f.type,
            'uploader': f.uploader.username,
            'created_at': f.created_at.isoformat()
        } for f in files],
        # 如果有 parent_id，返回当前文件夹信息用于面包屑导航
        'current_folder': {
            'id': parent_id,
            'name': FileCenterFolder.query.get(parent_id).name if parent_id else '根目录'
        } if parent_id else None
    })

@files_bp.route('/all_folders', methods=['GET'])
@jwt_required()
def get_all_folders():
    """获取所有文件夹（用于移动选择）"""
    folders = FileCenterFolder.query.order_by(FileCenterFolder.name).all()
    return jsonify([{
        'id': f.id, 
        'name': f.name, 
        'parent_id': f.parent_id
    } for f in folders])

@files_bp.route('/folders', methods=['POST'])
@jwt_required()
def create_folder():
    """创建文件夹"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 只有管理员可以创建文件夹
    if user.role != 'admin':
        return jsonify({'error': '无权限'}), 403
        
    data = request.get_json()
    name = data.get('name')
    parent_id = data.get('parent_id')
    
    if not name:
        return jsonify({'error': '文件夹名称不能为空'}), 400
        
    folder = FileCenterFolder(
        name=name,
        parent_id=parent_id,
        creator_id=current_user_id
    )
    db.session.add(folder)
    db.session.commit()
    
    return jsonify({'message': '文件夹创建成功', 'id': folder.id})

@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """上传文件"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # 只有管理员可以上传文件
    if user.role != 'admin':
        return jsonify({'error': '无权限'}), 403
        
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
        
    parent_id = request.form.get('parent_id', type=int)
    
    # 生成对象名称 (UUID + 原始后缀)
    ext = os.path.splitext(file.filename)[1].lower()
    object_name = f"{uuid.uuid4().hex}{ext}"
    
    # 上传到 MinIO
    try:
        size = storage_client.upload_file(file, object_name, content_type=file.content_type)
    except Exception as e:
        current_app.logger.error(f"MinIO upload failed: {e}")
        return jsonify({'error': '文件上传失败'}), 500
        
    # 保存到数据库
    new_file = FileCenterFile(
        name=file.filename,
        path=object_name, # 存储 MinIO object name
        size=size,
        type=ext.replace('.', '') if ext else 'unknown',
        folder_id=parent_id,
        uploader_id=current_user_id
    )
    db.session.add(new_file)
    db.session.commit()
    
    return jsonify({'message': '上传成功', 'id': new_file.id})

@files_bp.route('/folders/<int:id>', methods=['PUT'])
@jwt_required()
def update_folder(id):
    """更新文件夹（重命名/移动）"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'error': '无权限'}), 403
        
    folder = FileCenterFolder.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        folder.name = data['name']
    if 'parent_id' in data:
        if data['parent_id'] == folder.id:
            return jsonify({'error': '不能移动到自身'}), 400
        folder.parent_id = data['parent_id']
        
    db.session.commit()
    return jsonify({'message': '更新成功'})

@files_bp.route('/files/<int:id>', methods=['PUT'])
@jwt_required()
def update_file(id):
    """更新文件（重命名/移动）"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'error': '无权限'}), 403
        
    file = FileCenterFile.query.get_or_404(id)
    data = request.get_json()
    
    if 'name' in data:
        file.name = data['name']
    if 'folder_id' in data:
        file.folder_id = data['folder_id']
        
    db.session.commit()
    return jsonify({'message': '更新成功'})

@files_bp.route('/files/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_file(id):
    """删除文件"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'error': '无权限'}), 403
        
    file = FileCenterFile.query.get_or_404(id)
    
    # 从 MinIO 删除
    try:
        storage_client.delete_file(file.path)
    except Exception as e:
        current_app.logger.warning(f"Failed to delete file from MinIO: {e}")
        # 继续删除数据库记录
        
    db.session.delete(file)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@files_bp.route('/folders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_folder(id):
    """删除文件夹（及其内容）"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'error': '无权限'}), 403
        
    folder = FileCenterFolder.query.get_or_404(id)
    
    # 获取所有子文件并删除
    # 这里需要递归删除，或者利用 cascade='all, delete-orphan'
    # 但是我们需要物理删除 MinIO 中的文件。
    # 简单起见，这里假设用户只能删除空文件夹，或者需要先递归删除文件。
    # 为了用户体验，我们可以后台遍历删除 MinIO 文件。
    # 考虑到性能和复杂性，先实现：如果文件夹不为空，禁止删除，或者级联删除。
    # 这里实现级联删除 DB 记录（由 DB 引擎处理），但 MinIO 文件会残留。
    # **生产环境建议**：使用软删除，或者用 Celery 任务清理。
    # 本地环境：先遍历一次删除文件。
    
    def delete_recursive(folder):
        # 删除文件
        for f in folder.files:
            try:
                storage_client.delete_file(f.path)
            except:
                pass
        # 递归子文件夹
        for sub in folder.subfolders:
            delete_recursive(sub)
            db.session.delete(sub) # 显式删除子文件夹
            
    delete_recursive(folder)
    
    db.session.delete(folder)
    db.session.commit()
    return jsonify({'message': '删除成功'})

@files_bp.route('/files/<int:id>/preview', methods=['GET'])
@jwt_required()
def preview_file(id):
    """获取文件预览链接（MinIO Presigned URL）"""
    # 无需管理员权限，用户也可预览
    file = FileCenterFile.query.get_or_404(id)
    try:
        url = storage_client.get_presigned_url(file.path, original_filename=file.name)
        return jsonify({'url': url, 'type': file.type, 'name': file.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@files_bp.route('/files/<int:id>/download', methods=['GET'])
@jwt_required()
def download_file(id):
    """获取文件下载链接（强制下载）"""
    file = FileCenterFile.query.get_or_404(id)
    try:
        url = storage_client.get_download_url(file.path, original_filename=file.name)
        return jsonify({'url': url, 'type': file.type, 'name': file.name})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
