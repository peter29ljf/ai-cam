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
import traceback

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
        print(f"Replacing image at page {page}, file: {dest}") # 添加日志
        
        # 保存上传的文件
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
            
        print(f"Successfully replaced {dest}") # 添加日志
        return {'message': f'已替换第{page}页图片'}
    except HTTPException as e:
        print(f"Error replacing image (HTTP): {e.detail}") # 添加日志
        raise e
    except Exception as e:
        print(f"Error replacing image (Exception): {str(e)}") # 添加日志
        raise HTTPException(status_code=500, detail=f"替换图片失败: {str(e)}")

@router.post('/images/insert/{page}')
async def insert_image(page: int, file: UploadFile = File(...)):
    """
    在指定页码之后插入图片
    page=0 表示在最前面插入
    page=N 表示在第N张图片后插入 (N >= 1)
    """
    try:
        # 验证文件类型和大小 (与 /upload 类似)
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

        content = await file.read()
        file_size = len(content) / (1024 * 1024) # MB
        max_size = 5 if file_ext != '.mp4' else 200
        if file_size > max_size:
            raise HTTPException(status_code=400, detail=f"文件太大: {file_size:.2f}MB，最大允许{max_size}MB")

        files = get_sorted_images()
        num_files = len(files)

        # 验证页码
        if page < 0 or page > num_files:
             raise HTTPException(status_code=404, detail=f'无效的页码: {page}，当前共 {num_files} 张图片')

        # -- 根据 page 计算目标时间戳 --
        target_timestamp_ms = int(time.time() * 1000) # 默认是当前时间 (用于 page=0)

        if num_files > 0:
            if page == num_files: # 插入到最后 (Add button)
                # 获取当前最后一张图片的时间戳 (它是列表第一个，因为是降序)
                # 不对，get_sorted_images 是降序，最后一张是 files[num_files-1]
                try:
                    last_file_timestamp_str = files[num_files - 1].split('_')[0]
                    last_file_timestamp_ms = int(last_file_timestamp_str)
                    target_timestamp_ms = last_file_timestamp_ms - 1 # 比最后一张稍早
                except (IndexError, ValueError):
                    print(f"Warning: Could not parse timestamp from last file: {files[num_files - 1]}. Using current time minus offset.")
                    target_timestamp_ms = int(time.time() * 1000) - 5000 # fallback: 5秒前

            elif page > 0: # 在指定页码 N 之后插入 (Insert After button)
                # 需要在 files[page-1] 之后插入
                # 所以时间戳需要比 files[page-1] 的时间戳稍早
                try:
                    after_file_timestamp_str = files[page - 1].split('_')[0]
                    after_file_timestamp_ms = int(after_file_timestamp_str)
                    target_timestamp_ms = after_file_timestamp_ms - 1 # 比目标图片稍早
                except (IndexError, ValueError):
                     print(f"Warning: Could not parse timestamp from file at page {page}: {files[page - 1]}. Using current time.")
                     target_timestamp_ms = int(time.time() * 1000) # fallback: 当前时间
        # -- 时间戳计算结束 --

        # 使用原始文件名的一部分，防止特殊字符问题
        original_filename_stem = Path(file.filename).stem
        original_filename_suffix = Path(file.filename).suffix
        safe_original_part = "".join(c for c in original_filename_stem if c.isalnum() or c in ('_', '-'))[:50] # 保留部分安全字符
        
        # 确保时间戳是唯一的，如果计算出的时间戳已存在，稍微调整
        while True:
            new_filename = f"{target_timestamp_ms}_{safe_original_part}{original_filename_suffix}"
            file_path = SHOTS_DIR / new_filename
            if not file_path.exists():
                break
            target_timestamp_ms -= 1 # 如果冲突，时间戳再减1毫秒

        print(f"Inserting image after page {page}. Target timestamp: {target_timestamp_ms}, New file: {file_path}")

        # 写入文件
        with open(file_path, "wb") as f:
            f.write(content)

        print(f"Successfully inserted {file_path}")
        return {'message': f'已在第{page}页目标位置附近插入图片', 'new_filename': new_filename} # 修改消息提示

    except HTTPException as e:
        print(f"Error inserting image (HTTP): {e.detail}") # 添加日志
        raise e
    except Exception as e:
        print(f"Error inserting image (Exception): {str(e)}") # 添加日志
        traceback.print_exc() # 打印详细错误堆栈
        raise HTTPException(status_code=500, detail=f"插入图片失败: {str(e)}") 