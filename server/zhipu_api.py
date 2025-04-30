#!/usr/bin/env python3
"""
智谱GLM-4v-plus API处理模块
"""
import os
import time
import json
import base64
import hashlib
import hmac
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv

# 路由器
router = APIRouter(prefix="/api/zhipu", tags=["zhipu"])

# 加载环境变量
load_dotenv()

# 智谱API配置
ZHIPU_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
# 如果新格式的密钥不存在，尝试从旧格式获取
if not ZHIPU_API_KEY:
    ZHIPU_API_KEY = os.getenv("API_KEY", "")
ZHIPU_MODEL = os.getenv("ZHIPUAI_MODEL_NAME", "glm-4v-plus-0111")  # 默认使用高级版多模态模型
ZHIPU_ENDPOINT = os.getenv("ZHIPUAI_API_ENDPOINT", "https://open.bigmodel.cn/api/paas/v4")

print(f"智谱API配置: 模型={ZHIPU_MODEL}, API密钥={ZHIPU_API_KEY[:8] if ZHIPU_API_KEY else '未设置'}...")

# 路径配置
TEMP_DIR = Path(__file__).parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# 模型
class ZhipuRequest(BaseModel):
    prompt: str
    image_paths: List[str] = []
    system_prompt: Optional[str] = None

class ZhipuTextRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None

class ZhipuResponse(BaseModel):
    content: str
    model: str
    
def generate_jwt_token(api_key: str, exp_seconds: int = 3600) -> str:
    """
    生成JWT Token
    """
    try:
        # 防止API密钥格式错误
        if "." not in api_key:
            raise ValueError(f"API密钥格式错误，应包含'.'分隔的ID和密钥: {api_key[:8]}...")
        
        api_key_parts = api_key.split(".")
        if len(api_key_parts) != 2:
            raise ValueError(f"API密钥格式错误，应有两部分: {api_key[:8]}...")
            
        id, secret = api_key_parts
        
        # JWT Header
        header = {"alg": "HS256", "sign_type": "SIGN"}
        header_base64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        
        # JWT Payload
        payload = {
            "api_key": id,
            "exp": int(time.time()) + exp_seconds,
            "timestamp": int(time.time())
        }
        payload_base64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        
        # JWT Signature
        signature_data = f"{header_base64}.{payload_base64}"
        signature = hmac.new(
            secret.encode(),
            signature_data.encode(),
            digestmod=hashlib.sha256
        ).digest()
        signature_base64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        
        # 组合Token
        token = f"{signature_data}.{signature_base64}"
        return token
    except Exception as e:
        print(f"JWT Token生成失败: {str(e)}")
        raise Exception(f"JWT Token generation failed: {str(e)}")

def encode_image_to_base64(image_path: str) -> str:
    """
    将图片转换为Base64编码
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return encoded_string
    except Exception as e:
        raise Exception(f"Image encoding failed: {str(e)}")

# 添加视频处理函数
def encode_video_to_base64(video_path: str) -> str:
    """
    将视频文件转换为Base64编码
    """
    try:
        with open(video_path, "rb") as video_file:
            encoded_string = base64.b64encode(video_file.read()).decode()
            return encoded_string
    except Exception as e:
        raise Exception(f"Video encoding failed: {str(e)}")

@router.post("/chat", response_model=ZhipuResponse)
async def chat_with_image(request: ZhipuRequest):
    """
    使用GLM-4v-plus模型进行多模态对话
    """
    try:
        if not ZHIPU_API_KEY:
            raise HTTPException(status_code=500, detail="未配置智谱API密钥")
            
        # 检查输入
        if not request.prompt:
            raise HTTPException(status_code=400, detail="提示词不能为空")
        
        # 准备请求头
        token = generate_jwt_token(ZHIPU_API_KEY)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备消息
        messages = []
        
        # 添加系统提示词
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # 处理图片
        user_content = []
        
        # 添加文本提示
        user_content.append({
            "type": "text",
            "text": request.prompt
        })
        
        # 遍历图片路径
        image_count = 0
        for path in request.image_paths:
            if not Path(path).exists():
                print(f"文件不存在: {path}")
                continue
                
            # 处理图片
            if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    # 检查图片大小限制
                    file_size = Path(path).stat().st_size / (1024 * 1024)  # MB
                    if file_size > 5:
                        print(f"图片大小超过限制(5MB): {path} ({file_size:.2f}MB)")
                        continue
                    
                    # 读取图片并编码
                    base64_image = encode_image_to_base64(path)
                    # 文件扩展名
                    file_ext = Path(path).suffix.lower().lstrip('.')
                    # 转换jpg扩展名为jpeg (智谱API兼容性要求)
                    if file_ext == 'jpg':
                        file_ext = 'jpeg'
                        
                    # 添加图片到用户内容
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{file_ext};base64,{base64_image}"
                        }
                    })
                    print(f"成功添加图片: {path}")
                    image_count += 1
                except Exception as e:
                    print(f"处理图片出错: {str(e)}")
                    
        # 限制图片数量
        if image_count == 0:
            print("警告: 没有成功处理任何图片，将使用纯文本对话模式")
            # 使用纯文本模式
            messages.append({
                "role": "user",
                "content": request.prompt
            })
        else:
            # 添加用户消息
            messages.append({
                "role": "user",
                "content": user_content
            })
            print(f"使用多模态对话模式，共 {image_count} 张图片")
        
        # 准备请求体
        payload = {
            "model": ZHIPU_MODEL,
            "messages": messages
        }
        
        print(f"正在发送请求到智谱API: {ZHIPU_ENDPOINT}")
        
        # 发送请求
        completion_url = f"{ZHIPU_ENDPOINT}/chat/completions"
        response = requests.post(
            completion_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # 检查响应
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_msg = error_json["error"].get("message", "未知错误")
                    error_code = error_json["error"].get("code", "")
                    error_detail = f"错误代码: {error_code}, 错误信息: {error_msg}"
            except:
                pass
                
            print(f"API错误: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"API错误: {error_detail}"
            )
            
        # 解析响应
        result = response.json()
        ai_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 返回结果
        return {
            "content": ai_content,
            "model": ZHIPU_MODEL
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"处理请求出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求出错: {str(e)}")

@router.post("/process_images")
async def process_images(
    prompt: str = Form(...),
    files: List[UploadFile] = File(None),
    system_prompt: Optional[str] = Form(None)
):
    """
    处理上传的图片和PDF并发送到智谱GLM-4v-plus模型
    """
    try:
        # 处理特殊标记
        use_images = '#使用图片' in prompt or '#useimages' in prompt
        clean_prompt = prompt.replace('#使用图片', '').replace('#useimages', '').strip()
        
        # 检查是否有上传的文件
        if not files:
            raise HTTPException(status_code=400, detail="请上传至少一个文件")
            
        image_paths = []
        has_pdf = False
        pdf_content = ""
        
        # 保存上传的文件
        for file in files:
            try:
                timestamp = int(time.time())
                filename = f"{timestamp}_{file.filename}"
                file_path = TEMP_DIR / filename
                
                # 检查文件类型
                is_pdf = file.filename.lower().endswith('.pdf')
                
                # 保存文件
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # 如果是PDF，提取文本（未来这里可以调用专门的PDF处理逻辑）
                if is_pdf:
                    has_pdf = True
                    try:
                        import PyPDF2
                        with open(file_path, "rb") as pdf_file:
                            pdf_reader = PyPDF2.PdfReader(pdf_file)
                            for page_num in range(len(pdf_reader.pages)):
                                page = pdf_reader.pages[page_num]
                                pdf_content += page.extract_text() + "\n\n"
                        
                        pdf_content += f"\n\n文件名: {file.filename}\n"
                    except ImportError:
                        # 如果没有PyPDF2，添加提示
                        pdf_content += f"[无法提取PDF文本，服务器缺少PyPDF2库]\n文件名: {file.filename}\n"
                else:
                    # 对于图片，添加到图片路径列表
                    image_paths.append(str(file_path))
            
            except Exception as e:
                print(f"处理文件 {file.filename} 出错: {str(e)}")
        
        # 如果有PDF但没有图片，或者用户不需要使用图片，使用纯文本模式
        if (has_pdf and not image_paths) or not use_images:
            # 将PDF内容添加到提示词
            final_prompt = clean_prompt
            if has_pdf:
                final_prompt = f"{clean_prompt}\n\n提取的PDF内容:\n{pdf_content}"
            
            # 使用纯文本API处理
            return await chat_text(
                ZhipuTextRequest(
                    prompt=final_prompt[:8000],  # 限制长度防止超出模型上限
                    system_prompt=system_prompt
                )
            )
        
        # 如果有PDF也有图片，将PDF内容添加到提示词
        if has_pdf:
            clean_prompt = f"{clean_prompt}\n\n同时上传的PDF内容概要:\n{pdf_content[:1500]}..."
            
        # 调用多模态聊天接口处理图片
        if image_paths:
            return await chat_with_image(
                ZhipuRequest(
                    prompt=clean_prompt,
                    image_paths=image_paths,
                    system_prompt=system_prompt
                )
            )
        else:
            raise HTTPException(status_code=400, detail="没有可处理的文件")
    
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"处理图片和PDF出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理文件出错: {str(e)}")

@router.post("/process_server_images")
async def process_server_images(request: ZhipuRequest):
    """
    处理服务器上的图片并发送到智谱GLM-4v-plus模型
    """
    try:
        # 处理特殊标记
        use_images = '#使用图片' in request.prompt or '#useimages' in request.prompt
        clean_prompt = request.prompt.replace('#使用图片', '').replace('#useimages', '').strip()
        
        print(f"接收到处理请求: 提示词={clean_prompt}, 使用图片={use_images}, 图片数={len(request.image_paths)}")
        
        # 如果不使用图片，直接使用纯文本模式
        if not use_images:
            print("用户选择不使用图片，使用纯文本模式")
            return await chat_text(ZhipuTextRequest(
                prompt=clean_prompt,
                system_prompt=request.system_prompt
            ))
            
        # 图片路径修正 - 将URL转为本地路径
        fixed_image_paths = []
        for path in request.image_paths:
            try:
                # 提取文件名
                filename = path.split('/')[-1]
                local_path = str(Path(__file__).parent / "shots" / filename)
                
                if Path(local_path).exists():
                    fixed_image_paths.append(local_path)
                    print(f"找到本地图片: {local_path}")
                else:
                    print(f"警告: 图片文件不存在: {local_path}")
                    # 尝试下载远程图片
                    if path.startswith(('http://', 'https://')):
                        try:
                            print(f"尝试下载远程图片: {path}")
                            response = requests.get(path, verify=False, timeout=10)
                            if response.status_code == 200:
                                # 保存到临时目录
                                temp_path = str(TEMP_DIR / filename)
                                with open(temp_path, 'wb') as f:
                                    f.write(response.content)
                                fixed_image_paths.append(temp_path)
                                print(f"已下载远程图片到: {temp_path}")
                            else:
                                print(f"下载远程图片失败: {response.status_code}")
                        except Exception as e:
                            print(f"下载远程图片出错: {str(e)}")
            except Exception as e:
                print(f"处理图片路径出错: {str(e)}")
        
        # 检查是否有可用图片
        if not fixed_image_paths:
            print("没有找到有效的图片路径")
            # 如果没有图片，尝试使用纯文本模式
            return await chat_text(ZhipuTextRequest(
                prompt=clean_prompt,
                system_prompt=request.system_prompt
            ))
        
        # 使用修正后的路径
        request.image_paths = fixed_image_paths
        request.prompt = clean_prompt
        print(f"修正后图片路径: {request.image_paths}")
        
        return await chat_with_image(request)
    except Exception as e:
        print(f"处理服务器图片出错: {str(e)}")
        # 尝试降级到纯文本模式
        try:
            print("尝试使用纯文本模式作为降级方案")
            return await chat_text(ZhipuTextRequest(
                prompt=request.prompt.replace('#使用图片', '').replace('#useimages', '').strip(),
                system_prompt=request.system_prompt
            ))
        except Exception as text_error:
            print(f"纯文本模式也失败: {str(text_error)}")
            raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}; 纯文本降级也失败: {str(text_error)}")

@router.post("/chat_text", response_model=ZhipuResponse)
async def chat_text(request: ZhipuTextRequest):
    """
    使用智谱GLM模型进行纯文本对话
    """
    try:
        if not ZHIPU_API_KEY:
            raise HTTPException(status_code=500, detail="未配置智谱API密钥")
            
        # 检查输入
        if not request.prompt:
            raise HTTPException(status_code=400, detail="提示词不能为空")
        
        # 准备请求头
        token = generate_jwt_token(ZHIPU_API_KEY)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备消息
        messages = []
        
        # 添加系统提示词
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # 添加用户消息
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        # 准备请求体
        payload = {
            "model": ZHIPU_MODEL,
            "messages": messages
        }
        
        print(f"正在发送请求到智谱API: {ZHIPU_ENDPOINT}, 模型: {ZHIPU_MODEL}")
        
        # 发送请求
        completion_url = f"{ZHIPU_ENDPOINT}/chat/completions"
        response = requests.post(
            completion_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        # 检查响应
        if response.status_code != 200:
            print(f"API错误: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"API错误: {response.text}")
            
        # 解析响应
        result = response.json()
        print(f"API响应: {result}")
        ai_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 返回结果
        return {
            "content": ai_content,
            "model": ZHIPU_MODEL
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"处理纯文本对话出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理纯文本对话出错: {str(e)}")

@router.get("/test_connection")
async def test_connection():
    """
    测试智谱API连接
    """
    try:
        if not ZHIPU_API_KEY:
            return {"status": "error", "message": "未配置智谱API密钥"}
            
        # 生成JWT Token
        try:
            token = generate_jwt_token(ZHIPU_API_KEY)
        except Exception as e:
            return {"status": "error", "message": f"生成JWT Token失败: {str(e)}"}
            
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 准备一个简单的消息
        messages = [
            {
                "role": "user",
                "content": "你好"
            }
        ]
        
        # 准备请求体
        payload = {
            "model": ZHIPU_MODEL,
            "messages": messages
        }
        
        # 发送请求
        completion_url = f"{ZHIPU_ENDPOINT}/chat/completions"
        response = requests.post(
            completion_url,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        # 检查响应
        if response.status_code != 200:
            error_message = response.text
            try:
                error_json = response.json()
                if "error" in error_json:
                    error_message = error_json.get("error", {}).get("message", error_message)
            except:
                pass
            return {
                "status": "error", 
                "message": f"API错误({response.status_code}): {error_message}"
            }
            
        # 解析响应
        result = response.json()
        
        return {
            "status": "success",
            "message": "智谱API连接正常",
            "model": ZHIPU_MODEL,
            "response": result.get("choices", [{}])[0].get("message", {}).get("content", "")
        }
        
    except Exception as e:
        return {"status": "error", "message": f"测试连接失败: {str(e)}"} 