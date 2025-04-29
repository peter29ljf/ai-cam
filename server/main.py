#!/usr/bin/env python3
"""
手部监控系统 - 主服务器
基于 FastAPI + WebSockets 的手部监控后端
"""
import os
import time
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any

import cv2
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# MediaPipe 手部检测
mp_hands = mp.solutions.hands

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="手部监控系统")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建截图目录
SHOTS_DIR = Path(__file__).parent / "shots"
SHOTS_DIR.mkdir(exist_ok=True)

# 挂载截图静态目录
app.mount("/shots", StaticFiles(directory=str(SHOTS_DIR)), name="shots")

# 包含图片管理 API 路由
from image_processing import router as image_router
app.include_router(image_router, prefix="/api")

# 创建手部检测器
class HandDetector:
    def __init__(self, 
                 max_num_hands=1, 
                 min_detection_confidence=0.5, 
                 min_tracking_confidence=0.5):
        self.hands = mp_hands.Hands(
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            static_image_mode=False
        )
        
    def detect(self, image):
        # 处理图像
        results = self.hands.process(image)
        
        # 检查是否有手部关键点
        return bool(results.multi_hand_landmarks)

# 初始化手部检测器
hand_detector = HandDetector()

# 管理连接的客户端
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"客户端连接，当前连接数：{len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"客户端断开，当前连接数：{len(self.active_connections)}")

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# 路由
@app.get("/")
async def root():
    return {"message": "手部监控系统 API 服务"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # 状态机状态
    state = 0  # 0: WAIT_HAND, 1: HAND_ON
    count = 0
    
    try:
        while True:
            # 接收前端发送的图像帧
            data = await websocket.receive_bytes()
            
            # 转换为图像并处理
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            
            # 检测手部
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            has_hand = hand_detector.detect(frame_rgb)
            
            # 状态机逻辑
            if state == 0 and has_hand:
                state = 1
                await manager.send_message("手势已检测", websocket)
            elif state == 1 and not has_hand:
                # 延时0.5秒，确保手真的离开
                await websocket.send_text("手部消失，准备截图...")
                time.sleep(0.5)
                
                # 请求高清截图
                await websocket.send_text("请发送高清截图")
                
                # 等待高清截图
                hd_data = await websocket.receive_bytes()
                hd_frame = cv2.imdecode(np.frombuffer(hd_data, np.uint8), cv2.IMREAD_COLOR)
                
                # 截图保存
                count += 1
                shot_path = SHOTS_DIR / f'shot_{count}.png'
                cv2.imwrite(str(shot_path), hd_frame)
                
                # 发送成功消息给前端
                await manager.send_message(f"截图成功：{shot_path}", websocket)
                
                # 重置状态
                state = 0
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    
    except Exception as e:
        logger.error(f"WebSocket处理错误: {str(e)}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 