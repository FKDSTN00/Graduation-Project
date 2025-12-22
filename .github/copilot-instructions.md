## 快速说明（供 AI 代码代理使用）

本仓库是一个基于 Vue 3 (Vite) + Flask 的企业协同平台，包含 AI 助手（通过 Ollama 运行 DeepSeek-R1）。下面的内容帮助你快速定位修改点和常见约定，避免通用但与本项目无关的建议。

### 大体架构（必读）
- 后端：`backend/`（Flask 应用）。入口工厂在 `backend/app/__init__.py`，各功能通过 Blueprint 划分并注册到 `/api/<module>`。
  - 示例：`app.register_blueprint(ai_bp, url_prefix='/api/ai')`。
- 前端：`frontend/`（Vite + Vue 3），axios 基址由 `frontend/src/api/request.js` 控制，默认为 `/api`（见 `baseURL`）。
- 基础设施：通过 `docker/docker-compose.yml` 启动多个服务（mysql、elasticsearch、minio、redis、ollama、nginx、frontend、backend）。Nginx 在 `docker/nginx.conf` 中将 `/api` 和 `/socket.io` 反向代理到后端。

### 启动 / 调试（最常用命令）
- 推荐：使用 Docker Compose（项目 README 中已有）：
  - `cd docker` 然后 `docker compose up -d`
  - 首次启动后需在 ollama 容器拉模型：`docker compose exec ollama ollama pull deepseek-r1:1.5b`
- 后端快速命令（容器内）：
  - 初始化 ES：`docker compose exec backend python scripts/init_es.py`
  - 创建 DB 表：`docker compose exec backend python scripts/create_tables.py`
- 本地前端开发：在 `frontend/` 下使用 `npm/yarn`：`npm run dev`（Vite，默认端口 5173）。但 Docker Compose 默认也以开发卷挂载源码；可直接在容器中热重载。

### 项目约定与关键点（容易出错的地方）
- 所有后端 API 都以 `/api` 前缀暴露（参考 `backend/app/__init__.py` 和 `docker/nginx.conf`）。
- 前端 token 流程：token 存在 `localStorage`（键为 `token`），axios 自动在请求头 `Authorization: Bearer <token>` 中注入（见 `frontend/src/api/request.js`），遇 401 会清理 token 并重定向登录页。
- SocketIO 路径为 `/socket.io`，Nginx 已做代理（参见 `docker/nginx.conf`）。实现新的实时功能时确保后端的 socket 命名与前端一致。
- 后端配置集中在 `backend/app/config.py`，关键环境变量名称：`DATABASE_URL`, `ELASTICSEARCH_URL`, `MINIO_ENDPOINT`, `AI_API_URL`, `AI_MODEL_NAME`, `REDIS_URL`。
- 后端扩展与全局资源：`backend/app/extensions.py`（请查看该文件以使用 db/jwt/socketio/migrate/cors），Redis 客户端会通过 `extensions.redis_client` 赋值（在 `app/__init__.py` 中初始化）。

### 如何添加新后端 API（示例流程）
1. 在 `backend/app/<module>/routes.py` 中实现蓝图对象，例如 `ai_bp`。
2. 在 `backend/app/__init__.py` 导入并注册蓝图（保持 `url_prefix='/api/<module>'` 风格）。
3. 如果需要 DB 模型，在 `backend/app/models/models.py` 中添加并迁移（使用 `scripts/create_tables.py` 或 flask-migrate）。

### 与 AI/模型相关的集成点
- Ollama 容器名为 `ollama`，API 暴露在 `11434` 端口（参见 `docker-compose.yml` 和 `backend/app/config.py` 中的 `AI_API_URL`）。
- 模型名称在 `AI_MODEL_NAME` 配置中指定（默认 `deepseek-r1:1.5b`），请在修改模型或参数前先在 README 中查找拉取命令。

### 依赖与构建文件
- 后端依赖：`backend/requirements.txt`（Flask、SQLAlchemy、elasticsearch、minio 等）。
- 前端依赖：`frontend/package.json`（Vite、Vue、Element Plus、Pinia、axios）。

### 代码风格 / 小约定（可自动化检测时参考）
- 后端使用蓝图模块化；新增模块请跟现有模块同目录布局（`routes.py`、若有 `services/` 则放在模块目录下）。
- API 返回约定：前端 `request` 拦截器默认 `response.data` 被直接返回，后端应把有用的数据放在响应 JSON 的根对象中以便直接消费。

### 变更/PR 指导（给 AI 的具体建议）
- 当修改 API 路由时，一并更新 `frontend/src/api` 中调用该路由的代码（搜索 `/api/<module>`）。
- 修改后端配置或新增环境变量，请同时更新 `docker/docker-compose.yml` 和 `backend/app/config.py` 的默认值示例。

如果有任何具体区域需要更详细的示例（例如如何新增一个 AI intent endpoint，或如何在本地调试 Ollama），告诉我你想要的焦点，我会把该部分扩展为 1-2 个可运行示例。请审阅这份草稿并指出哪些部分需要补充或调整。
