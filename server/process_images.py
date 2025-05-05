import os
import base64
import json
import requests
import shutil
import argparse
from pathlib import Path
import re
import time
from typing import List, Dict, Optional, Any
import importlib.util

# 检查智谱API模块是否存在
ZHIPU_API_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zhipu_api.py")
HAS_ZHIPU_API = os.path.exists(ZHIPU_API_PATH)
if HAS_ZHIPU_API:
    print("检测到智谱API模块")
else:
    print("未找到智谱API模块，将使用LM Studio API")

# 命令行参数
parser = argparse.ArgumentParser(description='图片处理与文字提取工具')
parser.add_argument('--mode', choices=['extract', 'summary'], default='extract',
                   help='操作模式: extract(提取文字) 或 summary(生成文档)')
args = parser.parse_args()

# 配置
SHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
LM_STUDIO_URL = "http://192.168.1.217:1234/v1/chat/completions"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
MAX_BATCH_SIZE = 10  # 每批最多处理的图片数
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")  # 临时目录，用于重命名操作
PAGES_CACHE_FILE = os.path.join(TEMP_DIR, "pages_cache.json")  # 页面内容缓存文件
TEMP_MD_FILE = os.path.join(TEMP_DIR, "temp.md")  # 临时MD文件，用于保存提取的文字内容

def encode_image_to_base64(image_path):
    """将图片转换为 base64 编码的字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_sorted_images():
    """
    获取排序后的图片列表，与 image_processing.py 中保持一致
    """
    try:
        files = []
        for file_path in Path(SHOTS_DIR).glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.mp4'):
                files.append(file_path.name)
                
        # 按时间戳排序（最新的在前）
        files.sort(reverse=True)
        return files
    except Exception as e:
        print(f"获取排序图片出错: {str(e)}")
        return []

def rename_images_by_ui_order():
    """
    根据 UI 中的图片顺序重命名图片文件
    返回重命名后的图片路径列表
    """
    # 确保临时目录存在
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 清空临时目录中的图片文件，但保留缓存文件
    for file in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, file)
        if os.path.isfile(file_path) and not file.endswith('.json'):  # 保留json缓存文件
            os.remove(file_path)
    
    # 获取 UI 中的图片顺序（按 image_processing.py 中的逻辑获取）
    ui_image_list = get_sorted_images()
    
    if not ui_image_list:
        print("未找到需要处理的图片")
        return []
    
    print(f"UI 中的图片顺序: {ui_image_list}")
    
    # 按照顺序重命名并复制到临时目录
    renamed_paths = []
    for idx, filename in enumerate(ui_image_list):
        # 创建新文件名（确保按顺序排序）
        original_path = os.path.join(SHOTS_DIR, filename)
        new_filename = f"{idx+1:03d}{Path(filename).suffix}"
        new_path = os.path.join(TEMP_DIR, new_filename)
        
        # 复制文件到临时目录
        shutil.copy2(original_path, new_path)
        renamed_paths.append(new_path)
        print(f"已复制 {filename} 到 {new_path}")
    
    print(f"共重命名 {len(renamed_paths)} 个文件")
    return sorted(renamed_paths)  # 确保按照新的数字序号排序

def get_cached_pages():
    """读取缓存的页面内容"""
    if not os.path.exists(PAGES_CACHE_FILE):
        return []
    
    try:
        with open(PAGES_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取缓存文件失败: {str(e)}")
        return []

def save_pages_to_cache(pages):
    """将页面内容保存到缓存文件和MD文件"""
    # 直接覆盖保存到JSON缓存
    os.makedirs(os.path.dirname(PAGES_CACHE_FILE), exist_ok=True)
    with open(PAGES_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)
    
    # 同时保存到MD文件，便于汇总处理
    with open(TEMP_MD_FILE, 'w', encoding='utf-8') as f:
        for page in pages:
            f.write(f"## 第{page['page']}页\n\n")
            f.write(f"{page['text']}\n\n")
    
    print(f"已保存 {len(pages)} 页到缓存及临时MD文件")
    return pages

def send_extract_request(image_paths: List[str]) -> Optional[dict]:
    """发送请求到 LM Studio API，只提取图片文字内容"""
    # 将所有图片转换为 base64
    base64_images = [encode_image_to_base64(path) for path in image_paths]
    
    # 提取文字的提示词
    prompt_text = (
        "请仅提取以下图片中的文字内容，并按顺序返回，不要生成标题，"
        "内容只需原文输出，后续统一处理。"
    )
    
    # 构建请求
    payload = {
        "model": "gemma-3-12b-it",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }
        ],
        "stream": False
    }
    
    # 为每个图片添加内容
    for base64_img in base64_images:
        payload["messages"][0]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img}"
            }
        })
    
    # 发送请求
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(LM_STUDIO_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)
        return None

def send_summary_request(md_content: str) -> Optional[dict]:
    """
    基于MD文件内容，生成Markdown格式的标题和正文
    输入: MD文件内容字符串
    """
    summary_prompt = (
        "以下是已提取的所有页面内容，删掉一些不必要的字符，和重复的段落，整理成新的文档，"
        "不要随意搬动段落，要按照页码整体搬动。"
        "请根据上下文内容，为该文档生成一个合适的标题，并按照Markdown格式输出完整文档：\n\n"
        "# {title}\n\n"
        f"{md_content}"
    )
    
    # 如果可用智谱API，优先使用
    if HAS_ZHIPU_API:
        try:
            print("使用智谱API生成汇总...")
            # 动态导入zhipu_api模块
            spec = importlib.util.spec_from_file_location("zhipu_api", ZHIPU_API_PATH)
            zhipu_api = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(zhipu_api)
            
            # 检查API密钥是否配置
            if not zhipu_api.ZHIPU_API_KEY:
                print("智谱API密钥未配置，将使用LM Studio API")
                raise ValueError("API密钥未配置")
                
            # 由于zhipu_api.chat_text是异步函数，我们需要通过直接调用底层API来实现同步调用
            # 1. 创建请求数据
            request = zhipu_api.ZhipuTextRequest(prompt=summary_prompt)
            
            # 2. 获取API相关配置
            try:
                token = zhipu_api.generate_jwt_token(zhipu_api.ZHIPU_API_KEY)
            except Exception as e:
                print(f"生成JWT令牌失败: {str(e)}")
                raise
                
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 3. 准备消息内容
            messages = []
            if hasattr(request, 'system_prompt') and request.system_prompt:
                messages.append({
                    "role": "system",
                    "content": request.system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # 4. 发送请求
            payload = {
                "model": zhipu_api.ZHIPU_MODEL,
                "messages": messages
            }
            
            completion_url = f"{zhipu_api.ZHIPU_ENDPOINT}/chat/completions"
            print(f"发送请求到: {completion_url}")
            print(f"使用模型: {zhipu_api.ZHIPU_MODEL}")
            
            response = requests.post(
                completion_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # 5. 解析响应
            if response.status_code == 200:
                result = response.json()
                ai_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not ai_content:
                    print("智谱API返回内容为空")
                    raise ValueError("API返回内容为空")
                
                print("智谱API处理成功，返回内容长度:", len(ai_content))
                
                # 构造与LM Studio API相同格式的返回值
                return {
                    "choices": [
                        {
                            "message": {
                                "content": ai_content
                            }
                        }
                    ]
                }
            else:
                error_detail = "未知错误"
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_msg = error_json["error"].get("message", "未知错误")
                        error_code = error_json["error"].get("code", "")
                        error_detail = f"错误代码: {error_code}, 错误信息: {error_msg}"
                except:
                    error_detail = response.text
                    
                print(f"智谱API请求失败: {response.status_code} - {error_detail}")
                # 失败时继续使用LM Studio API
                raise ValueError(f"API请求失败: {response.status_code} - {error_detail}")
                
        except Exception as e:
            print(f"智谱API调用失败: {str(e)}，将使用LM Studio API")
    else:
        print("智谱API不可用，将使用LM Studio API")
    
    # 智谱API不可用或调用失败时，使用LM Studio API
    print("使用LM Studio API生成汇总...")
    payload = {
        "model": "gemma-3-12b-it",
        "messages": [
            {
                "role": "user", 
                "content": [
                    {
                        "type": "text", 
                        "text": summary_prompt
                    }
                ]
            }
        ],
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(LM_STUDIO_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"LM Studio API汇总请求失败: {response.status_code}")
        print(response.text)
        return None

def extract_title_and_content(response_data):
    """从 API 响应中提取标题和内容"""
    if not response_data or "choices" not in response_data:
        return None, None
    
    content = response_data["choices"][0]["message"]["content"]
    
    # 尝试从格式化的title标记中提取标题
    title_match = re.search(r'"title"\s*:\s*"([^"]+)"', content)
    if title_match:
        title = title_match.group(1).strip()
    else:
        # 如果没有找到格式化标题，尝试使用第一行作为标题
        lines = content.strip().split('\n')
        if not lines:
            return None, None
        
        title = lines[0].strip()
        # 移除Markdown标记符号和特殊字符
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = re.sub(r'^#+\s*', "", title)  # 移除开头的Markdown标题符号(#)
        title = re.sub(r'^\*+\s*', "", title)  # 移除开头的星号(*)
        title = re.sub(r'^\-+\s*', "", title)  # 移除开头的短横线(-)
        title = title.strip()
    
    # 返回标题和完整内容
    return title, content

def create_folder_and_file(title, content):
    """创建文件夹和文件"""
    if not title:
        print("无法提取标题，使用默认标题")
        title = "未命名文档"
    
    folder_path = os.path.join(OUTPUT_DIR, title)
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 创建文件夹
    os.makedirs(folder_path, exist_ok=True)
    
    # 创建文件
    file_path = os.path.join(folder_path, f"{title}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"已创建文件夹: {folder_path}")
    print(f"已创建文件: {file_path}")
    return folder_path, file_path

def process_images_in_batches(image_paths: List[str]) -> List[Dict[str, Any]]:
    """
    分批提取每张图片的文字，并标注页码，返回按页码整理的内容列表
    """
    total_images = len(image_paths)
    total_batches = (total_images + MAX_BATCH_SIZE - 1) // MAX_BATCH_SIZE  # 向上取整
    
    print(f"共 {total_images} 张图片，将分 {total_batches} 批处理")
    
    all_pages = []
    # 页码始终从1开始
    base_page_num = 0
    
    # 分批处理
    for i in range(total_batches):
        start_idx = i * MAX_BATCH_SIZE
        end_idx = min(start_idx + MAX_BATCH_SIZE, total_images)
        batch = image_paths[start_idx:end_idx]
        
        print(f"处理第 {i+1}/{total_batches} 批，包含 {len(batch)} 张图片")
        
        # 发送请求提取文字
        response = send_extract_request(batch)
        
        if not response:
            print(f"第 {i+1} 批处理失败，跳过")
            continue
        
        # 提取文字内容
        text_content = response["choices"][0]["message"]["content"]
        
        # 为每张图片分配页码和内容
        for j, img_path in enumerate(batch):
            # 页码从1开始连续编号
            page_number = base_page_num + start_idx + j + 1
            all_pages.append({
                "page": page_number,
                "text": text_content,
                "path": img_path
            })
        
        print(f"第 {i+1} 批处理完成，已提取文字")
    
    return all_pages

def clean_temp_directory():
    """清空临时目录中的所有文件"""
    if not os.path.exists(TEMP_DIR):
        return
    
    # 遍历并删除临时目录中的所有文件
    for file in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"已删除临时文件: {file_path}")
    
    print("已清空临时目录")

def extract_mode():
    """提取模式：重命名图片、提取文字并保存缓存"""
    print("运行模式: 提取文字")
    
    # 确保临时目录存在
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # 清空现有缓存文件
    if os.path.exists(PAGES_CACHE_FILE):
        os.remove(PAGES_CACHE_FILE)
        print("已清空之前的缓存文件")
    
    # 清空现有临时MD文件
    if os.path.exists(TEMP_MD_FILE):
        os.remove(TEMP_MD_FILE)
        print("已清空之前的临时MD文件")
    
    print("根据 UI 顺序重命名图片...")
    renamed_image_paths = rename_images_by_ui_order()
    
    if not renamed_image_paths:
        print("未找到图片或重命名失败")
        return
    
    print(f"找到 {len(renamed_image_paths)} 张图片")
    
    # 分批处理图片，提取文字内容
    print("开始分批提取图片文字...")
    pages_content = process_images_in_batches(renamed_image_paths)
    
    if not pages_content:
        print("提取文字失败")
        return
    
    # 保存页面内容到缓存和MD文件
    save_pages_to_cache(pages_content)
    
    print(f"已提取 {len(pages_content)} 页内容并保存到缓存和临时MD文件")
    print("执行汇总时请使用 --mode=summary 参数")

def summary_mode():
    """汇总模式：读取临时MD文件，生成文档标题和内容"""
    print("运行模式: 生成文档")
    
    # 检查临时MD文件是否存在
    if not os.path.exists(TEMP_MD_FILE):
        print("临时MD文件不存在，请先运行提取模式")
        return
    
    # 读取临时MD文件内容
    try:
        with open(TEMP_MD_FILE, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        if not md_content.strip():
            print("临时MD文件内容为空")
            return
        
        print("从临时MD文件读取内容成功")
        print("开始生成标题和汇总...")
        
        # 发送汇总请求，生成标题和完整文档
        if HAS_ZHIPU_API:
            print("使用智谱API(ACTIVE_MODEL)进行文档生成")
        else:
            print("使用LM Studio API进行文档生成")
            
        summary_response = send_summary_request(md_content)
        
        if not summary_response:
            print("生成标题和汇总失败")
            return
        
        # 提取标题和内容
        title, content = extract_title_and_content(summary_response)
        
        if not title or not content:
            print("无法提取标题或内容")
            return
        
        # 创建文件夹和文件
        folder_path, file_path = create_folder_and_file(title, content)
        
        # 清理临时目录
        clean_temp_directory()
        
        print("处理完成!")
        print(f"文件夹: {folder_path}")
        print(f"文件: {file_path}")
    
    except Exception as e:
        print(f"读取或处理临时MD文件出错: {str(e)}")
        return

def main():
    """主函数"""
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 根据命令行参数选择模式
    if args.mode == 'extract':
        extract_mode()
    elif args.mode == 'summary':
        summary_mode()
    else:
        print(f"未知模式: {args.mode}")

if __name__ == "__main__":
    main() 