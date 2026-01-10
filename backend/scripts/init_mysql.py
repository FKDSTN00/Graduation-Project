#!/usr/bin/env python3
"""
MySQL 数据库初始化脚本
创建所有数据库表并初始化默认管理员账户
"""

import sys
import os

# 添加当前目录到 path (在容器中运行)
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models.models import (
    User, Document, Schedule, Meeting,
    ApprovalFlow, Notice, Vote, AISession, AIMessage, Task, FileCenterFolder, FileCenterFile, SystemNotification,
    Department, Role, TaskComment, AuditLog
)

from sqlalchemy import text

def create_tables():
    """创建所有数据库表并初始化基础数据"""
    app = create_app()
    
    with app.app_context():
        # 重置所有表 (开发环境方便，生产环境需谨慎)
        print("⚠️  正在重置数据库...")
        try:
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
            # 获取所有表名
            result = db.session.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            if tables:
                print(f"检测到 {len(tables)} 个表，准备删除...")
                for table in tables:
                    db.session.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                    print(f"  - 已删除表: {table}")
            
            db.session.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
            db.session.commit()
            print("✅ 旧数据清理完成")
        except Exception as e:
            print(f"⚠️ 清理部分旧表失败 (非致命): {e}")
            db.session.rollback()

        # 创建所有表
        db.create_all()
        print("✅ 所有数据库表创建成功！")



        
        # 1. 初始化角色
        roles = {
            'admin': {'name': '系统管理员', 'permissions': {'all': True}, 'desc': '拥有系统所有权限'},
            'manager': {'name': '部门主管', 'permissions': {'manage_dept': True, 'approve': True}, 'desc': '管理部门事务与审批'},
            'user': {'name': '普通员工', 'permissions': {'basic': True}, 'desc': '普通办公权限'}
        }
        
        created_roles = {}
        for code, info in roles.items():
            role = Role.query.filter_by(code=code).first()
            if not role:
                role = Role(name=info['name'], code=code, permissions=info['permissions'], description=info['desc'])
                db.session.add(role)
                print(f"➕ 创建角色: {info['name']}")
            created_roles[code] = role
        db.session.commit()

        # 2. 初始化部门
        depts = [
            {'name': '总经办', 'code': 'general', 'children': []},
            {'name': '研发中心', 'code': 'rd', 'children': ['后端开发组', '前端开发组', 'AI算法组']},
            {'name': '人力资源部', 'code': 'hr', 'children': ['招聘组', '薪酬组']},
            {'name': '财务部', 'code': 'finance', 'children': []}
        ]
        
        created_depts = {}
        for d in depts:
            dept = Department.query.filter_by(name=d['name']).first()
            if not dept:
                dept = Department(name=d['name'])
                db.session.add(dept)
                print(f"➕ 创建部门: {d['name']}")
                db.session.flush() # 获取ID
            created_depts[d['name']] = dept
            
            # 创建子部门
            for child_name in d['children']:
                child = Department.query.filter_by(name=child_name, parent_id=dept.id).first()
                if not child:
                    child = Department(name=child_name, parent_id=dept.id)
                    db.session.add(child)
                    print(f"  └─ 创建子部门: {child_name}")
        db.session.commit()

        # 3. 创建默认管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                department_id=created_depts['总经办'].id,
                role_id=created_roles['admin'].id
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("✅ 默认管理员用户创建成功: admin / admin")
        else:
            # 如果存在，尝试更新其角色和部门（如果是旧数据）
            if not admin.role_id or not admin.department_id:
                admin.role_id = created_roles['admin'].id
                admin.department_id = created_depts['总经办'].id
                db.session.commit()
                print("🔄 更新管理员用户的角色和部门信息")
            print("⚠️  管理员用户已存在")

if __name__ == '__main__':
    create_tables()
