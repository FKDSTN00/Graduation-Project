from flask import jsonify, request
from . import org_bp
from ..models.models import Department, Role, User
from ..extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity

@org_bp.route('/departments/tree', methods=['GET'])
@jwt_required()
def get_department_tree():
    """获取部门树"""
    # 获取顶级部门
    roots = Department.query.filter_by(parent_id=None).order_by(Department.order).all()
    
    def build_tree(dept):
        children = [build_tree(child) for child in dept.children]
        return {
            'id': dept.id,
            'label': dept.name,
            'managerId': dept.manager_id,
            'managerName': dept.manager.username if dept.manager else None,
            'children': children
        }
    
    tree_data = [build_tree(root) for root in roots]
    return jsonify(tree_data)

@org_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """获取所有角色"""
    roles = Role.query.all()
    # Sort roles: admin(hidden or first), manager, lead, user
    # Desired order for dropdown: Manager, Lead, User. Admin usually separate.
    # Map code to sort index
    sort_map = {'manager': 1, 'lead': 2, 'user': 3, 'admin': 0}
    
    roles_sorted = sorted(roles, key=lambda r: sort_map.get(r.code, 99))

    return jsonify([{
        'id': r.id,
        'name': r.name,
        'code': r.code,
        'description': r.description,
        'permissions': r.permissions
    } for r in roles_sorted])

@org_bp.route('/departments', methods=['POST'])
@jwt_required()
def create_department():
    """创建部门"""
    # 鉴权: 仅 Admin 可操作 (简化)
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    # 这里应该用 Role 判断，但暂时先假设 role_id=1 或 code='admin' 是管理员
    # 为了严谨，查 Role 表
    if not user.role_rel or user.role_rel.code != 'admin':
         return jsonify({'msg': '权限不足'}), 403

    data = request.get_json()
    name = data.get('name')
    parent_id = data.get('parentId')
    
    if not name:
        return jsonify({'msg': '部门名称不能为空'}), 400
        
    dept = Department(name=name, parent_id=parent_id)
    db.session.add(dept)
    db.session.commit()
    return jsonify({'msg': '创建成功', 'id': dept.id})

@org_bp.route('/users/<int:user_id>/assign', methods=['PUT'])
@jwt_required()
def assign_user_org(user_id):
    """分配用户部门和角色"""
    current_user_id = get_jwt_identity()
    operator = User.query.get(current_user_id)
    if not operator.role_rel or operator.role_rel.code != 'admin':
         return jsonify({'msg': '权限不足'}), 403

    target = User.query.get_or_404(user_id)
    data = request.get_json()
    
    dept_id = data.get('departmentId')
    role_id = data.get('roleId')
    
    if dept_id:
        target.department_id = dept_id
    if role_id:
        target.role_id = role_id
        
    db.session.commit()
    return jsonify({'msg': '分配成功'})

@org_bp.route('/departments/<int:id>', methods=['PUT'])
@jwt_required()
def update_department(id):
    """更新部门信息 (如设置主管)"""
    # 鉴权
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user.role_rel or user.role_rel.code != 'admin':
         return jsonify({'msg': '权限不足'}), 403

    dept = Department.query.get_or_404(id)
    data = request.get_json()
    
    if 'managerId' in data:
        old_manager_id = dept.manager_id
        new_manager_id = data['managerId']
        
        dept.manager_id = new_manager_id
        
        # 1. Demote old manager if changed
        if old_manager_id and old_manager_id != new_manager_id:
            old_user = User.query.get(old_manager_id)
            # If old user is found and not admin, reset to 'user'
            if old_user and (not old_user.role_rel or old_user.role_rel.code != 'admin'):
                user_role = Role.query.filter_by(code='user').first()
                if user_role:
                    old_user.role_id = user_role.id

        # 2. Promote new manager
        if dept.manager_id:
            # Check for name update or use existing name for exception
            current_dept_name = data.get('name', dept.name)
            
            manager_user = User.query.get(dept.manager_id)
            if manager_user:
                # Except '总经办'
                if current_dept_name != '总经办':
                     if not manager_user.role_rel or manager_user.role_rel.code != 'admin':
                        # Level 1 department (parent_id is None) -> Manager
                        # Level 2 department (parent_id is not None) -> Lead
                        target_role_code = 'manager' if dept.parent_id is None else 'lead'
                        target_role = Role.query.filter_by(code=target_role_code).first()
                        if target_role:
                            manager_user.role_id = target_role.id
    
    if 'name' in data:
        dept.name = data['name']
    
    if 'order' in data:
        dept.order = int(data['order'])
        
    db.session.commit()
    return jsonify({'msg': '更新成功'})

@org_bp.route('/departments/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_department(id):
    """删除部门"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user.role_rel or user.role_rel.code != 'admin':
         return jsonify({'msg': '权限不足'}), 403

    dept = Department.query.get_or_404(id)
    
    # 检查是否有子部门或员工
    if dept.children.count() > 0:
        return jsonify({'msg': '无法删除：该部门包含子部门'}), 400
    if dept.users and len(dept.users) > 0:
        return jsonify({'msg': '无法删除：该部门下还有员工'}), 400
        
    db.session.delete(dept)
    db.session.commit()
    return jsonify({'msg': '部门已删除'})

@org_bp.route('/departments/reorder', methods=['POST'])
@jwt_required()
def reorder_departments():
    """批量调整部门顺序/层级"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user.role_rel or user.role_rel.code != 'admin':
         return jsonify({'msg': '权限不足'}), 403
         
    data = request.get_json()
    nodes = data.get('nodes', [])
    
    for node in nodes:
        dept_id = node.get('id')
        parent_id = node.get('parent_id')
        order = node.get('order')
        
        dept = Department.query.get(dept_id)
        if dept:
            dept.parent_id = parent_id
            dept.order = order
            
    db.session.commit()
    return jsonify({'msg': '顺序调整成功'})


