# 🔧 脚本诊断流程图

## 当脚本出问题时用这个

### 问题诊断树

```
脚本双击没有反应
        ↓
    是否导出了错误信息？
    /                    \
 是/                      \否
  ↓                        ↓
看关键词                 检查磁盘空间
  ↓                        ↓
见 "错误代码表"          有空间吗？
                         /      \
                       是/      \否
                        ↓        ↓
                    继续诊断    清空磁盘
                                重试
```

---

## 从脚本的哪个阶段开始闪退？

### 情况 1：立即闪退（0-2秒）

**可能原因**：
- [ ] PowerShell 执行策略限制
- [ ] 文件路径不对
- [ ] 编码问题（UTF-8 BOM）

**诊断命令**：
```bash
# PowerShell 执行
Get-ExecutionPolicy
# 如果是 Restricted，执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**解决**：重新双击脚本

---

### 情况 2：检查 ngrok 时闪退

**可能原因**：
- [ ] ngrok 未安装
- [ ] ngrok 路径不在系统变量中

**诊断命令**：
```bash
# PowerShell 执行
where ngrok
# 如果提示"无法找到"，表示未安装
```

**解决**：
```bash
winget install ngrok
# 重启 PowerShell
# 再次检查
where ngrok
# 应该显示 ngrok 安装路径
```

---

### 情况 3：启动后端时闪退

**可能原因**：
- [ ] 后端代码有语法错误
- [ ] Python 环境问题
- [ ] 端口 8001 被占用

**诊断命令**：
```bash
# 检查端口占用
netstat -ano | findstr "8001"

# 如果有输出表示端口被占用，查看是什么进程
tasklist | findstr "PID"  (用上面查出的PID替换)
```

**解决**：
```bash
# 尝试杀死占用端口的进程
taskkill /PID ＜PID＞ /F

# 或者改变脚本使用的端口
# 编辑 start-tunnel-final.bat，改 8001 为其他端口，比如 8002
```

---

### 情况 4：启动前端时闪退

**可能原因**：
- [ ] npm 依赖未安装
- [ ] Node.js 版本过低
- [ ] 端口 3000 被占用

**诊断命令**：
```bash
# 检查 Node 版本
node --version
# 应该 >= 18.0

# 检查 npm
npm --version

# 检查 3000 端口
netstat -ano | findstr "3000"
```

**解决**：
```bash
# 重新安装依赖
cd Fuwu/BEIMS建筑能源智能管理系统/frontend
npm install

# 检查是否 package.json 有启动脚本
npm run dev
```

---

### 情况 5：ngrok 穿透时闪退

**可能原因**：
- [ ] Authtoken 未配置
- [ ] Authtoken 无效或过期
- [ ] 网络连接问题

**诊断命令**：
```bash
# 检查 authtoken
ngrok config check
# 应该显示: Authtoken saved to configuration file

# 手动测试 ngrok
ngrok http 3000
# 应该显示 Forwarding URL
```

**解决**：
```bash
# 重新配置 token
ngrok config add-authtoken ＜你的token＞

# 重新访问获取新 token（旧的可能过期）
# https://dashboard.ngrok.com/get-started/your-authtoken
```

---

## 错误代码表

| 错误代码 | 含义 | 解决方案 |
|---------|------|--------|
| 1 | 一般错误 | 查看详细错误信息，通常在脚本中写了原因 |
| 2 | 文件不存在 | 检查路径是否正确 |
| 5 | 访问被拒绝 | 以管理员身份运行 PowerShell |
| 127 | 命令找不到 | 检查程序是否已安装 |
| 111 | 连接被拒绝 | 检查服务是否运行，端口是否被占用 |
| 143 | 连接超时 | 检查网络连接，或者增加超时时间 |

---

## 快速自救清单

当任何脚本出问题时，按顺序执行：

- [ ] **Step 1**：检查所有程序是否已安装
  ```bash
  where ngrok
  where python
  where node
  ```

- [ ] **Step 2**：检查所有网络端口是否可用
  ```bash
  netstat -ano | findstr "8001"
  netstat -ano | findstr "3000"
  netstat -ano | findstr "4040"
  ```

- [ ] **Step 3**：检查磁盘空间是否足够
  ```bash
  get-volume C:
  ```

- [ ] **Step 4**：重启各项服务（手动）
  ```bash
  # 终止所有 Python 进程
  taskkill /IM python.exe /F
  
  # 终止所有 Node 进程
  taskkill /IM node.exe /F
  
  # 终止所有 ngrok 进程
  taskkill /IM ngrok.exe /F
  
  # 清空所有占用的端口
  # (上面命令执行后会自动释放)
  ```

- [ ] **Step 5**：重新运行脚本
  ```bash
  # 双击 start-tunnel-final.bat
  ```

---

## 完全手动模式（如果脚本还是不行）

如果脚本怎么都不行，你可以手动执行每个步骤：

### 第 1 步：启动后端
```bash
# PowerShell 进入项目目录
cd e:\openclaw-project\workspace\Fuwu\BEIMS建筑能源智能管理系统\backend

# 创建虚拟环境（如果还没有）
python -m venv venv
.\venv\Scripts\Activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 第 2 步：启动前端（新开一个 PowerShell）
```bash
# 进入前端目录
cd e:\openclaw-project\workspace\Fuwu\BEIMS建筑能源智能管理系统\frontend

# 安装依赖（如果还没有）
npm install

# 启动
npm run dev
```

### 第 3 步：启动 ngrok（新开一个 PowerShell）
```bash
ngrok http 3000
```

**如果这三个都能成功运行**，说明系统本身没问题，是脚本的问题（但这不应该发生，因为我已经修复了）。

---

## 最重要的 5 个诊断命令

记住这 5 个命令，99% 的问题都能解决：

```bash
# 1. 检查 ngrok
where ngrok

# 2. 检查 Python
where python

# 3. 检查 Node
where node

# 4. 检查端口
netstat -ano | findstr ":8001"

# 5. 重启一切
taskkill /IM python.exe /F
taskkill /IM node.exe /F
taskkill /IM ngrok.exe /F
```

执行这 5 个命令，99% 能解决问题。

---

## 还是不行？

如果以上都试过了，还是有问题，那你需要：

1. **截图脚本的错误信息**
2. **運行上面的 5 个诊断命令，截图结果**
3. **告诉我看到的具体错误**

给我这 3 份信息，我能更快地帮你解决问题。

---

**记住：9 成脚本问题都是因为缺少必要的程序或端口被占用。**

`where` + `netstat` 这两个命令往往能找到根本原因。

试试吧！
