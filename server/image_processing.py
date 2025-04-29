import os
import shutil
import io
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from PIL import Image

SHOTS_DIR = os.path.join(os.path.dirname(__file__), 'shots')

router = APIRouter()

def get_sorted_images():
    files = [f for f in os.listdir(SHOTS_DIR) if f.startswith('shot_') and f.endswith('.png')]
    files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    return files

@router.get('/images', response_model=List[str])
def list_images():
    return get_sorted_images()

@router.delete('/images/{page}')
def delete_image(page: int):
    files = get_sorted_images()
    if page < 1 or page > len(files):
        raise HTTPException(status_code=404, detail='页码不存在')
    os.remove(os.path.join(SHOTS_DIR, files[page-1]))
    # 重命名后续文件，保证页码连续
    for idx, fname in enumerate(get_sorted_images(), 1):
        new_name = f'shot_{idx}.png'
        if fname != new_name:
            os.rename(os.path.join(SHOTS_DIR, fname), os.path.join(SHOTS_DIR, new_name))
    return {'msg': '删除成功'}

@router.post('/images/replace/{page}')
def replace_image(page: int, file: UploadFile = File(...)):
    files = get_sorted_images()
    if page < 1 or page > len(files):
        raise HTTPException(status_code=404, detail='页码不存在')
    dest = os.path.join(SHOTS_DIR, files[page-1])
    # 重置文件指针并使用Pillow处理图片
    file.file.seek(0)
    img = Image.open(file.file)
    img.save(dest, format='PNG')
    return {'msg': '替换成功'}

@router.post('/images/insert/{page}')
def insert_image(page: int, file: UploadFile = File(...)):
    files = get_sorted_images()
    if page < 0 or page > len(files):
        raise HTTPException(status_code=404, detail='页码不存在')
    # 后移后续文件
    for idx in range(len(files), page, -1):
        src = os.path.join(SHOTS_DIR, f'shot_{idx}.png')
        dst = os.path.join(SHOTS_DIR, f'shot_{idx+1}.png')
        os.rename(src, dst)
    # 保存新图片
    dest = os.path.join(SHOTS_DIR, f'shot_{page+1}.png')
    # 重置文件指针并使用Pillow处理图片
    file.file.seek(0)
    img = Image.open(file.file)
    img.save(dest, format='PNG')
    return {'msg': '插入成功'} 