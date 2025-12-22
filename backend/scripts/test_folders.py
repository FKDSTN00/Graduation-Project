#!/usr/bin/env python3
"""测试文件夹 API 是否正常工作"""

import requests
import json

BASE_URL = "http://localhost/api"

# 1. 登录获取 token
print("1. 登录...")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin"
})

if login_response.status_code != 200:
    print(f"❌ 登录失败: {login_response.text}")
    exit(1)

token = login_response.json()['access_token']
print(f"✅ 登录成功，获取 token")

headers = {
    "Authorization": f"Bearer {token}"
}

# 2. 获取普通空间文件夹
print("\n2. 获取普通空间文件夹...")
folders_response = requests.get(f"{BASE_URL}/docs/folders", headers=headers)

if folders_response.status_code != 200:
    print(f"❌ 获取文件夹失败: {folders_response.text}")
    exit(1)

folders = folders_response.json()
print(f"✅ 成功获取 {len(folders)} 个文件夹:")
for folder in folders:
    print(f"   - ID: {folder['id']}, 名称: {folder['name']}, 隐私空间: {folder.get('in_privacy_space', False)}")

# 3. 获取隐私空间文件夹
print("\n3. 获取隐私空间文件夹...")
privacy_folders_response = requests.get(
    f"{BASE_URL}/docs/folders",
    headers=headers,
    params={"in_privacy_space": "true"}
)

if privacy_folders_response.status_code != 200:
    print(f"❌ 获取隐私空间文件夹失败: {privacy_folders_response.text}")
else:
    privacy_folders = privacy_folders_response.json()
    print(f"✅ 成功获取 {len(privacy_folders)} 个隐私空间文件夹:")
    for folder in privacy_folders:
        print(f"   - ID: {folder['id']}, 名称: {folder['name']}, 隐私空间: {folder.get('in_privacy_space', False)}")

print("\n✅ 测试完成！")
