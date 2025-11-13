FROM python:3.11-slim

WORKDIR /app

# 安装依赖
RUN pip install feedparser requests

# 复制脚本
COPY linode-status-monitor.py /app/

# 创建缓存目录
RUN mkdir -p /app/cache

# 环境变量
ENV RSS_URL="https://status.linode.com/history.rss"
ENV CACHE_FILE="/app/cache/processed.json"

CMD ["python3", "linode-status-monitor.py"]

