# stock_agent_v1

一个 A 股实时分析项目，前端使用 Next.js 14，后端使用 FastAPI，支持个股行情、分时/K 线、资金流、市场概览和 WebSocket 推送。

## 当前结构

- `backend/`: FastAPI 服务、数据源聚合、指标和评分逻辑
- `frontend/`: Next.js 前端界面

## 运行前准备

- Python 3.10+
- Node.js 20+ 和 npm

## 后端启动

1. 进入项目根目录。
2. 将 [backend/.env.example](/d:/AI/stock_agent_v1/backend/.env.example) 复制为 `backend/.env`。
   说明: 后端环境变量统一使用 `STOCK_AGENT_` 前缀，避免和系统里的 `DEBUG`、`PORT` 等通用变量冲突。
3. 安装依赖:

```powershell
python -m pip install -r backend\requirements.txt
```

4. 启动服务:

```powershell
python backend\main.py
```

默认地址为 `http://localhost:8000`，接口文档在 `http://localhost:8000/docs`。

## 前端启动

1. 将 [frontend/.env.example](/d:/AI/stock_agent_v1/frontend/.env.example) 复制为 `frontend/.env.local`。
2. 安装依赖:

```powershell
npm install
```

3. 启动开发环境:

```powershell
npm run dev
```

前端默认地址为 `http://localhost:3000`。

## 常用检查

前端类型检查:

```powershell
npm run type-check
```

前端 lint:

```powershell
npm run lint
```
