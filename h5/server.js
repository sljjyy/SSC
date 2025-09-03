const http = require('http');
const fs = require('fs');
const path = require('path');

// 服务器端口
const PORT = 3000;

// 支持的文件类型
const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.wasm': 'application/wasm',
  '.txt': 'text/plain'
};

// 创建服务器
const server = http.createServer((req, res) => {
  console.log(`Request for ${req.url}`);
  
  // 默认为index.html
  let filePath = '.' + (req.url === '/' ? '/index.html' : req.url);
  
  // 检查文件是否存在
  fs.exists(filePath, (exists) => {
    if (!exists) {
      res.writeHead(404);
      res.end('File not found!');
      return;
    }
    
    // 如果是目录，尝试访问index.html
    if (fs.statSync(filePath).isDirectory()) {
      filePath += '/index.html';
    }
    
    // 读取文件
    fs.readFile(filePath, (err, content) => {
      if (err) {
        res.writeHead(500);
        res.end('Error loading file!');
        return;
      }
      
      // 设置响应头
      const ext = path.extname(filePath);
      res.writeHead(200, {
        'Content-Type': MIME_TYPES[ext] || 'application/octet-stream',
        'Access-Control-Allow-Origin': '*' // 允许跨域请求
      });
      
      // 发送文件内容
      res.end(content);
    });
  });
});

// 启动服务器
server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
});