# LogTail - 日志实时查看工具

一个基于 Web 的日志实时监控工具，支持多服务器 SSH 连接，可以像 `tail -f` 一样实时查看日志文件。

## 功能特性

- ✅ 多服务器管理
- ✅ 目录浏览和文件选择
- ✅ 实时日志监控（类似 `tail -f`）
- ✅ 日志高亮显示（ERROR/WARN/INFO）
- ✅ WebSocket 实时推送
- ✅ SSH 密钥/密码认证
- ✅ 简洁的 UI 界面

## 系统架构

```
┌─────────────┐      HTTP/WebSocket     ┌──────────────┐      SSH       ┌─────────────┐
│   Browser   │ ◄─────────────────────► │  Web Server  │ ◄───────────►  │  远程服务器  │
│  (前端 UI)   │                        │  (Python)    │              │  (日志文件)  │
└─────────────┘                        └──────────────┘              └─────────────┘
```

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install aiohttp paramiko
```

### 2. 配置服务器信息

复制配置文件模板：

```bash
cp config.example.json config.json
```

编辑 `config.json`，填入服务器信息：

```json
{
  "servers": [
    {
      "id": "server1",
      "name": "应用服务器 1",
      "host": "192.168.0.10",
      "port": 22,
      "username": "root",
      "password": "你的密码",
      "key_file": "",
      "base_path": "/data/logs"
    }
  ]
}
```

**认证方式：**
- 密码认证：填写 `password` 字段
- 密钥认证：填写 `key_file` 字段（SSH 私钥文件路径）

### 3. 启动服务

```bash
python server.py
```

启动后会显示：
```
LogTail 服务器启动中...
访问地址：http://localhost:8080
```

### 4. 访问应用

打开浏览器访问：http://localhost:8080

## 使用说明

### 4.1 选择服务器

在页面顶部的下拉菜单中选择要连接的服务器。

### 4.2 浏览目录

- 左侧面板显示服务器上的目录结构
- 点击目录可以展开查看子目录
- 点击文件可以选择该日志文件

### 4.3 实时监控

1. 选择要查看的日志文件
2. 点击"开始监控"按钮
3. 右侧面板会实时显示日志内容
4. 点击"停止监控"按钮停止查看

### 4.4 日志高亮

系统会自动识别日志级别并高亮显示：
- 🔴 红色：ERROR 级别
- 🟡 黄色：WARN 级别
- 🔵 蓝色：INFO 级别

## 目录结构

```
logtail/
├── index.html          # 前端页面
├── server.py           # 后端服务
├── config.json         # 配置文件（需自行创建）
├── config.example.json # 配置文件模板
├── requirements.txt    # Python 依赖
└── README.md          # 说明文档
```

## API 接口

### 获取文件列表

```
GET /api/files/list?server={server_ip}&path={directory_path}
```

响应：
```json
{
  "success": true,
  "data": [
    {
      "name": "api-gateway",
      "type": "directory",
      "permissions": "drwxr-xr-x",
      "size": "4096",
      "modified": "Mar 20 10:00"
    },
    {
      "name": "app.log",
      "type": "file",
      "permissions": "-rw-r--r--",
      "size": "1024",
      "modified": "Mar 20 10:00"
    }
  ]
}
```

### 实时查看日志

```
GET /api/tail?server={server_ip}&file={file_path}
```

WebSocket 连接，实时推送日志内容。

## 安全建议

1. **生产环境部署**：
   - 使用 SSH 密钥认证代替密码
   - 配置 HTTPS
   - 添加用户认证

2. **访问控制**：
   - 限制可访问的目录范围
   - 设置 IP 白名单
   - 添加登录验证

3. **密钥管理**：
   - 不要将密码明文存储在配置文件中
   - 使用环境变量或密钥管理服务

## 故障排查

### 无法连接服务器

1. 检查服务器 IP 和端口是否正确
2. 确认 SSH 服务是否运行
3. 检查防火墙设置
4. 验证用户名和密码/密钥

### 日志不显示

1. 检查文件路径是否正确
2. 确认文件是否存在且有读取权限
3. 查看后端日志是否有错误信息

### WebSocket 连接失败

1. 检查浏览器控制台错误
2. 确认防火墙允许 WebSocket 连接
3. 查看服务器日志

## 技术栈

- **前端**：原生 HTML/CSS/JavaScript
- **后端**：Python + aiohttp
- **SSH 连接**：paramiko
- **实时通信**：WebSocket

## 扩展功能

计划中的功能：
- [ ] 日志搜索和过滤
- [ ] 日志下载
- [ ] 多文件同时监控
- [ ] 日志统计分析
- [ ] 告警通知
- [ ] 历史记录

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请提交 Issue。
# 停止占用 18081 端口的进程
$process = netstat -ano | Select-String ":18081" | ForEach-Object { $_.ToString().Split(' ')[-1] }
if ($process) {
    taskkill /F /PID $process
    Write-Host "已停止占用 18081 端口的进程"
}

# 启动服务器
cd c:\Coding\logtail
python server.py