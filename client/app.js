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
        });
    });
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
    const uploadBtn = document.getElementById('uploadBtn');
    
    // 预设提示词按钮
    promptBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            mainPrompt.value = btn.getAttribute('data-prompt');
        });
    });
    
    // 上传按钮
    uploadBtn.addEventListener('click', async () => {
        // 获取文件和提示词
        const fileInput = document.getElementById('fileUpload');
        const files = fileInput.files;
        const prompt = mainPrompt.value.trim();
        
        if (files.length === 0) {
            alert('请选择至少一个文件');
            return;
        }
        
        // 设置加载状态
        const aiResponse = document.getElementById('aiResponse');
        aiResponse.textContent = '正在处理，请稍候...';
        
        try {
            // 获取当前激活的模型配置
            const modelConfig = await window.getActiveModelConfig();
            
            // 这里后续会实现与选择的AI模型API的集成
            // 根据 modelConfig.model 和 modelConfig.autoSwitch 决定使用哪个模型
            
            aiResponse.innerHTML = `
                <p><strong>处理完成</strong></p>
                <p>使用模型: ${modelConfig.model} (${modelConfig.modelName || '未指定'})</p>
                <p>API密钥: ${modelConfig.apiKey ? '已配置' : '未配置'}</p>
                <p>访问节点: ${modelConfig.apiEndpoint || '未配置'}</p>
                <p>提示词: ${prompt || '未提供'}</p>
                <p>文件数量: ${files.length}</p>
                <p>自动切换: ${modelConfig.autoSwitch ? '启用' : '禁用'}</p>
                <p>此功能将在后续更新中完全实现。</p>
            `;
            
            // 根据不同模型的处理逻辑（未来实现）
            /*
            switch(modelConfig.model) {
                case 'deepseek':
                    // 调用Deepseek API
                    break;
                case 'zhipu':
                    // 调用智谱API
                    break;
                case 'openai':
                    // 调用OpenAI API
                    break;
                // 其他模型...
            }
            */
            
        } catch (error) {
            console.error('AI处理错误:', error);
            aiResponse.textContent = `处理出错: ${error.message}`;
        }
    });
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