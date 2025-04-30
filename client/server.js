const https = require('https');
const fs = require('fs');
const path = require('path');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = 8443;

// SSL证书配置
const options = {
  key: fs.readFileSync('../ssl/key.pem'),
  cert: fs.readFileSync('../ssl/cert.pem')
};

// 静态文件服务
app.use(express.static(path.join(__dirname)));

// 代理 /shots 到后端 FastAPI
app.use('/shots', createProxyMiddleware({
  target: 'https://localhost:8000',
  changeOrigin: true,
  secure: false,
  logLevel: 'debug',
  pathRewrite: (path, req) => {
    if (path.startsWith('/shots/')) return path; // 已包含前缀
    return '/shots' + path; // 补上前缀
  }
}));

// 代理 /api 到后端 FastAPI
app.use('/api', createProxyMiddleware({
  target: 'https://localhost:8000',
  changeOrigin: true,
  secure: false,
  logLevel: 'debug',
  pathRewrite: (path, req) => {
    // 如果转发后的 path 已经包含 /api，则直接返回
    if (path.startsWith('/api/')) return path;
    // 否则给 path 前面补上 /api 前缀
    return '/api' + path;
  },
  onProxyReq: (proxyReq, req, res) => {
    console.log(`[Proxy /api] Received request: ${req.method} ${req.originalUrl}`);
    console.log(`[Proxy /api] Forwarding path to backend: ${proxyReq.path}`);
  },
  onError: (err, req, res) => {
    console.error('[Proxy /api] Error:', err);
    res.writeHead(500, {
      'Content-Type': 'text/plain',
    });
    res.end('Proxy error occurred.');
  }
}));

// 启动HTTPS服务器
const server = https.createServer(options, app);

server.listen(PORT, () => {
  console.log(`HTTPS服务器运行在 https://localhost:${PORT}`);
  console.log(`您也可以通过 https://${getLocalIP()}:${PORT} 访问`);
});

// 获取本地IP地址
function getLocalIP() {
  const { networkInterfaces } = require('os');
  const nets = networkInterfaces();
  
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      // 跳过内部接口和非IPv4地址
      if (net.family === 'IPv4' && !net.internal) {
        return net.address;
      }
    }
  }
  return 'localhost';
} 