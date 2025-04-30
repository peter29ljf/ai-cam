/**
 * 设置管理器 - 管理系统设置
 * 负责在页面加载时从服务器获取设置，以及将设置保存到服务器
 */

// DOM元素
let modelSelect;
let modelName;
let apiKey;
let apiEndpoint;
let modelSwitch;
let mainSystemPrompt;
let customPromptNames;
let customPromptContents;
let saveSettingsBtn;
let settingsStatus;
let testApiBtn;
let apiTestResult;

// 模型映射前缀
const MODEL_PREFIXES = {
    'deepseek': 'DEEPSEEK',
    'zhipu': 'ZHIPUAI',
    'openai': 'OPENAI',
    'ollama': 'OLLAMA',
    'lmstudio': 'LMSTUDIO'
};

// 初始化设置管理器
document.addEventListener('DOMContentLoaded', () => {
    // 获取DOM元素
    modelSelect = document.getElementById('model-select');
    modelName = document.getElementById('model-name');
    apiKey = document.getElementById('api-key');
    apiEndpoint = document.getElementById('api-endpoint');
    modelSwitch = document.getElementById('model-switch');
    mainSystemPrompt = document.getElementById('main-system-prompt');
    customPromptNames = document.querySelectorAll('.custom-prompt-name');
    customPromptContents = document.querySelectorAll('.custom-prompt-content');
    saveSettingsBtn = document.getElementById('save-settings');
    settingsStatus = document.getElementById('settings-status');
    testApiBtn = document.getElementById('test-api-btn');
    apiTestResult = document.getElementById('api-test-result');

    // 从服务器加载设置
    loadSettings();

    // 保存设置事件
    saveSettingsBtn.addEventListener('click', saveSettings);
    
    // 当切换到设置标签页时重新加载设置
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.tab === 'settings') {
            btn.addEventListener('click', () => {
                loadSettings();
            });
        }
    });
    
    // 当更改模型时，动态更新输入字段
    modelSelect.addEventListener('change', () => {
        updateModelFields();
    });
    
    // 添加测试API连接事件
    testApiBtn.addEventListener('click', testApiConnection);
    
    // 更新AI标签页中的自定义提示词按钮
    updateCustomPromptButtons();
});

/**
 * 从服务器加载设置
 */
async function loadSettings() {
    try {
        settingsStatus.textContent = '正在加载设置...';
        settingsStatus.style.color = '#1890ff';
        
        const response = await fetch('/api/settings');
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const settings = await response.json();
        
        // 填充通用设置
        if (settings.ACTIVE_MODEL) {
            modelSelect.value = settings.ACTIVE_MODEL;
        }
        
        // 加载当前选择的模型对应的设置
        updateModelFields(settings);
        
        // 模型切换开关
        if (settings.MODEL_AUTO_SWITCH) {
            modelSwitch.checked = settings.MODEL_AUTO_SWITCH === 'true';
        }
        
        // 主提示词
        if (settings.MAIN_SYSTEM_PROMPT) {
            mainSystemPrompt.value = settings.MAIN_SYSTEM_PROMPT;
        }
        
        // 填充自定义提示词
        for (let i = 0; i < 5; i++) {
            const nameKey = `CUSTOM_PROMPT_NAME_${i}`;
            const contentKey = `CUSTOM_PROMPT_CONTENT_${i}`;
            
            if (settings[nameKey]) {
                customPromptNames[i].value = settings[nameKey];
            }
            
            if (settings[contentKey]) {
                customPromptContents[i].value = settings[contentKey];
            }
        }
        
        // 更新AI标签页中的自定义提示词按钮
        updateCustomPromptButtons();
        
        settingsStatus.textContent = '设置已加载';
        settingsStatus.style.color = '#52c41a';
        
        // 3秒后清除状态信息
        setTimeout(() => {
            settingsStatus.textContent = '';
        }, 3000);
        
    } catch (error) {
        console.error('加载设置失败:', error);
        settingsStatus.textContent = `加载设置失败: ${error.message}`;
        settingsStatus.style.color = '#ff4d4f';
    }
}

/**
 * 更新模型相关字段
 */
function updateModelFields(settings = {}) {
    const currentModel = modelSelect.value;
    const prefix = MODEL_PREFIXES[currentModel];
    
    if (!prefix) return;
    
    // 更新模型名称
    const modelNameKey = `${prefix}_MODEL_NAME`;
    modelName.value = settings[modelNameKey] || '';
    
    // 更新API密钥
    const apiKeyKey = `${prefix}_API_KEY`;
    apiKey.value = settings[apiKeyKey] || '';
    
    // 更新访问节点
    const endpointKey = `${prefix}_API_ENDPOINT`;
    apiEndpoint.value = settings[endpointKey] || '';
}

/**
 * 保存设置到服务器
 */
async function saveSettings() {
    try {
        settingsStatus.textContent = '正在保存设置...';
        settingsStatus.style.color = '#1890ff';
        
        const currentModel = modelSelect.value;
        const prefix = MODEL_PREFIXES[currentModel];
        
        // 收集设置数据
        const settings = {
            // 通用设置 - 当前选择的模型
            ACTIVE_MODEL: currentModel,
            MODEL_AUTO_SWITCH: modelSwitch.checked.toString(),
            MAIN_SYSTEM_PROMPT: mainSystemPrompt.value
        };
        
        // 添加模型特定配置
        settings[`${prefix}_MODEL_NAME`] = modelName.value;
        settings[`${prefix}_API_KEY`] = apiKey.value;
        settings[`${prefix}_API_ENDPOINT`] = apiEndpoint.value;
        
        // 收集自定义提示词
        for (let i = 0; i < 5; i++) {
            settings[`CUSTOM_PROMPT_NAME_${i}`] = customPromptNames[i].value;
            settings[`CUSTOM_PROMPT_CONTENT_${i}`] = customPromptContents[i].value;
        }
        
        // 发送到服务器
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const result = await response.json();
        
        settingsStatus.textContent = '设置已保存';
        settingsStatus.style.color = '#52c41a';
        
        // 更新AI标签页中的自定义提示词按钮
        updateCustomPromptButtons();
        
        // 3秒后清除状态信息
        setTimeout(() => {
            settingsStatus.textContent = '';
        }, 3000);
        
    } catch (error) {
        console.error('保存设置失败:', error);
        settingsStatus.textContent = `保存设置失败: ${error.message}`;
        settingsStatus.style.color = '#ff4d4f';
    }
}

/**
 * 更新AI标签页中的自定义提示词按钮
 */
function updateCustomPromptButtons() {
    const presetPrompts = document.querySelector('.preset-prompts');
    
    // 先移除所有现有的自定义按钮
    const existingCustomButtons = document.querySelectorAll('.custom-prompt-btn');
    existingCustomButtons.forEach(btn => btn.remove());
    
    // 添加有名称的自定义提示词按钮
    for (let i = 0; i < customPromptNames.length; i++) {
        const name = customPromptNames[i].value;
        const content = customPromptContents[i].value;
        
        if (name && content) {
            const btn = document.createElement('button');
            btn.className = 'prompt-btn custom-prompt-btn';
            btn.setAttribute('data-prompt', content);
            btn.textContent = name;
            
            presetPrompts.appendChild(btn);
            
            // 添加点击事件
            btn.addEventListener('click', () => {
                document.getElementById('mainPrompt').value = content;
            });
        }
    }
}

/**
 * 获取当前活跃模型的配置
 */
async function getActiveModelConfig() {
    const settings = await fetch('/api/settings').then(res => res.json());
    const activeModel = settings.ACTIVE_MODEL || 'deepseek';
    const prefix = MODEL_PREFIXES[activeModel];
    
    return {
        model: activeModel,
        modelName: settings[`${prefix}_MODEL_NAME`] || '',
        apiKey: settings[`${prefix}_API_KEY`] || '',
        apiEndpoint: settings[`${prefix}_API_ENDPOINT`] || '',
        autoSwitch: settings.MODEL_AUTO_SWITCH === 'true'
    };
}

/**
 * 测试API连接
 */
async function testApiConnection() {
    try {
        const currentModel = modelSelect.value;
        
        apiTestResult.textContent = '正在测试...';
        apiTestResult.style.color = '#1890ff';
        
        // 先保存当前设置
        await saveSettings();
        
        if (currentModel === 'zhipu') {
            // 测试智谱API
            const response = await fetch('/api/zhipu/test_connection');
            const result = await response.json();
            
            if (result.status === 'success') {
                apiTestResult.textContent = `✅ ${result.message}`;
                apiTestResult.style.color = '#52c41a';
            } else {
                apiTestResult.textContent = `❌ ${result.message}`;
                apiTestResult.style.color = '#ff4d4f';
            }
        } else {
            apiTestResult.textContent = `暂不支持测试 ${currentModel} 模型`;
            apiTestResult.style.color = '#faad14';
        }
        
        // 5秒后清除状态
        setTimeout(() => {
            apiTestResult.textContent = '';
        }, 5000);
        
    } catch (error) {
        console.error('API测试失败:', error);
        apiTestResult.textContent = `❌ 测试失败: ${error.message}`;
        apiTestResult.style.color = '#ff4d4f';
    }
}

// 导出函数，以便在其他地方使用
window.loadSettings = loadSettings;
window.saveSettings = saveSettings;
window.getActiveModelConfig = getActiveModelConfig; 