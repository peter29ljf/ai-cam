#!/usr/bin/env python3
"""
手部监控系统 - HTTPS安全主服务器
"""
import os
import uvicorn
import ssl
from main import app  # 导入原有的FastAPI应用

# 自签名证书的路径
SSL_CERT_FILE = "../ssl/cert.pem"
SSL_KEY_FILE = "../ssl/key.pem"

# 设置SSL上下文
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(SSL_CERT_FILE, SSL_KEY_FILE)

if __name__ == "__main__":
    # 带SSL启动服务器
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        ssl_keyfile=SSL_KEY_FILE,
        ssl_certfile=SSL_CERT_FILE
    ) 