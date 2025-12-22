# 企业知识协同与业务管理平台

基于 Vue 3 + Flask 的企业知识协同平台，内置 AI 智能助手（DeepSeek-R1）。

## 技术栈

### 前端
- Vue 3 + Vite
- Pinia (状态管理)
- Vue Router
- Element Plus (UI 组件库)
- Axios

### 后端
- Flask
- SQLAlchemy (ORM)
- Flask-JWT-Extended (认证)
- Flask-SocketIO (WebSocket)
- Gunicorn (WSGI 服务器)

### 基础设施
- MySQL (数据库)
- Elasticsearch (全文搜索)
- Redis (缓存)
- MinIO (对象存储)
- Nginx (反向代理)
- DeepSeek-R1 (AI 模型，通过 Ollama 运行)

## 功能模块

1. **文档管理** - 文档创建/编辑/删除、全文检索、标签分类、版本控制
2. **日程会议** - 个人日程、团队会议、实时提醒
3. **审批流程** - 请假/报销/采购审批、多级审批
4. **公告投票** - 公告发布、投票、问卷
5. **工作看板** - Trello 风格看板、任务管理
6. **AI 助手** - 文档问答、会议纪要生成、审批建议

## 快速开始

### 前置要求

- Docker & Docker Compose

### 使用 Docker Compose 启动（推荐）

```bash
# 进入项目目录
cd docker

# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# [重要] 首次启动后需要下载模型
docker compose exec ollama ollama pull deepseek-r1:1.5b
```

服务访问地址：
- 前端: http://localhost
- 后端 API: http://localhost/api
- MinIO 控制台: http://localhost:9001
- Elasticsearch: http://localhost:9200

### 本地开发 (可选)

如果您希望在本地运行代码而不是 Docker 容器中，您仍然需要安装 Python 和 Node.js。但推荐使用 Docker Compose 进行开发和部署。

### 初始化服务

```bash
# 初始化 Elasticsearch 索引
docker compose exec backend python scripts/init_es.py

# 初始化 MinIO 存储桶
docker compose exec backend python scripts/init_minio.py

# 创建数据库表和默认管理员
docker compose exec backend python scripts/create_tables.py
```

## 默认账号

- **系统管理员**: `admin` / `admin`
- **Elasticsearch**: `elastic` / `elastic`
- **MinIO**: `minioadmin` / `minioadmin`

## 项目结构

```
├── backend/              # Flask 后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models/       # 数据模型
│   │   ├── auth/         # 认证模块
│   │   ├── docs/         # 文档管理
│   │   ├── schedule/     # 日程会议
│   │   ├── approval/     # 审批流程
│   │   ├── notice/       # 公告投票
│   │   ├── kanban/       # 工作看板
│   │   └── ai/           # AI 助手
│   ├── scripts/          # 初始化脚本
│   │   ├── create_tables.py
│   │   ├── init_es.py
│   │   └── init_minio.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # Vue 前端
│   ├── src/
│   │   ├── api/          # API 封装
│   │   ├── views/        # 页面
│   │   ├── components/   # 组件
│   │   ├── store/        # 状态管理
│   │   └── router/       # 路由
│   ├── package.json
│   └── Dockerfile
├── docker/               # Docker 配置
│   ├── docker-compose.yml
│   └── nginx.conf
```

## 开发说明

### API 接口

所有 API 接口以 `/api` 为前缀：

- `/api/auth/login` - 登录
- `/api/auth/register` - 注册
- `/api/docs/` - 文档管理
- `/api/schedule/` - 日程管理
- `/api/approval/` - 审批管理
- `/api/notice/` - 公告管理
- `/api/kanban/` - 看板管理
- `/api/ai/chat` - AI 对话

### 环境变量

在 `docker-compose.yml` 中配置：

```yaml
DATABASE_URL=mysql+pymysql://user:user@mysql/db
ELASTICSEARCH_URL=http://elasticsearch:9200
MINIO_ENDPOINT=minio:9000
AI_API_URL=http://ollama:11434/v1
AI_MODEL_NAME=deepseek-r1:1.5b
```

## TODO

- [ ] 完善 Elasticsearch 全文搜索
- [ ] 实现 MinIO 文件上传
- [ ] WebSocket 实时通知
- [x] AI 模型替换为 DeepSeek-R1 (Ollama)
- [ ] 单元测试
- [ ] 生产环境部署配置

## 许可证

MIT License
