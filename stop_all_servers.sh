#!/bin/bash
# 关闭所有相关服务器进程

# 优雅杀掉已知进程
pkill -f "uvicorn" || true
pkill -f "python.*main.py" || true
pkill -f "python.*ssl_main.py" || true
pkill -f "python.*http.server" || true
pkill -f "node.*server.js" || true

# 强制杀掉占用端口8000和8443的进程
for port in 8000 8443; do
  pids=$(lsof -ti tcp:$port)
  if [ -n "$pids" ]; then
    echo "检测到占用端口 $port 的进程: $pids，正在杀掉..."
    kill -9 $pids || true
  fi
done

echo "所有相关服务器进程已关闭。" 