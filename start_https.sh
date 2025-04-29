#!/bin/bash
# 启动HTTPS服务器

# 停止任何可能已经运行的Python服务器
pkill -f "python.*http.server" || true
pkill -f "python.*main.py" || true
pkill -f "node.*server.js" || true

# 获取项目根目录的绝对路径
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "项目根目录: ${PROJECT_DIR}"

# 启动后端服务器（带SSL）
cd "${PROJECT_DIR}/server" && python3 ssl_main.py &
echo "已启动HTTPS后端服务器: https://localhost:8000"

# 给后端一点时间启动
sleep 2

# 启动前端HTTPS服务器
cd "${PROJECT_DIR}/client" && node server.js &
echo "已启动HTTPS前端服务器: https://localhost:8443"

# 显示本地IP，方便远程访问
LOCAL_IP=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n 1)
echo ""
echo "可通过以下地址远程访问："
echo "https://${LOCAL_IP}:8443"
echo ""
echo "注意：首次访问时会有安全警告，请点击'高级'然后选择'继续访问'" 