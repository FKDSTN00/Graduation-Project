from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_, or_

from ..models.models import Document, Folder, User
from ..extensions import db
from ..utils.es_service import (
    delete_document_from_index,
    index_document,
    search_document_ids,
)
from ..utils.crypto_service import encrypt_content, decrypt_content
from ..utils.privacy_service import PrivacySpaceService
from ..utils.minio_service import upload_file_to_minio, delete_file_by_url

docs_bp = Blueprint('docs', __name__)


def _parse_datetime(value):
    """将字符串或时间戳解析为 datetime，用于备份恢复保持原时间。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # 支持 ISO 字符串、RFC1123（Flask jsonify 默认格式）以及时间戳
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value))
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except Exception:
                pass
            for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except Exception:
                    continue
    except Exception:
        pass
    return None


@docs_bp.route('/attachments', methods=['POST'])
@jwt_required()
def upload_attachment():
    """上传附件（图片/视频/文件），返回可访问 URL"""
    current_user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({'msg': '未找到文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'msg': '文件名为空'}), 400
    # 为区分用户与时间生成唯一名称
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'bin'
    import uuid
    object_name = f"docs/{current_user_id}_{uuid.uuid4().hex}.{ext}"
    try:
        url = upload_file_to_minio(file, object_name, bucket_name='documents')
        return jsonify({
            'url': url,
            'name': file.filename,
            'content_type': file.content_type
        }), 200
    except Exception as exc:
        return jsonify({'msg': '附件上传失败', 'error': str(exc)}), 500


@docs_bp.route('/attachments', methods=['DELETE'])
@jwt_required()
def delete_attachment():
    """删除附件文件（用户手动移除或未保存退出时清理）"""
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({'msg': '缺少附件 URL'}), 400
    try:
        delete_file_by_url(url)
        return jsonify({'msg': '删除成功'}), 200
    except Exception as exc:
        return jsonify({'msg': '删除失败', 'error': str(exc)}), 500


def _build_like_condition(keyword: str):
    pattern = f"%{keyword}%"
    return or_(
        Document.title.ilike(pattern),
        Document.content.ilike(pattern)
    )


def _apply_split_keyword_filter(query, keyword: str):
    """将关键词拆分为单个字符做模糊匹配，提升中文单字召回率。"""
    keyword = (keyword or '').strip()
    if not keyword:
        return query

    base_condition = _build_like_condition(keyword)
    char_conditions = [_build_like_condition(char) for char in keyword if char.strip()]

    if not char_conditions:
        return query.filter(base_condition)

    combined_chars = and_(*char_conditions)
    return query.filter(or_(base_condition, combined_chars))

# --- 文件夹相关路由 ---

@docs_bp.route('/folders', methods=['GET'])
@jwt_required()
def get_folders():
    """获取当前用户的所有文件夹"""
    current_user_id = int(get_jwt_identity())
    in_privacy_space = request.args.get('in_privacy_space', 'false') == 'true'
    
    folders = Folder.query.filter_by(
        owner_id=current_user_id,
        in_privacy_space=in_privacy_space
    ).order_by(Folder.order.asc(), Folder.created_at.desc()).all()
    
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'parent_id': f.parent_id,
        'order': f.order,
        'in_privacy_space': f.in_privacy_space
    } for f in folders]), 200

@docs_bp.route('/folders/reorder', methods=['PUT'])
@jwt_required()
def reorder_folders():
    """更新文件夹排序"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 数据格式: [{'id': 1, 'order': 0}, {'id': 2, 'order': 1}]
    try:
        for item in data:
            folder = Folder.query.get(item['id'])
            if folder and folder.owner_id == current_user_id:
                folder.order = item['order']
        
        db.session.commit()
        return jsonify({'msg': '排序更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '更新失败', 'error': str(e)}), 500

@docs_bp.route('/folders', methods=['POST'])
@jwt_required()
def create_folder():
    """创建新文件夹"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    name = data.get('name')
    parent_id = data.get('parent_id')
    in_privacy_space = data.get('in_privacy_space', False)
    
    if not name:
        return jsonify({'msg': '文件夹名称不能为空'}), 400
        
    folder = Folder(
        name=name,
        parent_id=parent_id,
        owner_id=current_user_id,
        in_privacy_space=in_privacy_space
    )
    
    try:
        db.session.add(folder)
        db.session.commit()
        return jsonify({
            'id': folder.id,
            'name': folder.name,
            'parent_id': folder.parent_id,
            'order': folder.order,
            'in_privacy_space': folder.in_privacy_space,
            'msg': '文件夹创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '创建失败', 'error': str(e)}), 500

@docs_bp.route('/folders/<int:id>', methods=['PUT'])
@jwt_required()
def update_folder(id):
    """更新文件夹（重命名/移动）"""
    current_user_id = int(get_jwt_identity())
    folder = Folder.query.get_or_404(id)
    
    if folder.owner_id != current_user_id:
        return jsonify({'msg': '无权限'}), 403
        
    data = request.get_json()
    folder.name = data.get('name', folder.name)
    folder.parent_id = data.get('parent_id', folder.parent_id)
    
    try:
        db.session.commit()
        return jsonify({'msg': '更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '更新失败', 'error': str(e)}), 500

@docs_bp.route('/folders/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_folder(id):
    """删除文件夹"""
    current_user_id = int(get_jwt_identity())
    folder = Folder.query.get_or_404(id)
    
    if folder.owner_id != current_user_id:
        return jsonify({'msg': '无权限'}), 403
    
    # 若文件夹下仍有子文件夹或未删除的文档，则禁止删除，避免出现孤儿数据
    active_documents = [doc for doc in folder.documents if not doc.is_deleted]
    if folder.subfolders or active_documents:
        return jsonify({'msg': '文件夹不为空，无法删除'}), 400
        
    try:
        db.session.delete(folder)
        db.session.commit()
        return jsonify({'msg': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '删除失败', 'error': str(e)}), 500

# --- 文档相关路由 ---

@docs_bp.route('/', methods=['GET'])
@jwt_required()
def get_documents():
    """获取文档列表（支持筛选、排序）"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # 查询参数，支持按文件夹、排序方式、视图类型等进行过滤
    print(f"[DEBUG] get_documents 请求参数: {request.args}")
    folder_id = request.args.get('folder_id', type=int)
    print(f"[DEBUG] 解析后的 folder_id: {folder_id}")
    
    sort_by = request.args.get('sort_by', 'updated_at') # 可选 created_at / updated_at
    order = request.args.get('order', 'desc') # 可选 asc / desc
    is_recycle_bin = request.args.get('recycle_bin', type=str) == 'true'
    in_privacy_space = request.args.get('privacy_space', type=str) == 'true'
    
    query = Document.query.filter_by(owner_id=current_user_id)
    search_query = (request.args.get('q') or '').strip()
    search_ids = None
    
    if is_recycle_bin:
        query = query.filter_by(is_deleted=True)
    elif in_privacy_space:
        query = query.filter_by(is_deleted=False, in_privacy_space=True)
        # 隐私空间需要验证令牌
        privacy_token = request.headers.get('X-Privacy-Token')
        if not privacy_token or not PrivacySpaceService.verify_access_token(current_user_id, privacy_token):
            return jsonify({'msg': '隐私空间访问令牌无效或已过期'}), 401
            
        if folder_id is not None:
            print(f"[DEBUG] 隐私空间文件夹过滤 - folder_id: {folder_id}, 类型: {type(folder_id)}")
            if folder_id == 0: # 根目录
                query = query.filter(Document.folder_id.is_(None))
                print(f"[DEBUG] 过滤根目录文档")
            else:
                query = query.filter_by(folder_id=folder_id)
                print(f"[DEBUG] 过滤文件夹 ID={folder_id} 的文档")
    else:
        # 默认视图仅展示未删除且未在隐私空间的文档，确保不同视图互不干扰
        query = query.filter_by(is_deleted=False, in_privacy_space=False)
        if folder_id is not None:
            if folder_id == 0: # 根目录
                query = query.filter(Document.folder_id.is_(None))
            else:
                query = query.filter_by(folder_id=folder_id)

    if search_query:
        search_ids = search_document_ids(search_query, current_user_id)
        if search_ids:
            query = query.filter(Document.id.in_(search_ids))
        else:
            query = _apply_split_keyword_filter(query, search_query)
    
    # 排序字段保护，防止非法字段造成 SQL 注入
    if sort_by not in ['created_at', 'updated_at']:
        sort_by = 'updated_at'
        
    sort_column = getattr(Document, sort_by)
    if order == 'desc':
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
        
    # 置顶逻辑：普通视图中将置顶文档优先展示，其余视图使用单一排序字段
    if not is_recycle_bin and not in_privacy_space:
        query = query.order_by(Document.is_pinned.desc(), sort_column)
    else:
        query = query.order_by(sort_column)
        
    docs = query.all()
    print(f"[DEBUG] 查询返回文档数量: {len(docs)}")

    if search_ids:
        doc_map = {doc.id: doc for doc in docs}
        ordered_docs = [doc_map[doc_id] for doc_id in search_ids if doc_id in doc_map]
        docs = ordered_docs
    
    # 构建返回数据，如果是隐私空间文档需要解密
    result = []
    privacy_password = request.args.get('_privacy_password') if in_privacy_space else None
    
    if in_privacy_space:
        print(f"[DEBUG] 隐私空间查询 - 密码参数: {'已提供' if privacy_password else '未提供'}")
    
    for doc in docs:
        title = doc.title
        content = doc.content
        
        # 如果是隐私空间文档，解密标题和内容
        if doc.in_privacy_space and privacy_password:
            try:
                print(f"[DEBUG] 尝试解密文档 ID={doc.id}, 标题长度={len(title)}")
                title = decrypt_content(title, privacy_password)
                if content:
                    content = decrypt_content(content, privacy_password)
                print(f"[DEBUG] 解密成功 - 标题: {title[:20]}...")
            except Exception as e:
                # 解密失败，显示加密状态提示
                print(f"[DEBUG] 解密失败 ID={doc.id}: {str(e)}")
                title = '[加密文档 - 解密失败]'
                content = ''
        elif doc.in_privacy_space and not privacy_password:
            print(f"[DEBUG] 文档 ID={doc.id} 是隐私文档但未提供密码")
        
        # 内容预览
        content_preview = content[:200] + '...' if content and len(content) > 200 else content
        
        result.append({
            'id': doc.id,
            'title': title,
            'content': content_preview,
            'updated_at': doc.updated_at,
            'created_at': doc.created_at,
            'is_pinned': doc.is_pinned,
            'folder_id': doc.folder_id,
            'deleted_at': doc.deleted_at
        })
    
    return jsonify(result), 200

@docs_bp.route('/', methods=['POST'])
@jwt_required()
def create_document():
    """创建新文档"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    is_privacy = data.get('in_privacy_space', False)
    title = data['title']
    content = data.get('content', '')
    is_pinned = data.get('is_pinned', False)
    created_at = _parse_datetime(data.get('created_at'))
    updated_at = _parse_datetime(data.get('updated_at'))
    attachments = data.get('attachments') or []
    
    # 如果是隐私空间文档，需要验证令牌并加密内容
    if is_privacy:
        privacy_token = request.headers.get('X-Privacy-Token')
        if not privacy_token or not PrivacySpaceService.verify_access_token(current_user_id, privacy_token):
            return jsonify({'msg': '隐私空间访问令牌无效或已过期'}), 401
        
        # 使用用户的隐私空间密码加密内容
        if not user.privacy_password_hash:
            return jsonify({'msg': '尚未设置隐私空间密码'}), 400
        
        # 这里我们需要临时存储密码用于加密，实际上应该在验证时传递
        # 为简化，我们使用用户 ID 作为加密密钥的一部分
        # 更安全的做法是在验证时返回派生密钥
        privacy_password = data.get('_privacy_password')  # 前端在创建时需要传递
        if not privacy_password:
            return jsonify({'msg': '创建隐私文档需要提供密码'}), 400
        
        try:
            title = encrypt_content(title, privacy_password)
            content = encrypt_content(content, privacy_password)
        except Exception as e:
            return jsonify({'msg': '加密失败', 'error': str(e)}), 500
    
    doc = Document(
        title=title,
        content=content,
        owner_id=current_user_id,
        folder_id=data.get('folder_id'),
        in_privacy_space=is_privacy,
        is_pinned=is_pinned,
        attachments=attachments
    )
    if created_at:
        doc.created_at = created_at
    if updated_at:
        doc.updated_at = updated_at
    
    try:
        db.session.add(doc)
        db.session.commit()
        if not is_privacy:  # 隐私文档不索引到 ES
            index_document(doc)
        return jsonify({'id': doc.id, 'msg': '文档创建成功'}), 201
    except Exception as e:
        db.session.rollback()
        print(f"数据库错误: {e}")
        return jsonify({'msg': '保存失败'}), 500

@docs_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_document(id):
    """获取单个文档详情"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    doc = Document.query.get_or_404(id)
    
    # 权限检查
    if doc.owner_id != current_user_id:
        return jsonify({'msg': '无权限访问'}), 403
    
    title = doc.title
    content = doc.content
    
    # 如果是隐私空间文档，需要验证令牌并解密
    if doc.in_privacy_space:
        privacy_token = request.headers.get('X-Privacy-Token')
        privacy_password = request.args.get('_privacy_password')  # 或通过其他方式传递
        
        if not privacy_token or not PrivacySpaceService.verify_access_token(current_user_id, privacy_token):
            return jsonify({'msg': '隐私空间访问令牌无效或已过期'}), 401
        
        if not privacy_password:
            return jsonify({'msg': '访问隐私文档需要提供密码'}), 400
        
        try:
            title = decrypt_content(title, privacy_password)
            content = decrypt_content(content, privacy_password)
        except Exception as e:
            return jsonify({'msg': '解密失败，密码可能不正确', 'error': str(e)}), 400
    
    return jsonify({
        'id': doc.id,
        'title': title,
        'content': content,
        'folder_id': doc.folder_id,
        'is_pinned': doc.is_pinned,
        'in_privacy_space': doc.in_privacy_space,
        'attachments': doc.attachments or [],
        'updated_at': doc.updated_at,
        'created_at': doc.created_at
    }), 200


@docs_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_document(id):
    """更新文档"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    doc = Document.query.get_or_404(id)
    
    if doc.owner_id != current_user_id:
        return jsonify({'msg': '无权限'}), 403
    
    data = request.get_json()
    old_attachments = doc.attachments or []
    
    # 处理恢复逻辑：如果传入 restore，则撤销删除状态
    if data.get('restore'):
        doc.is_deleted = False
        doc.deleted_at = None
        try:
            db.session.commit()
            if not doc.in_privacy_space:
                index_document(doc)
            return jsonify({'msg': '文档已恢复'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'msg': '恢复失败', 'error': str(e)}), 500
    
    # 如果文档在隐私空间，更新时需要重新加密
    if doc.in_privacy_space:
        privacy_token = request.headers.get('X-Privacy-Token')
        privacy_password = data.get('_privacy_password')
        
        if not privacy_token or not PrivacySpaceService.verify_access_token(current_user_id, privacy_token):
            return jsonify({'msg': '隐私空间访问令牌无效或已过期'}), 401
        
        if not privacy_password:
            return jsonify({'msg': '更新隐私文档需要提供密码'}), 400
        
        try:
            if 'title' in data:
                doc.title = encrypt_content(data['title'], privacy_password)
            if 'content' in data:
                doc.content = encrypt_content(data['content'], privacy_password)
        except Exception as e:
            return jsonify({'msg': '加密失败', 'error': str(e)}), 500
    else:
        if 'title' in data:
            doc.title = data['title']
        if 'content' in data:
            doc.content = data['content']
    
    if 'folder_id' in data:
        doc.folder_id = data['folder_id']
        
    if 'is_pinned' in data:
        doc.is_pinned = data['is_pinned']

    if 'attachments' in data:
        doc.attachments = data['attachments']
        # 删除已移除的附件文件
        new_urls = {att.get('url') for att in (data['attachments'] or []) if att.get('url')}
        for att in old_attachments:
            url = att.get('url') if isinstance(att, dict) else att
            if url and url not in new_urls:
                try:
                    delete_file_by_url(url)
                except Exception as exc:
                    print(f'删除附件失败 {url}: {exc}')
    
    # 备份恢复时允许回写时间戳
    created_at = _parse_datetime(data.get('created_at'))
    updated_at = _parse_datetime(data.get('updated_at'))
    if created_at:
        doc.created_at = created_at
    if updated_at:
        doc.updated_at = updated_at
        
    if 'in_privacy_space' in data:
        doc.in_privacy_space = data['in_privacy_space']
    
    try:
        db.session.commit()
        if not doc.in_privacy_space:
            index_document(doc)
        return jsonify({'msg': '文档更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '更新失败', 'error': str(e)}), 500

@docs_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_document(id):
    """删除文档"""
    current_user_id = int(get_jwt_identity())
    doc = Document.query.get_or_404(id)
    
    if doc.owner_id != current_user_id:
        return jsonify({'msg': '无权限'}), 403
        
    hard_delete = request.args.get('hard_delete', type=str) == 'true'
    
    # 隐私空间的文档直接物理删除，避免回收站遗留敏感数据
    if doc.in_privacy_space:
        hard_delete = True
        
    if hard_delete or doc.is_deleted: # 已在回收站的文档直接执行物理删除
        try:
            from ..utils.minio_service import delete_file_by_url, delete_images_from_content
            
            # 1. 删除 attachments 列表中的附件
            if doc.attachments:
                for attachment_url in doc.attachments:
                    try:
                        delete_file_by_url(attachment_url)
                    except Exception as e:
                        print(f"删除附件失败 {attachment_url}: {e}")
            
            # 2. 如果不是隐私空间文档（内容未加密），解析内容并删除嵌入的图片
            if not doc.in_privacy_space:
                delete_images_from_content(doc.content)
            
            db.session.delete(doc)
            db.session.commit()
            delete_document_from_index(doc.id)
            return jsonify({'msg': '文档已彻底删除'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'msg': '删除失败', 'error': str(e)}), 500
    else:
        # 软删除：标记状态并记录删除时间，后续可从回收站恢复
        doc.is_deleted = True
        doc.deleted_at = datetime.utcnow()
        try:
            db.session.commit()
            delete_document_from_index(doc.id)
            return jsonify({'msg': '文档已移入回收站'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'msg': '删除失败', 'error': str(e)}), 500

@docs_bp.route('/recycle-bin/clear', methods=['DELETE'])
@jwt_required()
def clear_recycle_bin():
    """清空回收站"""
    current_user_id = int(get_jwt_identity())
    try:
        # 保留将被清理的文档 ID 和附件，以便在清空数据库记录后同步清除
        recycled_docs = Document.query.filter_by(owner_id=current_user_id, is_deleted=True).all()
        doc_ids = [doc.id for doc in recycled_docs]
        
        # 收集所有附件 URL
        from ..utils.minio_service import delete_file_by_url, delete_images_from_content
        for doc in recycled_docs:
            # 1. 删除附件列表
            if doc.attachments:
                for attachment_url in doc.attachments:
                    try:
                        delete_file_by_url(attachment_url)
                    except Exception as e:
                        print(f"删除附件失败 {attachment_url}: {e}")
            
            # 2. 从内容中删除图片
            if not doc.in_privacy_space: # 回收站通常不包含隐私文档，但防御性检查
                delete_images_from_content(doc.content)
        
        Document.query.filter_by(owner_id=current_user_id, is_deleted=True).delete(synchronize_session=False)
        db.session.commit()
        for doc_id in doc_ids:
            delete_document_from_index(doc_id)
        return jsonify({'msg': '回收站已清空'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '清空失败', 'error': str(e)}), 500

@docs_bp.route('/search', methods=['GET'])
@jwt_required()
def search_documents():
    """搜索文档"""
    keyword = (request.args.get('q') or '').strip()
    current_user_id = int(get_jwt_identity())

    if not keyword:
        return jsonify([]), 200

    # 优先通过 Elasticsearch 获取匹配的文档 ID，若 ES 不可用则回退数据库模糊匹配
    search_ids = search_document_ids(keyword, current_user_id)
    query = Document.query.filter(
        Document.owner_id == current_user_id,
        Document.is_deleted == False
    )

    if search_ids:
        query = query.filter(Document.id.in_(search_ids))
    else:
        query = _apply_split_keyword_filter(query, keyword)

    docs = query.order_by(Document.updated_at.desc()).all()

    if search_ids:
        doc_map = {doc.id: doc for doc in docs}
        docs = [doc_map[doc_id] for doc_id in search_ids if doc_id in doc_map]
    
    return jsonify([{
        'id': doc.id,
        'title': doc.title,
        'updated_at': doc.updated_at
    } for doc in docs]), 200
