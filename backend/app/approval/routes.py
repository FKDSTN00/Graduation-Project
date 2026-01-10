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
        'current_approver': {
            'id': approval.current_approver.id,
            'username': approval.current_approver.username
        } if approval.current_approver else None,
        'created_at': approval.created_at.isoformat()
    }


@approval_bp.route('/', methods=['POST'])
@jwt_required()
def create_approval():
    """提交审批申请"""
    try:
        current_user_id = int(get_jwt_identity())  # 转换为整数
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
        
        # 根据角色层级确定上一级审批人
        # user → lead, lead → manager, manager → admin
        from ..models.models import Role
        from flask import current_app
        
        approver_id = None
        current_role = user.role  # 使用 @property
        
        current_app.logger.info(f"创建审批 - 申请人: {user.username}(ID:{current_user_id}), 角色: {current_role}")
        
        # 角色层级映射：当前角色 -> 上一级角色
        role_hierarchy = {
            'user': 'lead',
            'lead': 'manager',
            'manager': 'admin'
        }
        
        next_role = role_hierarchy.get(current_role)
        
        if not next_role:
            return jsonify({"msg": f"{current_role} 角色无法发起审批"}), 400
        
        # 查找拥有上一级角色的用户
        next_role_obj = Role.query.filter_by(code=next_role).first()
        if next_role_obj:
            # 优先查找同部门的上一级（如果有部门信息）
            if user.department_id:
                approver = User.query.filter(
                    User.role_id == next_role_obj.id,
                    User.department_id == user.department_id
                ).first()
                if approver:
                    approver_id = approver.id
                    current_app.logger.info(f"{current_role} 申请 -> 同部门 {next_role} 审批: {approver.username}(ID:{approver_id})")
            
            # 如果同部门没有，查找任意一个拥有该角色的用户
            if not approver_id:
                approver = User.query.filter_by(role_id=next_role_obj.id).first()
                if approver:
                    approver_id = approver.id
                    current_app.logger.info(f"{current_role} 申请 -> {next_role} 审批: {approver.username}(ID:{approver_id})")
        
        if not approver_id:
            current_app.logger.error(f"未找到 {next_role} 角色的审批人")
            return jsonify({"msg": f"未找到 {next_role} 角色的审批人"}), 400

        new_approval = ApprovalFlow(
            title=title,
            applicant_id=current_user_id,
            current_approver_id=approver_id,
            type=app_type,
            status='pending',
            details=details,
            created_at=datetime.utcnow() + timedelta(hours=8)
        )
        
        db.session.add(new_approval)
        db.session.commit()
        
        current_app.logger.info(f"审批创建成功 - ID:{new_approval.id}, 申请人:{current_user_id}, 审批人:{approver_id}")
        
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
    current_user_id = int(get_jwt_identity())  # 转换为整数
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
    
    from sqlalchemy import or_, and_
    from ..models.models import Role
    from flask import current_app
    
    current_app.logger.info(f"获取审批列表 - 用户ID: {current_user_id}, 用户名: {user.username}, 角色: {user.role}")
    
    
    if user.role == 'admin':
        # Admin看所有发给自己审批的申请
        approvals = ApprovalFlow.query.filter(
            ApprovalFlow.current_approver_id == current_user_id
        ).order_by(ApprovalFlow.created_at.desc()).all()
        current_app.logger.info(f"Admin查询结果数量: {len(approvals)}")
    elif user.role in ['manager', 'lead']:
        # Manager/Lead看两类：1.发给自己审批的（下级申请） 2.自己发起的
        from sqlalchemy import or_
        
        approvals = ApprovalFlow.query.filter(
            or_(
                ApprovalFlow.current_approver_id == current_user_id,  # 待审批的
                ApprovalFlow.applicant_id == current_user_id  # 自己发起的
            )
        ).order_by(ApprovalFlow.created_at.desc()).all()
        current_app.logger.info(f"{user.role}查询结果数量: {len(approvals)}")
        for a in approvals:
            current_app.logger.info(f"  - ID:{a.id}, 申请人:{a.applicant_id}, 审批人:{a.current_approver_id}, 状态:{a.status}")
    else:
        # user只查看自己的申请
        approvals = ApprovalFlow.query.filter(
            ApprovalFlow.applicant_id == current_user_id
        ).order_by(ApprovalFlow.created_at.desc()).all()
        
    return jsonify([to_dict(a) for a in approvals]), 200


@approval_bp.route('/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_status(id):
    """更新审批状态"""
    current_user_id = int(get_jwt_identity())  # 转换为整数
    user = User.query.get(current_user_id)
    
    approval = ApprovalFlow.query.get_or_404(id)
    
    # 权限检查：必须是当前审批人
    is_approver = (approval.current_approver_id == current_user_id)
    
    if not is_approver:
         return jsonify({"msg": "权限不足，非当前审批人"}), 403

    data = request.get_json()
    action = data.get('action')
    
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
            notif_content = f"您的重置密码申请已通过，新密码为：{new_password}"
            
            # 发送邮件通知用户
            try:
                msg = Message(
                    "【密码重置成功】您的密码已重置",
                    recipients=[target_user.email]
                )
                msg.body = f"""尊敬的用户 {target_user.username}：

您好！

您的密码重置申请已通过审批。

新密码为：{new_password}

请使用新密码登录系统，并建议您登录后尽快修改密码。

---
此邮件为系统自动发送，请勿直接回复。
"""
                mail.send(msg)
                from flask import current_app
                current_app.logger.info(f"密码重置邮件已发送到: {target_user.email}")
            except Exception as e:
                # 邮件发送失败只记录警告，不影响密码重置
                import logging
                logging.warning(f"邮件发送失败: {str(e)}")
                
        elif action == 'reject':
            approval.status = 'rejected'
            notif_content = f"您的重置密码申请已被拒绝。"
            
            # 发送邮件通知用户
            try:
                msg = Message(
                    "【密码重置被拒绝】您的密码重置申请未通过",
                    recipients=[target_user.email]
                )
                msg.body = f"""尊敬的用户 {target_user.username}：

您好！

您的密码重置申请已被管理员拒绝。

如果您确实需要重置密码，请联系系统管理员获取帮助。

---
此邮件为系统自动发送，请勿直接回复。
"""
                mail.send(msg)
                from flask import current_app
                current_app.logger.info(f"密码重置拒绝邮件已发送到: {target_user.email}")
            except Exception as e:
                # 邮件发送失败只记录警告
                import logging
                logging.warning(f"邮件发送失败: {str(e)}")
                
    else:
        # Standard Logic - 单级审批
        if action == 'approve':
            approval.status = 'approved'
            notif_content = f"您的 [{approval.title}] 已通过审批。"
        elif action == 'reject':
            approval.status = 'rejected'
            notif_content = f"您的 [{approval.title}] 未通过审批。"
        else:
            return jsonify({"msg": "无效操作"}), 400
    
    
    # 创建通知（密码重置类型除外，因为用户登录不进去）
    if approval.type != 'password_reset':
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
    """清空已处理的审批记录"""
    current_user_id = int(get_jwt_identity())  # 转换为整数
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"msg": "用户不存在"}), 404
        
    try:
        from sqlalchemy import or_
        
        if user.role == 'admin':
            # Admin 清空所有已处理记录
            deleted_count = ApprovalFlow.query.filter(ApprovalFlow.status != 'pending').delete()
        elif user.role in ['manager', 'lead']:
            # Manager/Lead 清空：自己审批过的 OR 自己发起的（已处理）
            deleted_count = ApprovalFlow.query.filter(
                ApprovalFlow.status != 'pending',
                or_(
                    ApprovalFlow.current_approver_id == current_user_id,
                    ApprovalFlow.applicant_id == current_user_id
                )
            ).delete(synchronize_session=False)
        else:
            # User 清空自己发起的已处理记录
            deleted_count = ApprovalFlow.query.filter(
                ApprovalFlow.status != 'pending',
                ApprovalFlow.applicant_id == current_user_id
            ).delete(synchronize_session=False)
        
        db.session.commit()
        return jsonify({"msg": f"已成功清除 {deleted_count} 条记录"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"操作失败: {str(e)}"}), 500











