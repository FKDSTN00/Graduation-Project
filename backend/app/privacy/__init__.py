"""
隐私空间 API
提供密码设置、验证、令牌管理等功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models.models import User
from ..extensions import db
from ..utils.privacy_service import PrivacySpaceService

privacy_bp = Blueprint('privacy', __name__)


@privacy_bp.route('/check-password', methods=['GET'])
@jwt_required()
def check_password_exists():
    """
    检查用户是否已设置隐私空间密码
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    has_password = bool(user.privacy_password_hash)
    
    return jsonify({
        'has_password': has_password
    }), 200


@privacy_bp.route('/set-password', methods=['POST'])
@jwt_required()
def set_privacy_password():
    """
    设置或修改隐私空间密码
    首次设置时直接设置，修改时需要验证旧密码
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    new_password = data.get('password')
    old_password = data.get('old_password')
    
    if not new_password:
        return jsonify({'msg': '请提供新密码'}), 400
    
    if len(new_password) < 6:
        return jsonify({'msg': '密码长度不能少于6位'}), 400
    
    # 如果已有密码，需要验证旧密码
    if user.privacy_password_hash:
        if not old_password:
            return jsonify({'msg': '请提供旧密码'}), 400
        
        if not user.check_privacy_password(old_password):
            return jsonify({'msg': '旧密码错误'}), 400
        
        # 修改密码后撤销现有令牌
        PrivacySpaceService.revoke_access_token(current_user_id)
    
    try:
        user.set_privacy_password(new_password)
        db.session.commit()
        
        return jsonify({'msg': '隐私空间密码设置成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '设置失败', 'error': str(e)}), 500


@privacy_bp.route('/verify-password', methods=['POST'])
@jwt_required()
def verify_privacy_password():
    """
    验证隐私空间密码
    成功后返回访问令牌（有效期3分钟）
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    password = data.get('password')
    
    if not password:
        return jsonify({'msg': '请提供密码'}), 400
    
    if not user.privacy_password_hash:
        return jsonify({'msg': '尚未设置隐私空间密码'}), 400
    
    if not user.check_privacy_password(password):
        return jsonify({'msg': '密码错误'}), 401
    
    # 生成访问令牌
    token = PrivacySpaceService.generate_access_token(current_user_id)
    
    if not token:
        return jsonify({'msg': '生成令牌失败'}), 500
    
    return jsonify({
        'msg': '验证成功',
        'access_token': token,
        'expires_in': PrivacySpaceService.TOKEN_EXPIRY
    }), 200


@privacy_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_privacy_token():
    """
    验证隐私空间访问令牌是否有效
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    token = data.get('token')
    
    if not token:
        return jsonify({'valid': False, 'msg': '未提供令牌'}), 400
    
    valid = PrivacySpaceService.verify_access_token(current_user_id, token)
    
    return jsonify({
        'valid': valid
    }), 200


@privacy_bp.route('/refresh-token', methods=['POST'])
@jwt_required()
def refresh_privacy_token():
    """
    刷新隐私空间访问令牌的有效期
    """
    current_user_id = int(get_jwt_identity())
    data = request.get_json()
    
    token = data.get('token')
    
    if not token:
        return jsonify({'msg': '未提供令牌'}), 400
    
    success = PrivacySpaceService.refresh_access_token(current_user_id, token)
    
    if success:
        return jsonify({
            'msg': '令牌已刷新',
            'expires_in': PrivacySpaceService.TOKEN_EXPIRY
        }), 200
    else:
        return jsonify({'msg': '令牌无效或已过期'}), 401


@privacy_bp.route('/revoke-token', methods=['POST'])
@jwt_required()
def revoke_privacy_token():
    """
    撤销隐私空间访问令牌（退出隐私空间）
    """
    current_user_id = int(get_jwt_identity())
    
    PrivacySpaceService.revoke_access_token(current_user_id)
    
    return jsonify({'msg': '已退出隐私空间'}), 200
