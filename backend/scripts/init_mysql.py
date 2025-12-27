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
    User, Document, RecycleBin, Schedule, Meeting,
    ApprovalFlow, Notice, Vote, KanbanList, KanbanCard, AISession, AIMessage, Task, FileCenterFolder, FileCenterFile, SystemNotification
)

def create_tables():
    """创建所有数据库表"""
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✅ 所有数据库表创建成功！")
        
        # 创建默认管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("✅ 默认管理员用户创建成功: admin / admin")
        else:
            print("⚠️  管理员用户已存在，跳过创建")

if __name__ == '__main__':
    create_tables()
