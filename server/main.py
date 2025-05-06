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
import json

import cv2
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import subprocess
import shutil

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
SHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
# 设置输出目录路径
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

# 确保目录存在
os.makedirs(SHOTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 挂载截图静态目录
app.mount("/shots", StaticFiles(directory=SHOTS_DIR), name="shots")

# 包含图片管理 API 路由
from image_processing import router as image_router
app.include_router(image_router, prefix="/api")

# 导入设置API路由
from settings_api import router as settings_router
app.include_router(settings_router, prefix="/api")

# 导入智谱API路由
if os.path.exists(os.path.join(os.path.dirname(__file__), "zhipu_api.py")):
    from zhipu_api import setup_zhipu_api
    setup_zhipu_api(app)
    logger.info("智谱API路由已加载")

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
                # 延时2秒，确保手真的离开
                await websocket.send_text("手部消失，准备截图...")
                time.sleep(2.0)
                
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

# 获取 output 目录下的文件夹列表
@app.get("/api/output-folders")
async def get_output_folders():
    """获取输出目录下的所有文件夹"""
    try:
        # 确保输出目录存在
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 获取所有文件夹列表（不包括文件）
        folders = [name for name in os.listdir(OUTPUT_DIR) 
                  if os.path.isdir(os.path.join(OUTPUT_DIR, name)) and not name.startswith('.')]
        
        return folders
    except Exception as e:
        logger.error(f"获取输出文件夹列表出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件夹列表失败: {str(e)}")

# 删除指定的 output 文件夹
@app.delete("/api/output-folders/{folder_name}")
async def delete_output_folder(folder_name: str):
    """删除指定的输出文件夹及其内容"""
    try:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        
        # 安全检查：确保路径在 OUTPUT_DIR 内
        if not os.path.abspath(folder_path).startswith(os.path.abspath(OUTPUT_DIR)):
            raise HTTPException(status_code=403, detail="路径安全检查失败")
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise HTTPException(status_code=404, detail=f"文件夹 '{folder_name}' 不存在")
        
        # 删除文件夹及其所有内容
        shutil.rmtree(folder_path)
        
        return {"success": True, "message": f"文件夹 '{folder_name}' 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件夹出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件夹失败: {str(e)}")

# 执行 process_images.py 脚本
@app.post("/api/process-images")
async def process_images(mode: str = "extract"):
    """
    执行图片处理脚本
    
    参数:
    - mode: 操作模式，可选值为 "extract"(提取文字) 或 "summary"(生成文档)
    """
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "process_images.py")
        
        # 检查脚本文件是否存在
        if not os.path.exists(script_path):
            raise HTTPException(status_code=404, detail="处理脚本文件不存在")
        
        # 检查模式参数
        if mode not in ["extract", "summary"]:
            raise HTTPException(status_code=400, detail=f"无效的模式: {mode}，可选值为 extract 或 summary")
        
        # 执行脚本，传递模式参数
        result = subprocess.run(["python3", script_path, f"--mode={mode}"], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        
        # 检查执行结果
        if result.returncode == 0:
            # 脚本执行成功
            if mode == "extract":
                message = "文字提取成功"
            else:
                message = "文档生成成功"
                
            return {
                "success": True, 
                "message": message,
                "mode": mode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            # 脚本执行失败
            return {
                "success": False,
                "message": f"处理失败，退出代码: {result.returncode}",
                "mode": mode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
    except subprocess.SubprocessError as e:
        logger.error(f"脚本执行错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"脚本执行错误: {str(e)}")
    except Exception as e:
        logger.error(f"处理图片出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理图片失败: {str(e)}")

@app.get("/api/folder-content/{folder_name}")
async def get_folder_content(folder_name: str):
    """获取指定文件夹中的Markdown文件内容和对话历史"""
    try:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        
        # 安全检查：确保路径在 OUTPUT_DIR 内
        if not os.path.abspath(folder_path).startswith(os.path.abspath(OUTPUT_DIR)):
            raise HTTPException(status_code=403, detail="路径安全检查失败")
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise HTTPException(status_code=404, detail=f"文件夹 '{folder_name}' 不存在")
        
        # 查找 Markdown 文件
        md_content = ""
        for file in os.listdir(folder_path):
            if file.endswith('.md'):
                md_file_path = os.path.join(folder_path, file)
                try:
                    with open(md_file_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    break  # 找到第一个 Markdown 文件即停止
                except Exception as e:
                    logger.error(f"读取Markdown文件出错: {str(e)}")
        
        # 查找或创建 conversation_history.json 文件
        history_file_path = os.path.join(folder_path, 'conversation_history.json')
        conversation_history = []
        
        if os.path.exists(history_file_path):
            try:
                with open(history_file_path, 'r', encoding='utf-8') as f:
                    conversation_history = json.load(f)
            except Exception as e:
                logger.error(f"读取对话历史文件出错: {str(e)}")
        
        return {
            "document_content": md_content,
            "conversation_history": conversation_history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件夹内容出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件夹内容失败: {str(e)}")

@app.post("/api/update-conversation/{folder_name}")
async def update_conversation(folder_name: str, data: dict):
    """更新指定文件夹中的对话历史"""
    try:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        
        # 安全检查：确保路径在 OUTPUT_DIR 内
        if not os.path.abspath(folder_path).startswith(os.path.abspath(OUTPUT_DIR)):
            raise HTTPException(status_code=403, detail="路径安全检查失败")
        
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise HTTPException(status_code=404, detail=f"文件夹 '{folder_name}' 不存在")
        
        # 获取用户输入和AI响应
        user_input = data.get("user_input")
        ai_response = data.get("ai_response")
        
        if not user_input or not ai_response:
            raise HTTPException(status_code=400, detail="缺少必要的对话内容")
        
        # 更新对话历史
        history_file_path = os.path.join(folder_path, 'conversation_history.json')
        conversation_history = []
        
        # 如果文件存在，先读取现有内容
        if os.path.exists(history_file_path):
            try:
                with open(history_file_path, 'r', encoding='utf-8') as f:
                    conversation_history = json.load(f)
            except Exception as e:
                logger.error(f"读取对话历史文件出错: {str(e)}")
        
        # 添加新的对话记录
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })
        
        # 保存更新后的对话历史
        try:
            with open(history_file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存对话历史文件出错: {str(e)}")
            raise HTTPException(status_code=500, detail=f"保存对话历史失败: {str(e)}")
        
        return {"success": True, "message": "对话历史已更新"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话历史出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新对话历史失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 