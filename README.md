# 项目说明

## 版本记录
- v1.0.3：修复前端代理路径导致缩略图/原图 404 的问题；新增删除全部图片、添加图片按钮；完善图片列表实时刷新。
- v1.0.1：新增 图片管理功能，包括浏览、删除、替换、插入截图页面，并支持页码管理。

## 安装与使用指南

### 环境要求

- **前端**：Node.js v14+
- **后端**：Python 3.8+
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
- 前端：HTML5 + JavaScript
- 后端：Python + FastAPI + WebSockets
- 图像处理：OpenCV + MediaPipe
- 部署：云端服务器（如 AWS、GCP）

## 功能说明

### 现有功能
- **手部监控**：使用摄像头实时监控手部动作，检测到手部消失后进行截图。
- **截图保存**：将高清截图保存到指定目录，供后续处理使用。
- **图片管理与编辑**：浏览、插入、删除、替换截图及页码管理。

### 未来扩展功能

#### 1. 图片生成 PDF
- **功能描述**：将扫描的图片按顺序合并生成 PDF 文件。
- **扩展接口**：`pdf_generation.py` 模块中预留接口，用于接收图片列表并生成 PDF。

#### 2. OCR 转 Markdown
- **功能描述**：对图片进行 OCR 识别，将结果转换为 Markdown 格式，并传给大模型进行总结或对话。
- **扩展接口**：`ocr_processing.py` 模块中预留接口，用于 OCR 处理和 Markdown 转换。

#### 3. 生词表功能
- **功能描述**：收集扫描过程中识别的生词，生成生词表以供学习。
- **扩展接口**：`vocabulary_builder.py` 模块中预留接口，用于记录和管理生词。

#### 4. 与大模型交互
- **功能描述**：在网页中新增一个标签页，用户可以上传 PDF 和图片文件，与大模型进行讨论和交互。
- **前端实现**：
  - 新增标签页和文件上传控件。
  - 添加自定义 Prompt 按钮，支持一键发送常用 Prompt。
- **后端实现**：
  - 实现与大模型的 API 交互逻辑，处理前端请求并返回结果。

## 设计原则
- **模块化设计**：每个功能模块独立开发，互不干扰，便于后续扩展和维护。
- **接口预留**：在现有代码中预留接口和钩子，确保未来功能可以无缝集成。
- **文档记录**：在项目说明文档中详细记录未来功能需求和设计思路，便于后续开发人员理解和实现。

## 项目文件结构

```
project-root/
│
├── client/                      # 前端代码
│   ├── index.html               # 主页面
│   ├── direct_demo.html         # 本地模式页面
│   ├── test_camera.html         # 测试页面
│   ├── style.css                # 样式文件
│   ├── app.js                   # 前端逻辑
│   ├── imageManager.js          # 前端图片管理逻辑
│   ├── server.js                # HTTPS 前端服务器脚本
│   ├── package.json             # 依赖配置
│   └── package-lock.json        # 锁定依赖文件
│
├── server/                      # 后端代码
│   ├── main.py                  # FastAPI 主应用
│   ├── ssl_main.py              # HTTPS后端服务器脚本
│   ├── flip_monitor_mediapipe.py# 服务端监控脚本
│   ├── hand_detection.py        # 手部检测逻辑
│   ├── image_processing.py      # 图片管理模块
│   ├── ocr_processing.py        # OCR处理模块（预留）
│   ├── pdf_generation.py        # PDF生成模块（预留）
│   ├── vocabulary_builder.py    # 生词表模块（预留）
│   ├── model_interaction.py     # 大模型交互模块
│   ├── requirements.txt         # Python依赖
│   └── Dockerfile               # Docker配置
│
├── flip_monitor_mediapipe.py     # 本地模式脚本（客户端调用）
├── start_https.sh                # 启动HTTPS一键脚本
├── ssl/                          # 自签名证书目录
│   ├── cert.pem
│   └── key.pem
└── README.md                     # 项目说明文档
```

## 测试方案

### 前端测试（`tests/test_client.py`）

1. **摄像头访问测试**：
   - 确保 `getUserMedia` 能够正常访问摄像头。
   - 验证视频流在网页上正常显示。
   - **涉及文件**：`client/index.html`, `client/app.js`

2. **WebSockets 连接测试**：
   - 测试 WebSockets 连接的建立和断开。
   - 验证数据传输的完整性和稳定性。
   - **涉及文件**：`client/app.js`, `server/main.py`

3. **UI 交互测试**：
   - 测试用户界面的响应性和交互性。
   - 确保提示信息和错误信息正确显示。
   - **涉及文件**：`client/index.html`, `client/style.css`, `client/app.js`

4. **模型交互测试**：
   - 测试 `model_interaction.js` 模块：验证主提示词设置、常用 Prompt 按钮触发的请求是否正确发送。
   - 测试文件上传组件：前端上传 PDF/图片文件逻辑是否正常。
   - **涉及文件**：`client/model_interaction.js`, `client/index.html`, `client/app.js`

### 后端测试（`tests/test_server.py`）

1. **API 端点测试**：
   - 测试 FastAPI 端点的可用性和响应时间。
   - 验证 WebSockets 端点的连接和数据接收。
   - **涉及文件**：`server/main.py`

2. **手部检测测试**：
   - 使用模拟视频流测试手部检测的准确性。
   - 验证手部消失时高清截图的触发和保存。
   - 验证截图文件夹创建及文件写入。  
   - **涉及文件/目录**：`server/hand_detection.py`, `server/main.py`, `shots/`  

3. **性能测试**：
   - ...

4. **大模型 API 测试**：
   - 模拟 Deepseek API 服务，验证 `model_interaction.py` 构造请求和处理响应是否正确。
   - **涉及文件**：`server/model_interaction.py`, `server/main.py`

### 集成测试（`tests/test_integration.py`）

1. **端到端测试**：
   - 从前端到后端的完整数据传输链路测试。
   - 验证系统在真实环境下的整体表现。
   - 检查截图目录及图片文件生成。
   - **涉及文件/目录**：`client/index.html`, `client/app.js`, `server/main.py`, `shots/`

2. **延时测试**：
   - 测试从视频采集到截图保存的总延时。
   - 优化传输和处理流程，降低延时。
   - **涉及文件**：`client/app.js`, `server/main.py`

3. **异常处理测试**：
   - 模拟网络中断、摄像头故障等异常情况。
   - 验证系统的异常处理能力和恢复能力。
   - **涉及文件**：`client/app.js`, `server/main.py`

4. **模型交互集成测试**：
   - 前端上传截图并设置主提示词，后端调用 Deepseek API 并返回结果，验证 UI 正确展示。
   - **涉及文件/目录**：`client/model_interaction.js`, `server/model_interaction.py`, `shots/`

## 当前开发功能
- 大模型交互（Deepseek API）
  - 模块：`client/model_interaction.js`  # 大模型交互逻辑（使用 Deepseek API）
  - 功能：收集已截取的高清图片，按顺序编页码，发送到 Deepseek API，获取分析结果和相关提示词
  - UI 支持：
    - 主提示词设置
    - 常用 Prompt 按钮，一键发送自定义或预设 Prompt 

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
  - success_code.md
  - start_https.sh
  - stop_all_servers.sh
  - flip_monitor_mediapipe.py
  - mediapipe_demo.py
  - server/shots/（截图目录）
- 这样可避免隐私泄露和无用文件污染代码仓库，便于团队协作和部署。 