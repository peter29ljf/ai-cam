import os
import re
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 路由器
router = APIRouter()

# .env文件路径（位于项目根目录）
ENV_FILE = Path(__file__).parent.parent / '.env'

# 设置模型
class Settings(BaseModel):
    # 通用设置
    ACTIVE_MODEL: Optional[str] = 'deepseek'
    MODEL_AUTO_SWITCH: Optional[str] = 'false'
    MAIN_SYSTEM_PROMPT: Optional[str] = ''
    
    # 自定义提示词
    CUSTOM_PROMPT_NAME_0: Optional[str] = ''
    CUSTOM_PROMPT_CONTENT_0: Optional[str] = ''
    CUSTOM_PROMPT_NAME_1: Optional[str] = ''
    CUSTOM_PROMPT_CONTENT_1: Optional[str] = ''
    CUSTOM_PROMPT_NAME_2: Optional[str] = ''
    CUSTOM_PROMPT_CONTENT_2: Optional[str] = ''
    CUSTOM_PROMPT_NAME_3: Optional[str] = ''
    CUSTOM_PROMPT_CONTENT_3: Optional[str] = ''
    CUSTOM_PROMPT_NAME_4: Optional[str] = ''
    CUSTOM_PROMPT_CONTENT_4: Optional[str] = ''
    
    # Deepseek 设置
    DEEPSEEK_MODEL_NAME: Optional[str] = ''
    DEEPSEEK_API_KEY: Optional[str] = ''
    DEEPSEEK_API_ENDPOINT: Optional[str] = ''
    
    # 智谱 设置
    ZHIPUAI_MODEL_NAME: Optional[str] = ''
    ZHIPUAI_API_KEY: Optional[str] = ''
    ZHIPUAI_API_ENDPOINT: Optional[str] = ''
    
    # OpenAI 设置
    OPENAI_MODEL_NAME: Optional[str] = ''
    OPENAI_API_KEY: Optional[str] = ''
    OPENAI_API_ENDPOINT: Optional[str] = ''
    
    # Ollama 设置
    OLLAMA_MODEL_NAME: Optional[str] = ''
    OLLAMA_API_KEY: Optional[str] = ''
    OLLAMA_API_ENDPOINT: Optional[str] = ''
    
    # LM Studio 设置
    LMSTUDIO_MODEL_NAME: Optional[str] = ''
    LMSTUDIO_API_KEY: Optional[str] = ''
    LMSTUDIO_API_ENDPOINT: Optional[str] = ''

def read_env_file() -> Dict[str, str]:
    """读取.env文件内容"""
    settings = {}
    
    # 如果.env文件不存在，创建空文件
    if not ENV_FILE.exists():
        ENV_FILE.touch()
        return settings
    
    # 读取现有内容
    with open(ENV_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # 解析环境变量
            if match := re.match(r'^([A-Za-z0-9_]+)=(.*)$', line):
                key, value = match.groups()
                # 处理引号
                value = value.strip('\'"')
                settings[key] = value
    
    return settings

def write_env_file(settings: Dict[str, str]) -> None:
    """写入.env文件内容"""
    # 读取现有内容，保留注释和格式
    existing_lines = []
    existing_keys = set()
    
    if ENV_FILE.exists():
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    existing_lines.append(line)
                    continue
                    
                # 提取键
                if match := re.match(r'^([A-Za-z0-9_]+)=', line):
                    key = match.group(1)
                    existing_keys.add(key)
                    
                    # 如果设置中包含此键，更新值
                    if key in settings:
                        value = settings[key]
                        # 为包含特殊字符的值添加引号
                        if re.search(r'[\s"\'#]', value):
                            value = f'"{value}"'
                        existing_lines.append(f'{key}={value}')
                    else:
                        existing_lines.append(line)
    
    # 添加新的设置项
    for key, value in settings.items():
        if key not in existing_keys:
            # 为包含特殊字符的值添加引号
            if re.search(r'[\s"\'#]', value):
                value = f'"{value}"'
            existing_lines.append(f'{key}={value}')
    
    # 写入文件
    with open(ENV_FILE, 'w') as f:
        f.write('\n'.join(existing_lines))
        # 确保文件最后有一个换行符
        if existing_lines:
            f.write('\n')

@router.get('/settings')
async def get_settings() -> Dict[str, str]:
    """获取所有设置"""
    try:
        return read_env_file()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法读取设置: {str(e)}")

@router.post('/settings')
async def update_settings(settings: Settings) -> Dict[str, str]:
    """更新设置"""
    try:
        # 将设置转换为字典并过滤掉空值
        settings_dict = {k: v for k, v in settings.dict().items() if v is not None}
        
        # 特殊处理：确保API密钥格式正确
        if 'ZHIPUAI_API_KEY' in settings_dict:
            api_key = settings_dict['ZHIPUAI_API_KEY']
            # 检查API密钥格式
            if api_key and '.' not in api_key:
                raise HTTPException(status_code=400, detail=f"智谱API密钥格式错误，应包含'.'分隔的ID和密钥")
        
        # 写入.env文件
        write_env_file(settings_dict)
        
        return {"msg": "设置已保存"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法保存设置: {str(e)}") 