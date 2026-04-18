# stock_agent_v1

一个 A 股实时分析项目，前端使用 Next.js 14，后端使用 FastAPI，支持个股行情、分时/K 线、资金流、市场概览和 WebSocket 推送。

## 项目结构

- `backend/`: FastAPI 服务、数据源聚合、指标和评分逻辑
- `frontend/`: Next.js 前端界面

## 环境要求

- Python 3.10 及以上
- Node.js 20 及以上
- npm 10 及以上

Redis 和 Tushare Token 都是可选项，不配置也可以启动项目并查看主要 UI。

## 克隆后如何启动

### 1. 启动后端

在项目根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
python backend\main.py
```

说明：

- 后端默认运行在 `http://localhost:8000`
- 接口文档地址是 `http://localhost:8000/docs`
- 后端环境变量统一使用 `STOCK_AGENT_` 前缀，避免与系统里的 `DEBUG`、`PORT` 等通用变量冲突

如果你使用 macOS 或 Linux，把激活虚拟环境的命令改成：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 启动前端

打开第二个终端，在项目根目录执行：

```powershell
Copy-Item frontend\.env.example frontend\.env.local
cd frontend
npm install
npm run dev
```

说明：

- 前端默认运行在 `http://localhost:3000`
- 默认会请求 `http://localhost:8000` 的后端接口
- 如果后端改了端口，请同步修改 `frontend/.env.local`

## 常用检查

前端类型检查：

```powershell
cd frontend
npm run type-check
```

前端 lint：

```powershell
cd frontend
npm run lint
```

前端生产构建：

```powershell
cd frontend
npm run build
```

## 提交说明

仓库已经配置忽略本地依赖、构建产物、虚拟环境和日志文件。提交代码时只需要提交源码、配置模板和锁文件，不要提交以下内容：

- `frontend/node_modules`
- `frontend/.next`
- `.venv`
- `.tools`
- `__pycache__`
- 本地日志文件
