# 快速启动指南

本文档记录了在当前设备（Windows）上快速启动智能排产系统的方法。

## 环境说明

| 组件 | 来源 | 路径 |
|------|------|------|
| Conda 环境 | Miniconda3 | `D:\miniconda3\envs\smart-scheduling` |
| Node.js 20 | Conda 安装 | `D:\miniconda3\envs\smart-scheduling\node.exe` |
| npm | Conda 安装 | `D:\miniconda3\envs\smart-scheduling\npm.cmd` |
| Python 3.11+ | Conda 安装 | `D:\miniconda3\envs\smart-scheduling\python.exe` |
| MySQL 8.3 | Docker | 容器名 `aps-mysql` |

## 启动步骤

### 1. 启动 MySQL 数据库

```powershell
cd d:\Desktop\智能排产\智能排产POC
docker compose up -d
```

### 2. 启动后端

```powershell
conda activate smart-scheduling
cd d:\Desktop\智能排产\智能排产POC\backend
pip install -r requirements.txt   # 首次运行或依赖有更新时执行
python main.py
```

后端运行在 **http://localhost:8000**，API 文档见 **http://localhost:8000/docs**。

### 3. 启动前端

> ⚠️ 重要：Node.js 安装在 Conda 环境中，不在系统 PATH 中，启动前需要手动设置 PATH。

```powershell
$env:PATH = "D:\miniconda3\envs\smart-scheduling;" + $env:PATH
cd d:\Desktop\智能排产\智能排产POC\frontend
npm run dev
```

前端运行在 **http://localhost:3000**。

### 一键启动（推荐）

需要分别打开两个 PowerShell 终端：

**终端 1 — 启动后端**：
```powershell
cd d:\Desktop\智能排产\智能排产POC
docker compose up -d
conda activate smart-scheduling
cd backend
python main.py
```

**终端 2 — 启动前端**：
```powershell
$env:PATH = "D:\miniconda3\envs\smart-scheduling;" + $env:PATH
cd d:\Desktop\智能排产\智能排产POC\frontend
npm run dev
```

## 启动后验证

| 服务 | 地址 | 预期 |
|------|------|------|
| 后端 API | http://localhost:8000 | JSON 响应 |
| Swagger 文档 | http://localhost:8000/docs | API 交互页面 |
| 前端界面 | http://localhost:3000 | 管理后台页面 |
| MySQL | localhost:3306 | `aps` 数据库可访问 |

## 常见问题

### 1. `ModuleNotFoundError: No module named 'pymysql'`

依赖未安装，执行：

```powershell
conda activate smart-scheduling
cd d:\Desktop\智能排产\智能排产POC\backend
pip install -r requirements.txt
```

### 2. `'npm' 不是内部或外部命令`

未设置 Conda 环境 PATH，执行：

```powershell
$env:PATH = "D:\miniconda3\envs\smart-scheduling;" + $env:PATH
```

### 3. MySQL 容器未启动

```powershell
docker compose up -d
```

### 4. 端口被占用

```powershell
# 查看占用端口 8000 的进程
netstat -ano | findstr :8000
# 查看占用端口 3000 的进程
netstat -ano | findstr :3000
```

## 停止服务

### 一键关闭（推荐）

在任意 PowerShell 终端中执行：

```powershell
# 杀占用8000端口(后端)和3000端口(前端)的进程
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | % { Stop-Process -Id $_.OwningProcess -Force }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | % { Stop-Process -Id $_.OwningProcess -Force }

# 停止 MySQL 容器
cd d:\Desktop\智能排产\智能排产POC
docker compose down

Write-Host "所有服务已停止" -ForegroundColor Green
```

### 手动逐个关闭

- **后端/前端**：在对应终端按 `Ctrl + C`；或 `Stop-Process -Id <PID> -Force`（先用 `netstat -ano | findstr :8000` 查 PID）
- **MySQL**：`docker compose down`（保留数据）；`docker compose down -v`（删除数据）
