from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.models import KnowledgeCategory, KnowledgeArticle, User

bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

# ==================== 分类管理 ====================

@bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """获取所有分类"""
    categories = KnowledgeCategory.query.order_by(KnowledgeCategory.order.asc()).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'order': c.order,
        'article_count': c.articles.count()
    } for c in categories]), 200

@bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """创建分类（仅管理员）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'msg': '权限不足'}), 403
    
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'msg': '分类名称不能为空'}), 400
    
    category = KnowledgeCategory(
        name=name,
        order=data.get('order', 0)
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'msg': '创建成功',
        'data': {
            'id': category.id,
            'name': category.name,
            'order': category.order
        }
    }), 200

@bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    """更新分类（仅管理员）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'msg': '权限不足'}), 403
    
    category = KnowledgeCategory.query.get_or_404(category_id)
    data = request.get_json()
    
    if 'name' in data:
        category.name = data['name']
    if 'order' in data:
        category.order = data['order']
    
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '更新成功'}), 200

@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    """删除分类（仅管理员）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'msg': '权限不足'}), 403
    
    category = KnowledgeCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '删除成功'}), 200

# ==================== 文章管理 ====================

@bp.route('/articles', methods=['GET'])
@jwt_required()
def get_articles():
    """获取文章列表"""
    category_id = request.args.get('category_id', type=int)
    
    query = KnowledgeArticle.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    articles = query.order_by(KnowledgeArticle.updated_at.desc()).all()
    
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'content': a.content,
        'category_id': a.category_id,
        'category_name': a.category.name if a.category else '未分类',
        'author': a.author.username if a.author else 'Unknown',
        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': a.updated_at.strftime('%Y-%m-%d %H:%M')
    } for a in articles]), 200

@bp.route('/articles/<int:article_id>', methods=['GET'])
@jwt_required()
def get_article(article_id):
    """获取文章详情"""
    article = KnowledgeArticle.query.get_or_404(article_id)
    
    return jsonify({
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'category_id': article.category_id,
        'category_name': article.category.name if article.category else '未分类',
        'author': article.author.username if article.author else 'Unknown',
        'created_at': article.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at': article.updated_at.strftime('%Y-%m-%d %H:%M')
    }), 200

@bp.route('/articles', methods=['POST'])
@jwt_required()
def create_article():
    """创建文章（仅管理员）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'msg': '权限不足'}), 403
    
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    
    if not title:
        return jsonify({'msg': '标题不能为空'}), 400
    
    article = KnowledgeArticle(
        title=title,
        content=content,
        category_id=data.get('category_id'),
        author_id=user_id
    )
    
    db.session.add(article)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'msg': '创建成功',
        'data': {'id': article.id}
    }), 200

@bp.route('/articles/<int:article_id>', methods=['PUT'])
@jwt_required()
def update_article(article_id):
    """更新文章（仅管理员）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'msg': '权限不足'}), 403
    
    article = KnowledgeArticle.query.get_or_404(article_id)
    data = request.get_json()
    
    if 'title' in data:
        article.title = data['title']
    if 'content' in data:
        article.content = data['content']
    if 'category_id' in data:
        article.category_id = data['category_id']
    
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '更新成功'}), 200

@bp.route('/articles/<int:article_id>', methods=['DELETE'])
@jwt_required()
def delete_article(article_id):
    """删除文章（仅管理员）"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role != 'admin':
        return jsonify({'msg': '权限不足'}), 403
    
    article = KnowledgeArticle.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    
    return jsonify({'code': 200, 'msg': '删除成功'}), 200
