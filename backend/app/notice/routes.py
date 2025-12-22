from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.models import Notice, Vote
from ..extensions import db

notice_bp = Blueprint('notice', __name__)

@notice_bp.route('/', methods=['GET'])
@jwt_required()
def get_notices():
    """获取公告列表"""
    # TODO: 实现公告获取逻辑
    return jsonify([]), 200

@notice_bp.route('/vote', methods=['POST'])
@jwt_required()
def create_vote():
    """发起投票"""
    # TODO: 实现投票创建逻辑
    return jsonify({"msg": "投票发起成功"}), 201
