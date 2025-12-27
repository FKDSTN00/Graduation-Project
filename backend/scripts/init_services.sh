#!/bin/bash
# 服务初始化脚本
# 依次初始化 MySQL、Elasticsearch 和 MinIO
# 建议在 backend 容器内运行

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."  # 切换到 backend 根目录 (app 所在目录的父级)

echo "============================================================"
echo "🚀 开始初始化服务组件..."
echo "============================================================"

# 1. 初始化 MySQL (表结构 + 默认数据)
echo ""
echo ">>> [1/3] 初始化 MySQL..."
python3 scripts/init_mysql.py

# 2. 初始化 Elasticsearch (索引)
echo ""
echo ">>> [2/3] 初始化 Elasticsearch..."
python3 scripts/init_es.py

# 3. 初始化 MinIO (存储桶 + 策略)
echo ""
echo ">>> [3/3] 初始化 MinIO..."
python3 scripts/init_minio.py

echo ""
echo "============================================================"
echo "✅ 所有服务初始化完成！"
echo "============================================================"
