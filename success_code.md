## HTTPS服务配置方案

### 主要组件

1. **SSL证书**：
   - 使用OpenSSL生成自签名证书
   - 证书位置：`/ssl/cert.pem` 和 `/ssl/key.pem`

2. **前端HTTPS服务器**：
   - 使用Node.js的HTTPS模块和Express实现
   - 代码路径：`client/server.js`
   - 端口：8443

3. **后端HTTPS服务器**：
   - 使用uvicorn的SSL配置实现
   - 代码路径：`server/ssl_main.py`
   - 端口：8000

4. **WebSocket安全连接**：
   - 修改前端连接，根据当前页面协议自动切换ws/wss
   - 代码路径：`client/app.js`的getServerUrl函数

5. **一键启动脚本**：
   - 脚本路径：`/start_https.sh`
   - 自动启动前后端HTTPS服务器
   - 显示本地IP方便远程访问

### 关键改动

```javascript
// 前端WebSocket连接适配HTTPS
const getServerUrl = () => {
    const hostname = window.location.hostname;
    // 根据当前协议选择ws或wss
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${protocol}://${hostname}:8000/ws`;
};
```

### 使用方法

1. 执行脚本 `./start_https.sh`
2. 访问 `https://localhost:8443` 或 `https://[本地IP]:8443`

### 运行注意事项

- 初次访问需确认安全例外（因为是自签名证书）
- 确保防火墙允许8000和8443端口流量

## HTTPS远程访问优化方案

### 修复问题与优化

1. **脚本路径问题修复**：
   ```bash
   # 获取项目根目录的绝对路径
   PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
   
   # 使用绝对路径确保目录切换正确
   cd "${PROJECT_DIR}/server" && python3 ssl_main.py &
   cd "${PROJECT_DIR}/client" && node server.js &
   ```

2. **增强SSL证书配置**：
   ```bash
   # 生成包含IP地址的SSL证书
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
     -subj "/CN=localhost" -addext "subjectAltName = IP:192.168.1.101,DNS:localhost"
   ```

3. **服务管理优化**：
   ```bash
   # 停止现有服务
   pkill -f "python.*http.server" || true
   pkill -f "python.*main.py" || true
   pkill -f "node.*server.js" || true
   ```

### 远程访问成功要点

1. **防火墙配置**：确保macOS防火墙允许8000和8443端口的入站连接
2. **同一网络**：确保客户端与服务器在同一局域网内
3. **证书信任**：首次访问时需在浏览器中添加安全例外
