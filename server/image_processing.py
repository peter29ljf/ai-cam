#!/usr/bin/env python3
"""
图像处理模块
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image

# 路由器
router = APIRouter()

# 截图目录
SHOTS_DIR = Path(__file__).parent / "shots"
SHOTS_DIR.mkdir(exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.mp4'}

def get_sorted_images():
    """
    获取排序后的图片列表
    """
    try:
        files = []
        for file_path in SHOTS_DIR.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                files.append(file_path.name)
                
        # 按时间戳排序（最新的在前）
        files.sort(reverse=True)
        return files
    except Exception as e:
        print(f"获取排序图片出错: {str(e)}")
        return []

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    上传图片或视频
    """
    try:
        results = []
        for file in files:
            # 文件名
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"不支持的文件类型: {file_ext}"
                })
                continue
                
            # 检查文件大小
            file_content = await file.read()
            file_size = len(file_content) / (1024 * 1024)  # MB
            
            max_size = 5 if file_ext != '.mp4' else 200  # 图片5MB，视频200MB
            
            if file_size > max_size:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"文件太大: {file_size:.2f}MB，最大允许{max_size}MB"
                })
                continue
            
            # 生成唯一文件名
            timestamp = int(time.time())
            new_filename = f"{timestamp}_{file.filename}"
            file_path = SHOTS_DIR / new_filename
            
            # 写入文件
            with open(file_path, "wb") as f:
                f.write(file_content)
                
            # 返回结果
            results.append({
                "filename": file.filename,
                "saved_as": new_filename,
                "status": "success",
                "type": "video" if file_ext == '.mp4' else "image"
            })
            
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传文件出错: {str(e)}")

@router.get("/images")
async def get_images():
    """
    获取所有截图
    """
    try:
        return get_sorted_images()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")

@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """
    删除指定截图
    """
    try:
        file_path = SHOTS_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
            
        file_path.unlink()
        return {"message": f"已删除文件: {filename}"}
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.delete("/images")
async def delete_all_images():
    """
    删除所有截图
    """
    try:
        count = 0
        for file_path in SHOTS_DIR.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                file_path.unlink()
                count += 1
                
        return {"message": f"已删除 {count} 个文件"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

@router.get("/shots/{filename}")
async def get_image(filename: str):
    """
    获取指定图片
    """
    try:
        file_path = SHOTS_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
            
        return FileResponse(path=str(file_path))
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件失败: {str(e)}")

# 以下是兼容API，保留原有功能但删除重复定义

@router.delete('/images/by-page/{page}')
async def delete_image_by_page(page: int):
    """
    按页码删除图片
    """
    try:
        files = get_sorted_images()
        if page < 1 or page > len(files):
            raise HTTPException(status_code=404, detail='页码不存在')
            
        # 获取对应文件名并删除
        filename = files[page-1]
        file_path = SHOTS_DIR / filename
        file_path.unlink()
        
        return {'message': f'已删除第{page}页图片: {filename}'}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除图片失败: {str(e)}")

@router.post('/images/replace/{page}')
async def replace_image(page: int, file: UploadFile = File(...)):
    """
    替换指定页码的图片
    """
    try:
        files = get_sorted_images()
        if page < 1 or page > len(files):
            raise HTTPException(status_code=404, detail='页码不存在')
            
        # 获取对应文件路径
        dest = SHOTS_DIR / files[page-1]
        
        # 保存上传的文件
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
            
        return {'message': f'已替换第{page}页图片'}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"替换图片失败: {str(e)}") 