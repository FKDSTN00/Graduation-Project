import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models.models import Document

def cleanup():
    app = create_app()
    with app.app_context():
        # 回收站文档保留7天后自动删除
        days = 7 
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # 查找回收站中超过7天的文档
        docs = Document.query.filter(
            Document.is_deleted == True,
            Document.deleted_at < cutoff
        ).all()
        
        count = len(docs)
        for doc in docs:
            db.session.delete(doc)
            
        db.session.commit()
        print(f"已清理 {count} 个超过 {days} 天的回收站文档。")

if __name__ == '__main__':
    cleanup()
