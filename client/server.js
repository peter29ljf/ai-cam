const https = require('https');
const fs = require('fs');
const path = require('path');
const express = require('express');

const app = express();
const PORT = 8443;

// SSL证书配置
const options = {
  key: fs.readFileSync('../ssl/key.pem'),
  cert: fs.readFileSync('../ssl/cert.pem')
};

// 静态文件服务
app.use(express.static(path.join(__dirname)));

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