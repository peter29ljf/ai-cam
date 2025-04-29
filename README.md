# 项目说明

## 版本记录
- v1.0.1：新增 图片管理功能，包括浏览、删除、替换、插入截图页面，并支持页码管理。

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
├── mp_shots/                     # 本地截图存储目录
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