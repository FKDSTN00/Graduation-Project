
import sys
import os
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from sqlalchemy import text

def update_schema():
    app = create_app()
    with app.app_context():
        print("Checking schema updates...")
        
        # Check and add User.is_active
        try:
            db.session.execute(text("SELECT is_active FROM user LIMIT 1"))
            print(" - User.is_active already exists.")
        except Exception:
            print(" + Adding User.is_active column...")
            db.session.execute(text("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
            
        # Check and add Department.order
        try:
            db.session.execute(text("SELECT `order` FROM department LIMIT 1"))
            print(" - Department.order already exists.")
        except Exception:
            print(" + Adding Department.order column...")
            db.session.execute(text("ALTER TABLE department ADD COLUMN `order` INT DEFAULT 0"))
            
        db.session.commit()
        print("Schema update completed.")

if __name__ == '__main__':
    update_schema()
