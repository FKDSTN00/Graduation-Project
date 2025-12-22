from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import ApprovalFlow
from ..extensions import db

approval_bp = Blueprint('approval', __name__)

@approval_bp.route('/', methods=['POST'])
@jwt_required()
def create_approval():
    """提交审批申请"""
    current_user_id = get_jwt_identity()
    # TODO: 实现审批创建逻辑
    return jsonify({"msg": "审批申请提交成功"}), 201

@approval_bp.route('/', methods=['GET'])
@jwt_required()
def get_approvals():
    """获取审批列表"""
    current_user_id = get_jwt_identity()
    # TODO: 实现审批列表获取逻辑
    return jsonify([]), 200
