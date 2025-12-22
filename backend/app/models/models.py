from datetime import datetime
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment='用户名')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='邮箱')
    password_hash = db.Column(db.String(255), comment='密码哈希')
    department = db.Column(db.String(64), comment='部门')
    role = db.Column(db.String(20), default='user', comment='角色: user/admin')
    avatar = db.Column(db.String(500), comment='头像URL')
    privacy_password_hash = db.Column(db.String(255), comment='隐私空间密码哈希')

    def set_password(self, password):
        """设置密码（生成哈希）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def set_privacy_password(self, password):
        """设置隐私空间密码（生成哈希）"""
        self.privacy_password_hash = generate_password_hash(password)

    def check_privacy_password(self, password):
        """验证隐私空间密码"""
        if not self.privacy_password_hash:
            return False
        return check_password_hash(self.privacy_password_hash, password)

class Folder(db.Model):
    """文档文件夹"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='文件夹名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('folder.id'), comment='父文件夹ID')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建者ID')
    order = db.Column(db.Integer, default=0, comment='排序')
    in_privacy_space = db.Column(db.Boolean, default=False, comment='是否在隐私空间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]))

class Document(db.Model):
    """文档模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='文档标题')
    content = db.Column(db.Text, comment='文档内容')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建者ID')
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), comment='所属文件夹ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否已删除')
    deleted_at = db.Column(db.DateTime, comment='删除时间')
    is_private = db.Column(db.Boolean, default=False, comment='是否私有')
    in_privacy_space = db.Column(db.Boolean, default=False, comment='是否在隐私空间')
    is_pinned = db.Column(db.Boolean, default=False, comment='是否置顶')
    password = db.Column(db.String(128), comment='访问密码（私有文档）') 
    version = db.Column(db.Integer, default=1, comment='版本号')
    attachments = db.Column(db.JSON, comment='附件列表（图片、视频、文件URL）')
    
    owner = db.relationship('User', backref='documents')
    folder = db.relationship('Folder', backref='documents')

class Tag(db.Model):
    """文档标签"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='标签名称')
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False, comment='关联文档ID')

class RecycleBin(db.Model):
    """回收站"""
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False, comment='文档ID')
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow, comment='删除时间')

class Schedule(db.Model):
    """个人日程"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='日程标题')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=False, comment='结束时间')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    description = db.Column(db.Text, comment='描述')

class Meeting(db.Model):
    """会议"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='会议主题')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=False, comment='结束时间')
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='组织者ID')
    attendees = db.Column(db.JSON, comment='参会人员ID列表') 
    meeting_link = db.Column(db.String(255), comment='会议链接')

class ApprovalFlow(db.Model):
    """审批流程"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='申请标题')
    applicant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='申请人ID')
    type = db.Column(db.String(50), comment='类型: leave(请假)/reimbursement(报销)/procurement(采购)')
    status = db.Column(db.String(20), default='pending', comment='状态: pending/approved/rejected')
    current_step = db.Column(db.Integer, default=1, comment='当前审批步骤')
    total_steps = db.Column(db.Integer, default=1, comment='总步骤数')
    details = db.Column(db.JSON, comment='申请详情数据')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='申请时间')

class Notice(db.Model):
    """公告"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='公告标题')
    content = db.Column(db.Text, nullable=False, comment='公告内容')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='发布人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='发布时间')

class Vote(db.Model):
    """投票/问卷"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='投票标题')
    options = db.Column(db.JSON, comment='选项列表')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建人ID')
    end_time = db.Column(db.DateTime, comment='截止时间')

class KanbanList(db.Model):
    """看板列"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, comment='列标题')
    order = db.Column(db.Integer, default=0, comment='排序')

class KanbanCard(db.Model):
    """看板卡片"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='卡片标题')
    content = db.Column(db.Text, comment='卡片内容')
    list_id = db.Column(db.Integer, db.ForeignKey('kanban_list.id'), nullable=False, comment='所属列ID')
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='负责人ID')
    order = db.Column(db.Integer, default=0, comment='排序')

class AIQueryLog(db.Model):
    """AI 问答日志"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    query = db.Column(db.Text, nullable=False, comment='提问内容')
    response = db.Column(db.Text, comment='AI回复')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, comment='时间')

class Task(db.Model):
    """任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='任务标题')
    priority = db.Column(db.String(20), default='Medium', comment='优先级: High/Medium/Low')
    deadline = db.Column(db.DateTime, comment='截止时间')
    status = db.Column(db.String(20), default='pending', comment='状态: pending/in-progress/completed')
    notes = db.Column(db.Text, comment='备注')
    related_docs = db.Column(db.JSON, comment='关联文档ID列表')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    user = db.relationship('User', backref=db.backref('tasks', lazy='dynamic'))

class KnowledgeCategory(db.Model):
    """知识库分类"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, comment='分类名称')
    order = db.Column(db.Integer, default=0, comment='排序')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    articles = db.relationship('KnowledgeArticle', backref='category', lazy='dynamic', cascade='all, delete-orphan')

class KnowledgeArticle(db.Model):
    """知识库文章"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='文章标题')
    content = db.Column(db.Text, comment='文章内容')
    category_id = db.Column(db.Integer, db.ForeignKey('knowledge_category.id'), comment='分类ID')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='作者ID（管理员）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    author = db.relationship('User', backref='knowledge_articles')

class FileCenterFolder(db.Model):
    """文件中心文件夹"""
    __tablename__ = 'file_center_folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='文件夹名称')
    parent_id = db.Column(db.Integer, db.ForeignKey('file_center_folder.id'), nullable=True, comment='父文件夹ID')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建者ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    creator = db.relationship('User', backref='created_fc_folders')
    parent = db.relationship('FileCenterFolder', remote_side=[id], backref=db.backref('subfolders', lazy='dynamic'))

class FileCenterFile(db.Model):
    """文件中心文件"""
    __tablename__ = 'file_center_file'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, comment='文件名')
    path = db.Column(db.String(500), nullable=False, comment='文件存储路径')
    size = db.Column(db.Integer, comment='文件大小(字节)')
    type = db.Column(db.String(50), comment='文件类型')
    folder_id = db.Column(db.Integer, db.ForeignKey('file_center_folder.id'), nullable=True, comment='所属文件夹ID')
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='上传者ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='上传时间')
    
    uploader = db.relationship('User', backref='uploaded_fc_files')
    folder = db.relationship('FileCenterFolder', backref=db.backref('files', lazy='dynamic', cascade='all, delete-orphan'))
