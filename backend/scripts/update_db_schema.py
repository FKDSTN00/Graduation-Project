import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 1. 创建新表 SystemNotification
    # db.create_all() 会创建所有不存在的表
    db.create_all()
    print("Checked/Created tables.")

    # 2. 为 Schedule 表添加列
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE schedule ADD COLUMN remind_minutes INTEGER DEFAULT 0"))
            print("Added column 'remind_minutes' to schedule table.")
        except Exception as e:
            print(f"Column 'remind_minutes' might already exist in schedule: {e}")
            
        try:
            conn.execute(text("ALTER TABLE schedule ADD COLUMN is_notified BOOLEAN DEFAULT FALSE"))
            print("Added column 'is_notified' to schedule table.")
        except Exception as e:
            print(f"Column 'is_notified' might already exist in schedule: {e}")

    # 3. 为 Meeting 表添加列
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE meeting ADD COLUMN description TEXT"))
            print("Added column 'description' to meeting table.")
        except Exception as e:
            print(f"Column 'description' might already exist in meeting: {e}")

        try:
            conn.execute(text("ALTER TABLE meeting ADD COLUMN remind_minutes INTEGER DEFAULT 0"))
            print("Added column 'remind_minutes' to meeting table.")
        except Exception as e:
            print(f"Column 'remind_minutes' might already exist in meeting: {e}")
            
        try:
            conn.execute(text("ALTER TABLE meeting ADD COLUMN is_notified BOOLEAN DEFAULT FALSE"))
            print("Added column 'is_notified' to meeting table.")
        except Exception as e:
            print(f"Column 'is_notified' might already exist in meeting: {e}")

    # 4. 为 Notice 表添加列
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE notice ADD COLUMN level VARCHAR(20) DEFAULT 'normal'"))
            print("Added column 'level' to notice table.")
        except Exception as e:
            print(f"Column 'level' might already exist in notice: {e}")
    
    print("Database schema update completed.")
