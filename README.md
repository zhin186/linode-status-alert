DOCKER_USER="zhin186"
IMAGE_TAG="v2.0-stable"  # 使用语义化版本

docker build -t ${DOCKER_USER}/linode-status-monitor:${IMAGE_TAG} .
docker push ${DOCKER_USER}/linode-status-monitor:${IMAGE_TAG}

# 可选：验证镜像
docker run --rm -it \
  -e RSS_URL="https://status.linode.com/history.rss" \
  -e WEBHOOK_URL="test" \
  ${DOCKER_USER}/linode-status-monitor:${IMAGE_TAG}
