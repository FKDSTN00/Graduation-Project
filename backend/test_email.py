#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试邮件发送配置"""

import os
import sys

# 设置环境变量（模拟docker-compose中的配置）
os.environ['MAIL_SERVER'] = 'smtp.qq.com'
os.environ['MAIL_PORT'] = '465'
os.environ['MAIL_USE_SSL'] = 'True'
os.environ['MAIL_USERNAME'] = '1925396019@qq.com'
os.environ['MAIL_PASSWORD'] = 'swudjtuembbrchdf'
os.environ['MAIL_DEFAULT_SENDER'] = '1925396019@qq.com'

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'True') in ['True', 'true', '1', 'yes']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

print("邮件配置：")
print(f"  MAIL_SERVER: {app.config['MAIL_SERVER']}")
print(f"  MAIL_PORT: {app.config['MAIL_PORT']}")
print(f"  MAIL_USE_SSL: {app.config['MAIL_USE_SSL']}")
print(f"  MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"  MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")

mail = Mail(app)

try:
    with app.app_context():
        msg = Message(
            "测试邮件",
            recipients=['1925396019@qq.com'],  # 发给自己测试
            body="这是一封测试邮件，用于验证邮件配置是否正确。"
        )
        mail.send(msg)
        print("\n✅ 邮件发送成功！")
except Exception as e:
    print(f"\n❌ 邮件发送失败: {str(e)}")
    import traceback
    traceback.print_exc()
