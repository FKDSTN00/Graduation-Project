import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from sqlalchemy import text

def update_schema():
    app = create_app()
    with app.app_context():
        print("开始更新数据库结构...")
        
        # 1. 创建 Folder 表
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS folder (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(50) NOT NULL COMMENT '文件夹名称',
                parent_id INTEGER COMMENT '父文件夹ID',
                owner_id INTEGER NOT NULL COMMENT '创建者ID',
                created_at DATETIME COMMENT '创建时间',
                FOREIGN KEY (parent_id) REFERENCES folder(id),
                FOREIGN KEY (owner_id) REFERENCES user(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            db.session.execute(text(sql))
            print("✅ 已创建 folder 表")
        except Exception as e:
            print(f"⚠️  创建 folder 表失败: {e}")

        # 2. 为 Document 表添加字段
        columns_to_add = [
            ("folder_id", "INTEGER COMMENT '所属文件夹ID'"),
            ("is_pinned", "BOOLEAN DEFAULT FALSE COMMENT '是否置顶'"),
            ("deleted_at", "DATETIME COMMENT '删除时间'"),
            ("in_privacy_space", "BOOLEAN DEFAULT FALSE COMMENT '是否在隐私空间'")
        ]
        
        for col_name, col_def in columns_to_add:
            try:
                sql = f"ALTER TABLE document ADD COLUMN {col_name} {col_def}"
                db.session.execute(text(sql))
                print(f"✅ 已添加字段 {col_name} 到 document 表")
            except Exception as e:
                if "Duplicate column name" in str(e) or "1060" in str(e):
                    print(f"ℹ️  字段 {col_name} 已存在")
                else:
                    print(f"⚠️  添加字段 {col_name} 失败: {e}")
        
        # 为 folder_id 添加外键
        try:
            sql = "ALTER TABLE document ADD CONSTRAINT fk_document_folder FOREIGN KEY (folder_id) REFERENCES folder(id)"
            db.session.execute(text(sql))
            print("✅ 已为 folder_id 添加外键约束")
        except Exception as e:
            if "Duplicate key" in str(e) or "1061" in str(e) or "1215" in str(e):
                 print(f"ℹ️  folder_id 的外键可能已存在或添加失败: {e}")
            else:
                 print(f"⚠️  添加 folder_id 外键失败: {e}")

        # 3. 为 Folder 表添加 order 字段
        try:
            sql = "ALTER TABLE folder ADD COLUMN `order` INTEGER DEFAULT 0 COMMENT '排序'"
            db.session.execute(text(sql))
            print("✅ 已添加 order 字段到 folder 表")
        except Exception as e:
            if "Duplicate column name" in str(e) or "1060" in str(e):
                print("ℹ️  folder 表中已存在 order 字段")
            else:
                print(f"⚠️  添加 order 字段到 folder 表失败: {e}")

        # 4. 为 User 表添加 avatar 字段
        try:
            sql = "ALTER TABLE user ADD COLUMN avatar VARCHAR(500) COMMENT '头像URL'"
            db.session.execute(text(sql))
            print("✅ 已添加 avatar 字段到 user 表")
        except Exception as e:
            if "Duplicate column name" in str(e) or "1060" in str(e):
                print("ℹ️  user 表中已存在 avatar 字段")
            else:
                print(f"⚠️  添加 avatar 字段到 user 表失败: {e}")

        # 5. 为 User 表添加 privacy_password_hash 字段
        try:
            sql = "ALTER TABLE user ADD COLUMN privacy_password_hash VARCHAR(255) COMMENT '隐私空间密码哈希'"
            db.session.execute(text(sql))
            print("✅ 已添加 privacy_password_hash 字段到 user 表")
        except Exception as e:
            if "Duplicate column name" in str(e) or "1060" in str(e):
                print("ℹ️  user 表中已存在 privacy_password_hash 字段")
            else:
                print(f"⚠️  添加 privacy_password_hash 字段到 user 表失败: {e}")

        # 6. 为 Document 表添加 attachments 字段
        try:
            sql = "ALTER TABLE document ADD COLUMN attachments JSON COMMENT '附件列表（图片、视频、文件URL）'"
            db.session.execute(text(sql))
            print("✅ 已添加 attachments 字段到 document 表")
        except Exception as e:
            if "Duplicate column name" in str(e) or "1060" in str(e):
                print("ℹ️  document 表中已存在 attachments 字段")
            else:
                print(f"⚠️  添加 attachments 字段到 document 表失败: {e}")

        # 6. 为 Folder 表添加 in_privacy_space 字段
        try:
            sql = "ALTER TABLE folder ADD COLUMN in_privacy_space BOOLEAN DEFAULT FALSE COMMENT '是否在隐私空间'"
            db.session.execute(text(sql))
            print("✅ 已添加 in_privacy_space 字段到 folder 表")
        except Exception as e:
            if "Duplicate column name" in str(e) or "1060" in str(e):
                print("ℹ️  folder 表中已存在 in_privacy_space 字段")
            else:
                print(f"⚠️  添加 in_privacy_space 字段到 folder 表失败: {e}")

        # 7. 更新现有文件夹的 in_privacy_space 字段为 FALSE
        try:
            sql = "UPDATE folder SET in_privacy_space = FALSE WHERE in_privacy_space IS NULL"
            result = db.session.execute(text(sql))
            print(f"✅ 已更新 {result.rowcount} 个文件夹的 in_privacy_space 字段为 FALSE")
        except Exception as e:
            print(f"⚠️  更新文件夹 in_privacy_space 字段失败: {e}")

        db.session.commit()
        print("数据库结构更新完成。")

if __name__ == '__main__':
    update_schema()
