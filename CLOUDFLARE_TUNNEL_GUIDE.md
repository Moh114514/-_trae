# 🌐 Cloudflare Tunnel 快速开始指南

## 📋 前置要求

### 1. 安装 cloudflared

**选项 A: 使用 npm（推荐）**
```bash
npm install -g cloudflared
```

**选项 B: 官方下载**
访问 https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

**验证安装**
```bash
cloudflared --version
```

---

## 🚀 快速启动

### 方式 1: 一键启动前后端穿透（推荐）

```bash
双击运行: start-cloudflare-tunnel.bat
```

✅ **会自动：**
- 检查 cloudflared 是否安装
- 检查本地服务是否运行
- 启动两个穿透窗口（前端 + 后端）
- 显示分配的 Tunnel URL

---

### 方式 2: 分别启动

**仅启动前端穿透：**
```bash
双击运行: start-cloudflare-frontend.bat
```

**仅启动后端穿透：**
```bash
双击运行: start-cloudflare-backend.bat
```

---

### 方式 3: 命令行启动

**前端穿透：**
```bash
cloudflared tunnel --url http://localhost:3000
```

**后端穿透：**
```bash
cloudflared tunnel --url http://localhost:8001
```

---

## 📝 获取分配的 URL

启动穿透后，终端会输出类似内容：

```
Your quick tunnel has been created! Visit it at:
https://your-random-subdomain.trycloudflare.com
```

记下这个 URL，这就是您的 Tunnel URL！

---

## 🔧 配置前端

获取到后端的 Tunnel URL 后，更新配置文件：

**文件:** `BEIMS建筑能源智能管理系统/frontend/dist/config.js`

```javascript
var backendURL = 'https://your-backend-tunnel-url.trycloudflare.com';
//                ↑ 替换为您的后端 Tunnel URL
```

**例如：**
```javascript
var backendURL = 'https://acid-focal-affair-adds.trycloudflare.com';
```

---

## 📊 Tunnel 管理

### 查看所有活跃的 Tunnel

```bash
cloudflared tunnel list
```

### 获取 Tunnel 详细信息

```bash
cloudflared tunnel info beims-tunnel
```

### 删除 Tunnel

```bash
cloudflared tunnel delete beims-tunnel
```

---

## 🔐 持久化 URL（高级）

默认情况下，每次运行 `cloudflared tunnel --url` 都会分配一个新的随机 URL。

要获得**永久相同的 URL**，需要创建命名 Tunnel：

### 1. 创建命名 Tunnel

```bash
cloudflared tunnel create beims-tunnel
```

第一次运行会：
- 生成凭证文件：`%USERPROFILE%\.cloudflared\beims-tunnel.json`
- 创建 Tunnel

### 2. 使用配置文件启动

```bash
cloudflared tunnel run --config-file cloudflare-tunnel-config.yml
```

或使用我们的脚本：
```bash
双击运行: start-cloudflare-config.bat
```

**优势：**
- ✅ URL 保持不变
- ✅ 支持多个服务绑定
- ✅ 更灵活的配置

---

## 🧪 测试连接

### 测试前端

打开浏览器，访问：
```
https://your-frontend-tunnel-url.trycloudflare.com
```

### 测试后端

在浏览器或 curl 中访问：
```bash
curl https://your-backend-tunnel-url.trycloudflare.com/health
```

---

## ⚠️ 常见问题

### Q1: 提示 "cloudflared: command not found"

**解决：** 重新安装 cloudflared
```bash
npm install -g cloudflared
```

### Q2: "Connection refused" 或无法连接本地服务

**检查清单：**
- [ ] 前端服务是否在运行？ (端口 3000)
- [ ] 后端服务是否在运行？ (端口 8001)
- [ ] 本地防火墙是否阻止？

### Q3: URL 每次都不一样

**这是正常的。**

使用 `cloudflared tunnel` 快速命令每次都分配新 URL。
要获得永久 URL，需要创建命名 Tunnel（见上面的"持久化 URL"部分）。

### Q4: Tunnel 速度慢

**优化建议：**
- 选择距离最近的 Cloudflare 数据中心
- 增加 num-workers：`num-workers: 20`
- 检查网络延迟：`ping 1.1.1.1`

### Q5: 如何同时穿透前后端但用同一个 URL？

**需要反向代理配置：**
- 使用 nginx 或 Apache
- 在代理层区分请求路径
- 例如：`/api/*` 转发到后端，其他转发到前端

---

## 🎯 推荐工作流

### 开发阶段

1. 启动本地前后端服务
2. 运行 `start-cloudflare-tunnel.bat`
3. 获取分配的 URL
4. 更新 `config.js` 中的后端 URL
5. 测试功能

### 部署阶段

1. 创建命名 Tunnel 获得永久 URL
2. 将 URL 记录到文档
3. 配置自动启动脚本
4. 监控 Tunnel 连接状态

---

## 📚 更多资源

- **官方文档**: https://developers.cloudflare.com/cloudflare-one/
- **Tunnel 配置**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/
- **快速开始**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/

---

## 📞 获取帮助

如果遇到问题，请检查：
1. cloudflared 是否正确安装
2. 本地服务是否运行
3. 网络连接是否正常
4. Cloudflare 官方文档

✅ 祝您使用愉快！
