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
    remind_minutes = db.Column(db.Integer, default=0, comment='提前通知时间(分钟)，0表示不通知')
    is_notified = db.Column(db.Boolean, default=False, comment='是否已通知')
    
    user = db.relationship('User', backref='schedules')

class Meeting(db.Model):
    """会议"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='会议主题')
    start_time = db.Column(db.DateTime, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=False, comment='结束时间')
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='组织者ID')
    attendees = db.Column(db.JSON, comment='参会人员ID列表') 
    meeting_link = db.Column(db.String(255), comment='会议链接')
    description = db.Column(db.Text, comment='会议描述')
    remind_minutes = db.Column(db.Integer, default=0, comment='提前通知时间(分钟)，0表示不通知')
    is_notified = db.Column(db.Boolean, default=False, comment='是否已通知')
    
    organizer = db.relationship('User', backref='organized_meetings')

class SystemNotification(db.Model):
    """系统通知（针对个人的通知）"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='接收用户ID')
    title = db.Column(db.String(255), nullable=False, comment='通知标题')
    content = db.Column(db.Text, nullable=False, comment='通知内容')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    type = db.Column(db.String(50), default='system', comment='通知类型')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

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

    applicant = db.relationship('User', backref='approval_flows')

class Notice(db.Model):
    """公告"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='公告标题')
    content = db.Column(db.Text, nullable=False, comment='公告内容')
    level = db.Column(db.String(20), default='normal', comment='等级: normal/important')
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='发布人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='发布时间')

    author = db.relationship('User', backref='notices')

class Vote(db.Model):
    """投票/问卷"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='投票标题')
    options = db.Column(db.JSON, comment='选项列表') # [{"key": "opt1", "label": "选项1"}, ...]
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='创建人ID')
    end_time = db.Column(db.DateTime, comment='截止时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

    records = db.relationship('VoteRecord', backref='vote', lazy='dynamic', cascade='all, delete-orphan')

class VoteRecord(db.Model):
    """投票记录"""
    id = db.Column(db.Integer, primary_key=True)
    vote_id = db.Column(db.Integer, db.ForeignKey('vote.id'), nullable=False, comment='投票ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    option_key = db.Column(db.String(50), nullable=False, comment='选项标识')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='投票时间')

class Feedback(db.Model):
    """留言/反馈帖子"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, comment='标题')
    content = db.Column(db.Text, nullable=False, comment='内容')
    category = db.Column(db.String(50), default='message', comment='分类: bug/suggestion/message')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='发帖人ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    view_count = db.Column(db.Integer, default=0, comment='浏览量')

    user = db.relationship('User', backref='feedbacks')
    replies = db.relationship('FeedbackReply', backref='feedback', lazy='dynamic', cascade='all, delete-orphan')

class FeedbackReply(db.Model):
    """留言/反馈回复"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False, comment='回复内容')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='回复人ID')
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedback.id'), nullable=False, comment='所属帖子ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='回复时间')

    user = db.relationship('User', backref='feedback_replies')

class FeedbackLike(db.Model):
    """帖子点赞"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback_id = db.Column(db.Integer, db.ForeignKey('feedback.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FeedbackReplyLike(db.Model):
    """回复点赞"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reply_id = db.Column(db.Integer, db.ForeignKey('feedback_reply.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MonitorKeyword(db.Model):
    """管理员监控关键词"""
    __tablename__ = 'monitor_keyword'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False, unique=True, comment='监控关键词')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')

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

class AISession(db.Model):
    """AI 会话"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    title = db.Column(db.String(255), comment='会话标题')
    is_pinned = db.Column(db.Boolean, default=False, comment='是否置顶')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    user = db.relationship('User', backref=db.backref('ai_sessions', lazy='dynamic', cascade='all, delete-orphan'))
    messages = db.relationship('AIMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan')

class AIMessage(db.Model):
    """AI 消息"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('ai_session.id'), nullable=False, comment='会话ID')
    role = db.Column(db.String(20), nullable=False, comment='角色: user/assistant')
    content = db.Column(db.Text, nullable=False, comment='内容')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='时间')

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
