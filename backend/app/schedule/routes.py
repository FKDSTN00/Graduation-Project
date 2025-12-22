from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Schedule, Meeting
from ..extensions import db

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/', methods=['GET'])
@jwt_required()
def get_schedules():
    """获取日程列表"""
    current_user_id = get_jwt_identity()
    # TODO: 实现日程获取逻辑
    return jsonify([]), 200

@schedule_bp.route('/meetings', methods=['POST'])
@jwt_required()
def create_meeting():
    """创建会议"""
    current_user_id = get_jwt_identity()
    # TODO: 实现会议创建逻辑
    return jsonify({"msg": "会议创建成功"}), 201
