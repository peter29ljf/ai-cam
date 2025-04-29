// 图片管理模块
// 使用代理，前端直接访问同源路径
const API_BASE = '/api/images';
const IMAGE_BASE = '/shots';

async function fetchImages() {
    // 添加时间戳防止缓存
    const res = await fetch(`${API_BASE}?t=${Date.now()}`);
    return await res.json();
}

async function deleteImage(page) {
    await fetch(`${API_BASE}/${page}`, { method: 'DELETE' });
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