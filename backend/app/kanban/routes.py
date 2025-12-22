from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import KanbanList, KanbanCard
from ..extensions import db

kanban_bp = Blueprint('kanban', __name__)

@kanban_bp.route('/lists', methods=['GET'])
@jwt_required()
def get_lists():
    """获取看板列表"""
    # TODO: 实现看板列表获取逻辑
    return jsonify([]), 200

@kanban_bp.route('/cards', methods=['POST'])
@jwt_required()
def create_card():
    """创建看板卡片"""
    # TODO: 实现卡片创建逻辑
    return jsonify({"msg": "卡片创建成功"}), 201
