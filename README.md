# 项目说明

> **警告：后端仅支持 Python 3.9 版本，其他版本可能导致兼容性问题**

## 版本记录
- v1.0.8 增加一件图片转md功能
- v1.0.4：与大模型交互功能，但有缺陷，图片管理功能失效。
- v1.0.3：修复前端代理路径导致缩略图/原图 404 的问题；新增删除全部图片、添加图片按钮；完善图片列表实时刷新。
- v1.0.1：新增 图片管理功能，包括浏览、删除、替换、插入截图页面，并支持页码管理。

## 安装与使用指南

### 环境要求

- **前端**：Node.js v14+
- **后端**：Python 3.9（仅支持 3.9 版本）
- **系统**：支持 macOS, Linux 或 Windows
- **浏览器**：Chrome, Firefox, Safari 等现代浏览器

### 安装步骤

1. **克隆仓库**

   ```bash
   git clone https://github.com/peter29ljf/ai-cam.git
   cd ai-cam
   ```

2. **安装后端依赖**

   ```bash
   cd server
   pip install -r requirements.txt
   ```

3. **安装前端依赖**

   ```bash
   cd ../client
   npm install
   ```

4. **生成 SSL 证书**（参见下方 "SSL 证书生成说明"）

### 启动服务

1. **一键启动（推荐）**

   ```bash
   ./start_https.sh
   ```
   
   > 注意：首次运行可能需要 `chmod +x start_https.sh` 授予执行权限

2. **手动启动**

   如需单独启动后端：
   ```bash
   cd server
   python ssl_main.py
   ```

   如需单独启动前端：
   ```bash
   cd client
   node server.js
   ```

3. **停止服务**

   ```bash
   ./stop_all_servers.sh
   ```

### 使用方法

1. **访问应用**
   - 本地访问：https://localhost:8443
   - 远程访问：https://[您的IP地址]:8443

2. **功能说明**
   - **实时监控**：启动摄像头并监控手部动作
   - **图片管理**：查看、编辑和管理截图
   - **AI 交互**：上传文件与 AI 进行交互讨论

3. **操作流程**
   - 点击"开始监控"进入摄像头模式
   - 手部出现→消失后自动截图并保存
   - 切换到"图片管理"标签查看或编辑已保存的截图
   - 使用"删除"、"替换"、"在后插入"等功能管理图片
   - 点击"查看原图"可在新窗口中查看高清原图

### 常见问题

1. **无法访问摄像头**
   - 确保已授予浏览器摄像头权限
   - 使用 HTTPS 协议访问（非本地环境必须）
   - 如仍有问题，尝试使用本地模式 `direct_demo.html`

2. **HTTPS 证书警告**
   - 属于正常现象（自签名证书）
   - 点击"高级"→"继续访问"（具体提示因浏览器而异）

3. **端口占用冲突**
   - 使用 `stop_all_servers.sh` 停止旧进程
   - 修改 `start_https.sh` 中的端口号（如需更改）

4. **模块未找到错误**
   - 错误: `Error: Cannot find module 'http-proxy-middleware'`
   - 原因: 前端服务中使用了 `http-proxy-middleware`，但未安装该依赖
   - 解决办法:
     ```bash
     cd client
     npm install http-proxy-middleware --save
     ```
     然后重新运行 `./start_https.sh`

## 目标
实现一个基于云端的手部监控系统，使用低画质视频流进行实时监控，高清画质进行截图，支持后续的 OCR 处理。

## 技术栈
- 前端：HTML5 + JavaScript + Node.js
- 后端：Python + FastAPI + WebSockets
- 图像处理：OpenCV + MediaPipe
- 部署：云端服务器（如 AWS、GCP）

### 依赖清单
#### 前端（client/package.json）

| 依赖名称               | 版本             |
| ---------------------- | ---------------- |
| express                | ^5.1.0           |
| http-proxy-middleware  | ^3.0.5           |

#### 后端（server/requirements.txt）

| 依赖名称             | 版本              |
| -------------------- | ----------------- |
| fastapi              | 0.103.1           |
| uvicorn              | 0.23.2            |
| websockets           | 11.0.3            |
| opencv-python        | 4.8.0.76          |
| mediapipe            | 0.10.7            |
| python-multipart     | 0.0.6             |
| httpx                | 0.25.0            |
| pillow               | 10.0.1            |
| openai               | >=1.0.0           |
| zhipuai              | >=2.0.0           |

## 功能说明

### 核心功能
- **文字提取（extract）**：从 `shots/` 目录中按 UI 顺序重命名图片，分批调用大模型 API 提取文字，并缓存为 JSON 和临时 Markdown 文件 `temp/temp.md`。
- **文档汇总（summary）**：基于提取的 Markdown 文件调用 Active Model（智谱或 LM Studio v3）生成完整 Markdown 文档，输出到 `output/` 并自动清理临时文件。
- **模型交互**：可配置使用智谱 `glm-4v-plus` 模型或 LM Studio 自托管模型，支持 JS API 或 Python SDK。
- **缓存与降级**：未配置或调用智谱 API 时自动降级到 LM Studio API；缓存文件夹 `temp/` 用于存储提取中间数据。

### 扩展功能
- **OCR 转 Markdown**（预留）：`ocr_processing.py` 中的接口将图片 OCR 转为 Markdown 文本。
- **PDF 生成**（预留）：`pdf_generation.py` 接口可将多张图片按顺序打包生成 PDF。
- **生词表**（预留）：`vocabulary_builder.py` 用于收集关键术语和生词，并生成学习词表。

## 设计原则
- **模块化设计**：每个功能模块独立开发，互不干扰，便于后续扩展和维护。
- **接口预留**：在现有代码中预留接口和钩子，确保未来功能可以无缝集成。
- **文档记录**：在项目说明文档中详细记录未来功能需求和设计思路，便于后续开发人员理解和实现。

## 项目文件结构

```plaintext
project-root/                     # 仓库根目录
│
├── client/                       # 前端代码
│   ├── index.html                # 主页面
│   ├── direct_demo.html          # 本地模式页面
│   ├── test_camera.html          # 测试页面
│   ├── style.css                 # 样式文件
│   ├── app.js                    # 前端逻辑
│   ├── imageManager.js           # 图片管理逻辑
│   ├── settingsManager.js        # 配置管理逻辑
│   ├── server.js                 # HTTPS 前端代理服务器
│   ├── package.json              # 前端依赖配置
│   ├── package-lock.json         # 前端依赖锁定
│   └── node_modules/             # 前端依赖目录
│
├── server/                       # 后端代码
│   ├── main.py                   # FastAPI 主应用
│   ├── ssl_main.py               # HTTPS 后端服务器脚本
│   ├── image_processing.py       # 图片管理 API 路由模块
│   ├── process_images.py         # 图片文字提取与文档生成脚本
│   ├── zhipu_api.py              # 智谱 API 多模态/纯文本交互模块
│   ├── settings_api.py           # 系统配置 API 模块
│   ├── hand_detection.py         # 手部检测模块
│   ├── test_hand_detection.py    # 手部检测测试脚本
│   ├── requirements.txt          # Python 依赖 (仅 Python 3.9)
│   ├── temp/                     # 临时目录 (缓存、MD 等)
│   └── shots/                    # 截图存储目录
│
├── output/                       # 文档生成输出目录
│   └── <文档文件夹>               # 输出的 Markdown 文档文件夹
│
├── ssl/                          # 自签名证书目录
│   ├── cert.pem
│   └── key.pem
│
├── start_https.sh                # 一键启动脚本
├── stop_all_servers.sh           # 停止所有服务脚本
├── .gitignore                    # Git 忽略配置
├── .cursorrules                  # Cursor AI 本地规则配置
└── README.md                     # 项目说明文档
```

## 当前开发功能
- 大模型交互（Deepseek API）
  - 模块：`client/ai_interaction.js`、`server/model_interaction.py`
  - 功能：
    - API 提供商选择与 API Key 输入
    - 主 Prompt 与常用 Prompt 管理
    - 文字对话与图像交互（支持单图或多图）
    - 语音交互（TTS 文本转语音 & STT 语音识别）
  - UI 支持：
    - 设置页面：配置 API、主 Prompt、常用 Prompt
    - AI 交互页面：聊天输入框、上传/选择图片按钮、常用 Prompt 快捷按钮
- 已知缺陷：图片管理功能再次失效，待修复。

## HTTPS安全访问模式（远程访问摄像头）

为了解决远程访问时摄像头无法使用的问题，我们提供了HTTPS访问模式。浏览器要求在非localhost环境下，必须使用HTTPS协议才能访问摄像头等设备。

### 使用方法

1. 确保已生成SSL证书（首次运行会自动生成）
2. 执行启动脚本：
   ```bash
   ./start_https.sh
   ```
3. 通过以下地址访问：
   - 本地访问：https://localhost:8443
   - 远程访问：https://[您的IP地址]:8443

### 注意事项

- 首次访问会出现安全警告（因为使用自签名证书），请点击"高级"然后选择"继续访问"
- 确保防火墙未阻止8000和8443端口
- 如果仍然无法访问摄像头，可以尝试使用本地模式（direct_demo.html） 

## SSL 证书生成说明

首次使用需要生成 SSL 证书，请按以下步骤操作：

1. **创建 SSL 目录**：
   ```bash
   mkdir -p ssl
   ```

2. **生成自签名证书**：
   ```bash
   cd ssl
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
   -subj "/CN=localhost" -addext "subjectAltName = IP:192.168.1.101,DNS:localhost"
   ```
   > 注意：请将 IP 地址替换为您的本地 IP

3. **证书权限设置**（如需要）：
   ```bash
   chmod 600 key.pem cert.pem
   ```

生成的证书会在首次访问 HTTPS 链接时提示不安全，请在浏览器中添加例外。
证书有效期为 1 年，到期后需重新生成。

## 图片管理与编辑
- **图片管理与编辑**：
  - 浏览、插入、删除、替换截图及页码管理。
  - 支持图片缩略图展示，移动端自适应，操作按钮横向排列，触控友好。
  - 每张图片均可一键"查看原图"，新窗口打开高清大图。
  - 操作按钮包括：删除、替换、在后插入、查看原图，均有高对比度配色和圆角设计，适合手机端操作。 

## 文件与隐私管理

- 以下本地脚本和文档已加入 `.gitignore`，不会被纳入版本控制：

- 这样可避免隐私泄露和无用文件污染代码仓库，便于团队协作和部署。 