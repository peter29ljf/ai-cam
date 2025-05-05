// 图片管理模块
// 使用代理，前端直接访问同源路径
const API_BASE = '/api/images';
const IMAGE_BASE = '/shots';

async function fetchImages() {
    // 添加时间戳防止缓存
    try {
        const res = await fetch(`${API_BASE}?t=${Date.now()}`);
        if (!res.ok) {
            console.error('API 请求失败:', res.status);
            return []; // 出错时返回空数组
        }
        const data = await res.json();
        return Array.isArray(data) ? data : []; // 确保返回数组
    } catch (error) {
        console.error('获取图片列表失败:', error);
        return []; // 出错时返回空数组
    }
}

async function deleteImage(page) {
    try {
        // 先获取图片列表
        const images = await fetchImages();
        if (page < 1 || page > images.length) {
            console.error('页码超出范围:', page);
            return;
        }
        
        // 获取对应的文件名
        const filename = images[page-1];
        
        // 调用删除API
        const response = await fetch(`${API_BASE}/${filename}`, { 
            method: 'DELETE' 
        });
        
        if (!response.ok) {
            console.error('删除图片失败:', response.status);
            alert(`删除图片失败: ${response.status}`);
        }
    } catch (error) {
        console.error('删除图片出错:', error);
        alert(`删除图片出错: ${error.message}`);
    }
}

async function replaceImage(page, file) {
    const formData = new FormData();
    formData.append('file', file);
    await fetch(`${API_BASE}/replace/${page}`, { method: 'POST', body: formData });
}

async function insertImage(page, file) {
    const formData = new FormData();
    formData.append('file', file);
    await fetch(`${API_BASE}/insert/${page}`, { method: 'POST', body: formData });
}

// 添加新图片：在最后插入
async function addImage(file) {
    // 获取当前图片列表长度，用作插入位置
    const images = await fetchImages();
    const page = images.length;  // 在末尾插入
    await insertImage(page, file);
}

function renderImageManager(container) {
    fetchImages().then(images => {
        container.innerHTML = '';
        images.forEach((img, idx) => {
            const div = document.createElement('div');
            div.className = 'image-item';
            div.innerHTML = `
                <div class="img-thumb"><img src="${IMAGE_BASE}/${img}?t=${Date.now()}" alt="截图${idx+1}" style="width: 20vw; max-width: 90%; height: auto; display: block; margin: 0 auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);" /></div>
                <div class="img-actions" style="display: flex; flex-direction: row; justify-content: center; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap;">
                    <span style="font-size: 14px; min-width: 60px; text-align: center;">页码：${idx+1}</span>
                    <button class="delete-btn" style="font-size: 15px; padding: 6px 14px; border-radius: 6px; background:#ff4d4f;color:#fff;border:none;">删除</button>
                    <input type="file" class="replace-input" style="display:none" />
                    <button class="replace-btn" style="font-size: 15px; padding: 6px 14px; border-radius: 6px; background:#1890ff;color:#fff;border:none;">替换</button>
                    <input type="file" class="insert-input" style="display:none" />
                    <button class="insert-btn" style="font-size: 15px; padding: 6px 14px; border-radius: 6px; background:#52c41a;color:#fff;border:none;">在后插入</button>
                    <button class="view-btn" style="font-size: 15px; padding: 6px 14px; border-radius: 6px; background:#faad14;color:#fff;border:none;">查看原图</button>
                </div>
            `;
            // 删除
            div.querySelector('.delete-btn').onclick = async () => {
                await deleteImage(idx+1);
                renderImageManager(container);
            };
            // 替换
            div.querySelector('.replace-btn').onclick = () => {
                div.querySelector('.replace-input').click();
            };
            div.querySelector('.replace-input').onchange = async (e) => {
                if (e.target.files.length) {
                    await replaceImage(idx+1, e.target.files[0]);
                    renderImageManager(container);
                }
            };
            // 插入
            div.querySelector('.insert-btn').onclick = () => {
                div.querySelector('.insert-input').click();
            };
            div.querySelector('.insert-input').onchange = async (e) => {
                if (e.target.files.length) {
                    await insertImage(idx+1, e.target.files[0]);
                    renderImageManager(container);
                }
            };
            // 查看原图
            div.querySelector('.view-btn').onclick = () => {
                window.open(`${IMAGE_BASE}/${img}?t=${Date.now()}`, '_blank');
            };
            container.appendChild(div);
        });
    });
}

window.renderImageManager = renderImageManager;

// 统一绑定删除所有、添加按钮事件
document.addEventListener('DOMContentLoaded', () => {
    const deleteAllBtn = document.getElementById('delete-all-btn');
    const addBtn = document.getElementById('add-btn');
    const addInput = document.getElementById('add-input');
    const processImagesBtn = document.getElementById('process-images-btn');
    const container = document.getElementById('image-manager-container');
    
    if (deleteAllBtn && window.renderImageManager) {
        deleteAllBtn.addEventListener('click', async () => {
            if (confirm('确定要删除所有图片吗？')) {
                await deleteAllImages();
                renderImageManager(container);
            }
        });
    }
    
    if (addBtn && addInput && window.renderImageManager) {
        addBtn.addEventListener('click', () => addInput.click());
        addInput.addEventListener('change', async (e) => {
            if (e.target.files.length) {
                await addImage(e.target.files[0]);
                renderImageManager(container);
                addInput.value = '';
            }
        });
    }
    
    // 处理图片按钮点击事件
    if (processImagesBtn) {
        processImagesBtn.addEventListener('click', async () => {
            // 显示处理中状态
            processImagesBtn.disabled = true;
            processImagesBtn.textContent = '文字提取中...';
            
            try {
                // 第一步：提取文字
                let response = await fetch('/api/process-images?mode=extract', {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error(`文字提取失败: ${response.status}`);
                }
                
                let result = await response.json();
                
                if (!result.success) {
                    throw new Error(`文字提取失败: ${result.message || '未知错误'}`);
                }
                
                // 第二步：生成文档
                processImagesBtn.textContent = '生成文档中...';
                
                response = await fetch('/api/process-images?mode=summary', {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error(`生成文档失败: ${response.status}`);
                }
                
                result = await response.json();
                
                if (result.success) {
                    alert(`处理成功: 文档已生成`);
                } else {
                    alert(`生成文档失败: ${result.message || '未知错误'}`);
                }
            } catch (error) {
                console.error('处理图片出错:', error);
                alert(`处理图片出错: ${error.message}`);
            } finally {
                // 恢复按钮状态
                processImagesBtn.disabled = false;
                processImagesBtn.textContent = '处理图片';
            }
        });
    }
});

// 删除所有图片
async function deleteAllImages() {
    try {
        await fetch(API_BASE, { method: 'DELETE' });
    } catch (error) {
        console.error('删除所有图片失败:', error);
    }
} 