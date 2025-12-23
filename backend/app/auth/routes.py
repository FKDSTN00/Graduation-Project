from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..models.models import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"msg": "请求数据格式错误", "error": "INVALID_REQUEST"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"msg": "用户名和密码不能为空", "error": "MISSING_CREDENTIALS"}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({"msg": "用户不存在", "error": "USER_NOT_FOUND"}), 401
        
        if not user.check_password(password):
            return jsonify({"msg": "密码错误", "error": "INVALID_PASSWORD"}), 401
        
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "access_token": access_token,
            "msg": "登录成功",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar": user.avatar
            }
        }), 200
    except Exception as e:
        return jsonify({"msg": "服务器错误", "error": "SERVER_ERROR", "details": str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口"""
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "用户名已存在"}), 400
        
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"msg": "用户注册成功"}), 201

from ..models.models import ApprovalFlow
from datetime import datetime, timedelta

@auth_bp.route('/forgot-password', methods=['POST'])
def request_password_reset():
    """申请重置密码"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    
    user = User.query.filter_by(username=username, email=email).first()
    if not user:
        return jsonify({"msg": "用户名和邮箱不匹配或用户不存在"}), 400
        
    # Check if a pending request already exists
    pending = ApprovalFlow.query.filter(
        ApprovalFlow.applicant_id == user.id,
        ApprovalFlow.type == 'password_reset',
        ApprovalFlow.status == 'pending'
    ).first()
    
    if pending:
        return jsonify({"msg": "您已有一个待处理的重置申请"}), 400
        
    # Create Approval Request for Admin
    title = f"{username}忘记密码，申请重置密码"
    approval = ApprovalFlow(
        title=title,
        applicant_id=user.id,
        type='password_reset',
        status='pending',
        details={'reason': '用户忘记密码申请重置', 'target_user_id': user.id},
        created_at=datetime.utcnow() + timedelta(hours=8)
    )
    
    db.session.add(approval)
    db.session.commit()
    
    return jsonify({"msg": "申请已提交，请等待管理员审核"}), 200
