#!/usr/bin/env python3
"""测试文件中心 API"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app import create_app
from app.extensions import db
from app.models.models import User
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    # 获取管理员用户
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print("❌ 管理员用户不存在")
        sys.exit(1)
    
    # 创建测试 token
    token = create_access_token(identity=admin.id)
    print(f"✅ Token: {token[:50]}...")
    
    # 测试客户端
    with app.test_client() as client:
        # 测试文件列表 API
        response = client.get(
            '/api/files/list',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {response.get_json()}")
        
        if response.status_code != 200:
            print(f"\n❌ API 调用失败")
            print(f"错误详情: {response.data.decode('utf-8')}")
        else:
            print(f"\n✅ API 调用成功")
