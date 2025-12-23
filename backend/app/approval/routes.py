from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import ApprovalFlow, User, SystemNotification
from ..extensions import db
from datetime import datetime, timedelta

approval_bp = Blueprint('approval', __name__)

def to_dict(approval):
    return {
        'id': approval.id,
        'title': approval.title,
        'applicant': {
            'id': approval.applicant.id,
            'username': approval.applicant.username,
            'email': approval.applicant.email,
            'avatar': approval.applicant.avatar
        },
        'type': approval.type,
        'status': approval.status,
        'details': approval.details,
        'created_at': approval.created_at.isoformat()
    }

@approval_bp.route('/', methods=['POST'])
@jwt_required()
def create_approval():
    """提交审批申请"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        app_type = data.get('type')
        details = data.get('details', {})
        
        # 映射类型到中文标题
        type_map = {
            'intern_conversion': '实习生转正申请',
            'leave': '请假申请',
            'time_off': '调休申请',
            'business_trip': '出差申请',
            'salary_advance': '工资预支申请',
            'password_reset': '重置密码申请'
        }
        
        title_prefix = type_map.get(app_type, '审批申请')
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"msg": "用户不存在"}), 404

        title = f"{user.username}的{title_prefix}"
        
        new_approval = ApprovalFlow(
            title=title,
            applicant_id=current_user_id,
            type=app_type,
            status='pending',
            details=details,
            created_at=datetime.utcnow() + timedelta(hours=8)
        )
        
        db.session.add(new_approval)
        db.session.commit()
        
        return jsonify({
            "msg": "申请提交成功", 
            "data": {
                'id': new_approval.id,
                'title': new_approval.title,
                'applicant': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'avatar': user.avatar
                },
                'type': new_approval.type,
                'status': new_approval.status,
                'details': new_approval.details,
                'created_at': new_approval.created_at.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = f"Error creating approval: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        with open('/home/ztx/桌面/Project/backend/approval_error.log', 'w') as f:
            f.write(error_msg)
        return jsonify({"msg": f"系统错误: {str(e)}"}), 500

@approval_bp.route('/', methods=['GET'])
@jwt_required()
def get_approvals():
    """获取审批列表"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    
    if user.role == 'admin':
        # 管理员查看所有
        approvals = ApprovalFlow.query.order_by(ApprovalFlow.created_at.desc()).all()
    else:
        # 用户查看自己的
        approvals = ApprovalFlow.query.filter_by(applicant_id=current_user_id).order_by(ApprovalFlow.created_at.desc()).all()
        
    return jsonify([to_dict(a) for a in approvals]), 200

@approval_bp.route('/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_status(id):
    """更新审批状态 (管理员)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != 'admin':
        return jsonify({"msg": "权限不足"}), 403
        
    data = request.get_json()
    action = data.get('action') # 'approve' or 'reject'
    
    approval = ApprovalFlow.query.get_or_404(id)
    
    # Handle Password Reset Special Logic
    if approval.type == 'password_reset':
        from flask_mail import Message
        from ..extensions import mail
        
        target_user = User.query.get(approval.applicant_id)
        if not target_user:
            return jsonify({"msg": "申请用户不存在"}), 404
            
        if action == 'approve':
            new_password = data.get('new_password')
            if not new_password:
                return jsonify({"msg": "同意重置密码时必须提供新密码"}), 400
            
            # Reset Password
            target_user.set_password(new_password)
            approval.status = 'approved'
            notif_content = f"您的重置密码申请已通过，新密码已发送至您的邮箱。"
            
            # Send Email
            try:
                msg = Message("密码重置通知", recipients=[target_user.email])
                msg.body = f"尊敬的用户 {target_user.username}，您的密码重置申请已通过。\n\n您的新密码为：{new_password}\n\n请尽快登录并修改密码。"
                mail.send(msg)
            except Exception as e:
                db.session.rollback()
                return jsonify({"msg": f"邮件发送失败: {str(e)}"}), 500
                
        elif action == 'reject':
            approval.status = 'rejected'
            notif_content = f"您的重置密码申请已被拒绝。"
            
            # Send Email
            try:
                msg = Message("密码重置申请拒绝通知", recipients=[target_user.email])
                msg.body = f"尊敬的用户 {target_user.username}，您的密码重置申请已被管理员拒绝。"
                mail.send(msg)
            except Exception as e:
                db.session.rollback()
                return jsonify({"msg": f"邮件发送失败: {str(e)}"}), 500
                
    else:
        # Standard Logic
        if action == 'approve':
            approval.status = 'approved'
            notif_content = f"您的 [{approval.title}] 已通过审批。"
        elif action == 'reject':
            approval.status = 'rejected'
            notif_content = f"您的 [{approval.title}] 未通过审批。"
        else:
            return jsonify({"msg": "无效操作"}), 400
    
    # 创建通知
    notification = SystemNotification(
        user_id=approval.applicant_id,
        title="审批结果通知",
        content=notif_content,
        created_at=datetime.utcnow() + timedelta(hours=8)
    )
    db.session.add(notification)
    
    # 提交更改
    db.session.commit()
    
    return jsonify({"msg": "操作成功", "data": to_dict(approval)}), 200

@approval_bp.route('/processed', methods=['DELETE'])
@jwt_required()
def clear_processed():
    """清空已处理的审批记录 (管理员)"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or user.role != 'admin':
        return jsonify({"msg": "权限不足"}), 403
        
    try:
        # 删除所有状态不是 pending 的记录
        deleted_count = ApprovalFlow.query.filter(ApprovalFlow.status != 'pending').delete()
        db.session.commit()
        return jsonify({"msg": f"已成功清除 {deleted_count} 条记录"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"操作失败: {str(e)}"}), 500
