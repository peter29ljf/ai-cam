/**
 * 手部监控系统 - 前端逻辑
 */

// 全局变量
let socket = null;
let video = null;
let canvas = null;
let ctx = null;
let hdCanvas = null;
let hdCtx = null;
let isMonitoring = false;
let frameInterval = null;
let shotCount = 0;

// 常量
// 动态获取当前主机地址，支持localhost和IP访问
const getServerUrl = () => {
    const hostname = window.location.hostname;
    // 根据当前协议选择ws或wss
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${protocol}://${hostname}:8000/ws`;
};
const SERVER_URL = getServerUrl();
const FRAME_RATE = 10; // 每秒帧数
const LOW_QUALITY = 0.6; // 低质量JPEG压缩率
const HIGH_QUALITY = 0.9; // 高质量JPEG压缩率

// DOM 元素
document.addEventListener('DOMContentLoaded', () => {
    // 初始化标签页
    initTabs();
    
    // 检查浏览器兼容性
    checkBrowserSupport();
    
    // 初始化监控页面
    initMonitorPage();
    
    // 初始化 AI 交互页面
    initAIPage();
    
    // 检查当前是否处于AI交互页面
    const activeTabId = document.querySelector('.tab-btn.active').getAttribute('data-tab');
    if (activeTabId === 'ai') {
        checkImagesAvailability();
    }
});

/**
 * 检查浏览器兼容性
 */
function checkBrowserSupport() {
    const statusDiv = document.createElement('div');
    statusDiv.className = 'browser-status';
    statusDiv.style.padding = '10px';
    statusDiv.style.marginBottom = '20px';
    statusDiv.style.borderRadius = '5px';
    
    // 检查是否可以访问摄像头
    const hasGetUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    
    if (!hasGetUserMedia) {
        // 摄像头不可用，显示警告和替代方案
        statusDiv.style.backgroundColor = '#ffe6e6';
        statusDiv.style.border = '1px solid #ff8080';
        statusDiv.innerHTML = `
            <h3 style="margin-top: 0;">⚠️ 浏览器兼容性问题</h3>
            <p>您的浏览器不支持摄像头访问，这可能是因为：</p>
            <ul>
                <li>您正在通过非安全上下文（非HTTPS或非localhost）访问</li>
                <li>浏览器没有摄像头访问权限</li>
                <li>浏览器版本过旧</li>
            </ul>
            <p><strong>解决方案：</strong></p>
            <ol>
                <li>请通过 <a href="http://localhost:8080">localhost</a> 访问此页面</li>
                <li>或使用我们的<a href="direct_demo.html">替代方案</a>，直接在终端运行程序</li>
            </ol>
        `;
        
        // 插入到页面顶部
        const container = document.querySelector('.container');
        container.insertBefore(statusDiv, container.firstChild);
    }
    
    return hasGetUserMedia;
}

/**
 * 初始化标签页切换
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 移除所有活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            // 添加当前活动状态
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            // 切换到图片管理时刷新
            if (tabId === 'image-manager' && window.renderImageManager) {
                renderImageManager(document.getElementById('image-manager-container'));
            }
            
            // 切换到AI交互页面时检查图片状态
            if (tabId === 'ai') {
                checkImagesAvailability();
            }
        });
    });
}

/**
 * 检查是否有可用的图片
 */
async function checkImagesAvailability() {
    try {
        const aiResponse = document.getElementById('aiResponse');
        
        // 显示初始提示
        aiResponse.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <p>AI聊天已准备就绪</p>
                <p>输入提示词与AI对话</p>
                <p><small>如需使用图片功能，请先在"实时监控"标签页中截取图片或在"图片管理"标签页中上传图片，然后在提示词中添加 #使用图片 标记</small></p>
            </div>
        `;
        
        // 从服务器获取所有图片
        const response = await fetch('/api/images');
        const images = await response.json();
        
        if (images.length > 0) {
            // 如果有图片，显示额外信息
            aiResponse.innerHTML += `
                <div style="text-align: center; padding: 10px; margin-top: 10px; background-color: #f6f6f6; border-radius: 5px;">
                    <p>当前有 ${images.length} 张图片可用</p>
                    <p>在提示词中添加 <code>#使用图片</code> 标记即可使用图片进行对话</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('检查图片出错:', error);
    }
}

/**
 * 初始化监控页面
 */
function initMonitorPage() {
    // 获取 DOM 元素
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    ctx = canvas.getContext('2d');
    
    // 创建高清画布（不在DOM中显示）
    hdCanvas = document.createElement('canvas');
    hdCtx = hdCanvas.getContext('2d');
    
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statusElem = document.getElementById('status');
    const shotCountElem = document.getElementById('shotCount');
    
    // 按钮事件
    startBtn.addEventListener('click', async () => {
        try {
            // 检查摄像头API是否可用
            if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) {
                throw new Error('您的浏览器不支持摄像头访问。请使用 localhost 访问或使用替代方案。');
            }
            
            // 访问摄像头
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            });
            
            video.srcObject = stream;
            await video.play();
            
            // 设置画布尺寸
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // 设置高清画布尺寸
            hdCanvas.width = video.videoWidth;
            hdCanvas.height = video.videoHeight;
            
            // 连接 WebSocket
            connectWebSocket();
            
            // 开始监控
            startMonitoring();
            
            // 更新 UI
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusElem.textContent = '监控中';
            
        } catch (error) {
            console.error('访问摄像头失败:', error);
            statusElem.textContent = '无法访问摄像头: ' + error.message;
            statusElem.style.color = 'red';
            
            // 显示替代方案链接
            const alternativeLink = document.createElement('div');
            alternativeLink.innerHTML = '<p style="margin-top: 10px;"><a href="direct_demo.html" class="control-btn" style="text-decoration: none;">使用替代方案</a></p>';
            statusElem.parentNode.appendChild(alternativeLink);
        }
    });
    
    stopBtn.addEventListener('click', () => {
        stopMonitoring();
        
        // 更新 UI
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusElem.textContent = '已停止';
    });
    
    // 初始化 shotCount 显示
    shotCountElem.textContent = shotCount.toString();
}

/**
 * 初始化 AI 交互页面
 */
function initAIPage() {
    const promptBtns = document.querySelectorAll('.prompt-btn:not(.custom-prompt-btn)');
    const mainPrompt = document.getElementById('mainPrompt');
    const sendPromptBtn = document.getElementById('sendPromptBtn');
    const selectFilesBtn = document.getElementById('selectFilesBtn');
    const uploadAllBtn = document.getElementById('uploadAllBtn');
    const fileInput = document.getElementById('fileUpload');
    
    // 添加"使用图片"按钮
    const useImagesBtn = document.createElement('button');
    useImagesBtn.className = 'control-btn use-images-btn';
    useImagesBtn.textContent = '使用图片模式';
    useImagesBtn.title = '添加#使用图片标记，切换到图片对话模式';
    useImagesBtn.style.backgroundColor = '#13c2c2';
    useImagesBtn.style.marginRight = '10px';
    
    // 插入到发送按钮之前
    sendPromptBtn.parentNode.insertBefore(useImagesBtn, sendPromptBtn);
    
    // 添加点击事件
    useImagesBtn.addEventListener('click', () => {
        // 如果提示词结尾已经有#使用图片标记，则移除
        if (mainPrompt.value.trim().endsWith('#使用图片')) {
            mainPrompt.value = mainPrompt.value.replace(/#使用图片$/, '').trim();
            useImagesBtn.textContent = '使用图片模式';
            useImagesBtn.style.backgroundColor = '#13c2c2';
        } else {
            // 添加标记到提示词结尾
            mainPrompt.value = mainPrompt.value.trim() + ' #使用图片';
            useImagesBtn.textContent = '纯文本模式';
            useImagesBtn.style.backgroundColor = '#722ed1';
        }
        // 聚焦回文本框
        mainPrompt.focus();
    });
    
    // 预设提示词按钮
    promptBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            mainPrompt.value = btn.getAttribute('data-prompt');
        });
    });
    
    // 文件选择按钮
    selectFilesBtn.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 文件选择变化后处理上传
    fileInput.addEventListener('change', async () => {
        const files = fileInput.files;
        if (!files || files.length === 0) return;
        
        const aiResponse = document.getElementById('aiResponse');
        aiResponse.innerHTML = `
            <div style="padding: 10px; background-color: #e6f7ff; border-radius: 4px; margin-bottom: 15px;">
                <p>正在处理 ${files.length} 个文件...</p>
            </div>
        `;
        
        try {
            // 创建FormData对象
            const formData = new FormData();
            
            // 添加默认提示词
            formData.append('prompt', '请分析这些文档内容');
            
            // 获取系统提示词
            let systemPrompt = window.localStorage.getItem('MAIN_SYSTEM_PROMPT') || '';
            if (!systemPrompt) {
                try {
                    const settingsResp = await fetch('/api/settings');
                    const settings = await settingsResp.json();
                    systemPrompt = settings.MAIN_SYSTEM_PROMPT || '';
                } catch (e) {
                    console.error('获取系统提示词失败', e);
                }
            }
            
            if (systemPrompt) {
                formData.append('system_prompt', systemPrompt);
            }
            
            // 添加所有文件
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            // 上传文件
            const uploadResponse = await fetch('/api/zhipu/process_images', {
                method: 'POST',
                body: formData
            });
            
            if (!uploadResponse.ok) {
                throw new Error(`上传错误: ${uploadResponse.status} - ${await uploadResponse.text()}`);
            }
            
            const result = await uploadResponse.json();
            
            // 显示结果
            aiResponse.innerHTML = `
                <div class="ai-result">
                    <p class="ai-model">处理完成</p>
                    <div class="ai-content">${formatMarkdown(result.content)}</div>
                </div>
            `;
            
            // 清空文件输入，允许重新上传相同文件
            fileInput.value = '';
            
        } catch (error) {
            console.error('文件上传失败:', error);
            aiResponse.innerHTML = `
                <div style="color: #ff4d4f; padding: 10px; border: 1px solid #ff4d4f; border-radius: 5px;">
                    <p><strong>文件上传失败</strong></p>
                    <p>${error.message}</p>
                </div>
            `;
        }
    });
    
    // 上传全部截图按钮
    uploadAllBtn.addEventListener('click', async () => {
        const aiResponse = document.getElementById('aiResponse');
        aiResponse.textContent = '正在获取截图列表...';
        try {
            const resp = await fetch('/api/images');
            const images = await resp.json();
            
            if (images.length === 0) {
                aiResponse.textContent = '没有可用的截图，请先在"实时监控"标签页截取图片';
                return;
            }
            
            // 显示正在处理信息
            aiResponse.innerHTML = `
                <div style="padding: 10px; background-color: #e6f7ff; border-radius: 4px; margin-bottom: 15px;">
                    <p>正在处理 ${images.length} 张截图...</p>
                </div>
            `;
            
            // 创建FormData对象用于上传
            const formData = new FormData();
            
            // 添加提示词（自动添加#使用图片标记）
            formData.append('prompt', '请描述这些图片内容 #使用图片');
            
            // 获取系统提示词
            let systemPrompt = window.localStorage.getItem('MAIN_SYSTEM_PROMPT') || '';
            // 如果localStorage中没有，尝试从settings获取
            if (!systemPrompt) {
                try {
                    const settingsResp = await fetch('/api/settings');
                    const settings = await settingsResp.json();
                    systemPrompt = settings.MAIN_SYSTEM_PROMPT || '';
                } catch (e) {
                    console.error('获取系统提示词失败', e);
                }
            }
            
            if (systemPrompt) {
                formData.append('system_prompt', systemPrompt);
            }
            
            // 循环获取图片并添加到FormData
            const fetchPromises = images.map(async (img) => {
                try {
                    // 获取图片文件
                    const imgResponse = await fetch(`/api/shots/${img}`);
                    const imgBlob = await imgResponse.blob();
                    
                    // 添加到FormData，使用原始文件名
                    formData.append('files', new File([imgBlob], img, {
                        type: imgBlob.type
                    }));
                    
                    return true;
                } catch (err) {
                    console.error(`获取图片 ${img} 失败:`, err);
                    return false;
                }
            });
            
            // 等待所有图片获取完成
            await Promise.all(fetchPromises);
            
            // 上传图片并发送到智谱API
            const uploadResponse = await fetch('/api/zhipu/process_images', {
                method: 'POST',
                body: formData
            });
            
            if (!uploadResponse.ok) {
                throw new Error(`上传错误: ${uploadResponse.status} - ${await uploadResponse.text()}`);
            }
            
            const result = await uploadResponse.json();
            
            // 显示结果
            aiResponse.innerHTML = `
                <div class="ai-result">
                    <p class="ai-model">处理完成</p>
                    <div class="ai-content">${formatMarkdown(result.content)}</div>
                </div>
            `;
            
        } catch (error) {
            console.error('上传截图失败:', error);
            aiResponse.innerHTML = `
                <div style="color: #ff4d4f; padding: 10px; border: 1px solid #ff4d4f; border-radius: 5px;">
                    <p><strong>上传失败</strong></p>
                    <p>${error.message}</p>
                </div>
            `;
        }
    });
    
    // 发送提示词按钮
    sendPromptBtn.addEventListener('click', async () => {
        await processPrompt();
    });
    
    // 支持在文本框中按Enter键发送
    mainPrompt.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            e.preventDefault();
            await processPrompt();
        }
    });
    
    /**
     * 处理提示词并与AI交互
     */
    async function processPrompt() {
        const prompt = mainPrompt.value.trim();
        
        if (!prompt) {
            alert('请输入提示词');
            return;
        }
        
        // 设置加载状态
        const aiResponse = document.getElementById('aiResponse');
        aiResponse.textContent = '思考中...';
        
        try {
            // 获取当前激活的模型配置
            const modelConfig = await window.getActiveModelConfig();
            
            // 检查是否需要使用图片（在提示词中添加特殊标记）
            const useImages = prompt.toLowerCase().includes('#使用图片') || prompt.toLowerCase().includes('#useimages');
            
            // 准备最终提示词（移除特殊标记）
            let finalPrompt = prompt.replace(/#使用图片/gi, '').replace(/#useimages/gi, '').trim();
            
            // 获取系统提示词
            let systemPrompt = "";
            if (modelConfig.model === 'zhipu') {
                systemPrompt = window.localStorage.getItem('MAIN_SYSTEM_PROMPT') || '';
                // 如果localStorage中没有，尝试从settings获取
                if (!systemPrompt) {
                    try {
                        const settingsResp = await fetch('/api/settings');
                        const settings = await settingsResp.json();
                        systemPrompt = settings.MAIN_SYSTEM_PROMPT || '';
                    } catch (e) {
                        console.error('获取系统提示词失败', e);
                    }
                }
            }
            
            // 根据不同模型调用不同API
            let result;
            
            if (modelConfig.model === 'zhipu') {
                // 显示处理中状态
                aiResponse.innerHTML = `
                    <div style="margin-bottom: 10px; color: #1890ff;">
                        <p>正在使用智谱 ${modelConfig.modelName} 处理中...</p>
                        <p><small>模型名称: ${modelConfig.modelName}</small></p>
                        <p><small>模式: ${useImages ? '多模态(图片)' : '纯文本'}</small></p>
                    </div>
                `;
                
                try {
                    // 如果需要使用图片
                    if (useImages) {
                        // 从服务器获取所有图片
                        const imagesResponse = await fetch('/api/images');
                        const images = await imagesResponse.json();
                        
                        if (images.length === 0) {
                            aiResponse.textContent = '没有可用的图片，请先截取或上传图片';
                            return;
                        }
                        
                        // 调用智谱API（多模态）
                        const zhipuResponse = await fetch('/api/zhipu/process_server_images', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                prompt: finalPrompt,
                                image_paths: images.map(img => `${window.location.protocol}//${window.location.hostname}:8000/shots/${img}`),
                                system_prompt: systemPrompt
                            })
                        });
                        
                        if (!zhipuResponse.ok) {
                            let errorMessage = await zhipuResponse.text();
                            try {
                                // 尝试解析为JSON
                                const errorJson = JSON.parse(errorMessage);
                                if (errorJson.detail) {
                                    errorMessage = errorJson.detail;
                                }
                            } catch (e) {
                                // 不是JSON，保持原样
                            }
                            
                            throw new Error(`API错误(${zhipuResponse.status}): ${errorMessage}`);
                        }
                        
                        result = await zhipuResponse.json();
                    } else {
                        // 使用纯文本API
                        const textResponse = await fetch('/api/zhipu/chat_text', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                prompt: finalPrompt,
                                system_prompt: systemPrompt
                            })
                        });
                        
                        if (!textResponse.ok) {
                            throw new Error(`API错误: ${textResponse.status} - ${await textResponse.text()}`);
                        }
                        
                        result = await textResponse.json();
                    }
                    
                    // 显示结果
                    aiResponse.innerHTML = `
                        <div class="ai-result">
                            <p class="ai-model">使用模型: 智谱 ${modelConfig.modelName} ${useImages ? '(多模态)' : '(纯文本)'}</p>
                            <div class="ai-content">${formatMarkdown(result.content)}</div>
                        </div>
                    `;
                } catch (apiError) {
                    console.error('API错误:', apiError);
                    
                    // 如果多模态模式失败，尝试纯文本模式
                    if (useImages) {
                        aiResponse.innerHTML += `
                            <div style="margin: 10px 0; color: #faad14;">
                                <p>图像处理API出错: ${apiError.message}</p>
                                <p>正在尝试使用纯文本API作为备选...</p>
                            </div>
                        `;
                        
                        try {
                            const textResponse = await fetch('/api/zhipu/chat_text', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    prompt: finalPrompt,
                                    system_prompt: systemPrompt
                                })
                            });
                            
                            if (!textResponse.ok) {
                                throw new Error(`纯文本API错误: ${textResponse.status} - ${await textResponse.text()}`);
                            }
                            
                            result = await textResponse.json();
                            
                            aiResponse.innerHTML = `
                                <div class="ai-result">
                                    <p class="ai-model">使用模型: 智谱 ${modelConfig.modelName} (纯文本模式)</p>
                                    <div class="ai-content">${formatMarkdown(result.content)}</div>
                                </div>
                            `;
                        } catch (textApiError) {
                            throw new Error(`所有API尝试均失败: ${apiError.message}; 纯文本API: ${textApiError.message}`);
                        }
                    } else {
                        throw apiError; // 直接抛出错误
                    }
                }
            } else {
                // 其他模型处理（未来扩展）
                aiResponse.innerHTML = `
                    <p><strong>当前仅支持智谱模型</strong></p>
                    <p>请在设置中选择智谱模型</p>
                `;
            }
            
        } catch (error) {
            console.error('AI处理错误:', error);
            aiResponse.innerHTML = `
                <div style="color: #ff4d4f; padding: 10px; border: 1px solid #ff4d4f; border-radius: 5px;">
                    <p><strong>处理出错</strong></p>
                    <p>${error.message}</p>
                </div>
            `;
        }
    }
}

/**
 * 格式化Markdown内容为HTML
 */
function formatMarkdown(text) {
    if (!text) return '';
    
    // 简单的Markdown格式化
    // 1. 处理代码块
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // 2. 处理行内代码
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // 3. 处理标题
    text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // 4. 处理粗体
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // 5. 处理斜体
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // 6. 处理换行
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

/**
 * 连接 WebSocket
 */
function connectWebSocket() {
    // 关闭之前的连接
    if (socket) {
        socket.close();
    }
    
    // 创建新连接
    socket = new WebSocket(SERVER_URL);
    
    // 连接成功
    socket.onopen = () => {
        console.log('WebSocket 连接成功');
        document.getElementById('status').textContent = '已连接';
    };
    
    // 接收消息
    socket.onmessage = (event) => {
        const message = event.data;
        console.log('接收消息:', message);
        
        // 处理消息
        if (message.includes('截图成功')) {
            shotCount++;
            document.getElementById('shotCount').textContent = shotCount.toString();
        } 
        // 响应高清截图请求
        else if (message.includes('请发送高清截图')) {
            sendHighQualityFrame();
        }
    };
    
    // 连接关闭
    socket.onclose = () => {
        console.log('WebSocket 连接关闭');
        document.getElementById('status').textContent = '连接已断开';
    };
    
    // 连接错误
    socket.onerror = (error) => {
        console.error('WebSocket 错误:', error);
        document.getElementById('status').textContent = '连接错误';
    };
}

/**
 * 发送高清帧
 */
function sendHighQualityFrame() {
    if (!isMonitoring || !socket || socket.readyState !== WebSocket.OPEN) {
        return;
    }
    
    // 绘制视频帧到高清画布
    hdCtx.drawImage(video, 0, 0, hdCanvas.width, hdCanvas.height);
    
    // 将高清画布内容转换为高质量 JPEG
    hdCanvas.toBlob(blob => {
        if (blob && socket && socket.readyState === WebSocket.OPEN) {
            socket.send(blob);
        }
    }, 'image/jpeg', HIGH_QUALITY); // 设置质量为 0.9
}

/**
 * 开始监控
 */
function startMonitoring() {
    isMonitoring = true;
    
    // 定时发送视频帧
    frameInterval = setInterval(() => {
        if (!isMonitoring || !socket || socket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        // 绘制视频帧到画布
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // 将画布内容转换为低质量 JPEG
        canvas.toBlob(blob => {
            if (blob && socket && socket.readyState === WebSocket.OPEN) {
                socket.send(blob);
            }
        }, 'image/jpeg', LOW_QUALITY); // 设置质量为 0.6
    }, 1000 / FRAME_RATE);
}

/**
 * 停止监控
 */
function stopMonitoring() {
    isMonitoring = false;
    
    // 清除定时器
    if (frameInterval) {
        clearInterval(frameInterval);
        frameInterval = null;
    }
    
    // 关闭摄像头
    if (video && video.srcObject) {
        const tracks = video.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        video.srcObject = null;
    }
    
    // 关闭 WebSocket
    if (socket) {
        socket.close();
        socket = null;
    }
} 