#!/usr/bin/env python3
"""
手部监控系统 - HTTPS安全主服务器
"""
import os
import uvicorn
import ssl
import logging
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import subprocess
import shutil
from main import app, SHOTS_DIR, OUTPUT_DIR

# 自签名证书的路径
SSL_CERT_FILE = "../ssl/cert.pem"
SSL_KEY_FILE = "../ssl/key.pem"

# 设置 SSL 上下文
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(SSL_CERT_FILE, SSL_KEY_FILE)

# 创建日志记录器
logger = logging.getLogger("ssl_main")

# 挂载静态文件目录
# 已在main.py中挂载静态文件目录

# 包含图片管理API路由
# 已在main.py中定义了所有API路由，这里直接使用

# WebSocket 路由已在 main.py 中定义 

if __name__ == "__main__":
    # 带SSL启动服务器
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=SSL_KEY_FILE, ssl_certfile=SSL_CERT_FILE) 