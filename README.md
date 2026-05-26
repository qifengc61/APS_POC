# 智能排产系统

基于 **Python FastAPI + React + Google OR-Tools CP-SAT** 的智能生产排产系统（POC），覆盖从基础数据管理、MRP物料需求计划、任务自动生成到作业车间调度约束优化求解与结果可视化的全链路。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | Python 异步 Web 框架 |
| 优化引擎 | Google OR-Tools CP-SAT | 约束规划求解器，核心排产算法 |
| ORM | SQLAlchemy + Alembic | 数据库 ORM 与迁移 |
| 数据库 | MySQL 8.3 | 持久化存储（Docker） |
| 前端框架 | React 19 | 用户界面 |
| UI 库 | Ant Design 5 | 企业级 UI 组件 |
| 路由 | React Router 7 | 客户端路由 |
| 流程图 | @xyflow/react | 工艺路线 DAG 可视化编辑 |
| 图表 | Recharts | 统计图表展示 |
| 构建 | Vite 8 | 前端构建工具 |

## 快速启动

### 前置条件

- Docker Desktop（已安装）
- Conda（已安装 `smart-scheduling` 环境）
- Python 3.11+
- Node.js 20+

### 1. 启动 MySQL

```bash
cd 智能排产POC
docker compose up -d
```

### 2. 启动后端

```bash
conda activate smart-scheduling
cd backend
python main.py
```

后端运行在 `http://localhost:8000`，API 文档见 `http://localhost:8000/docs`。

### 3. 启动前端

```bash
conda activate smart-scheduling
cd frontend
npm run dev
```

前端运行在 `http://localhost:3000`。

### 4. 一键启动（Windows PowerShell）

```bash
docker compose up -d
Start-Process -NoNewWindow conda -ArgumentList "run -n smart-scheduling python main.py" -WorkingDirectory "backend"
Start-Process -NoNewWindow conda -ArgumentList "run -n smart-scheduling npm run dev" -WorkingDirectory "frontend"
```

## 系统架构

```
┌─────────────────────────┐
│   React (Vite) :3000    │  前端界面
│   Ant Design / Router   │
└───────────┬─────────────┘
            │  /api/* (proxy)
            ▼
┌─────────────────────────┐
│   FastAPI :8000         │  后端 API
│   CORS: all             │
└───────────┬─────────────┘
            │
  ┌─────────┼─────────┐
  ▼         ▼         ▼
┌──────┐ ┌──────┐ ┌──────────┐
│ API  │ │Services│ │Algorithm │
│Layer │ │MRP/   │ │OR-Tools  │
│11    │ │Solve  │ │Job-Shop  │
│Router│ │TaskGen│ │Scheduler │
└──┬───┘ └──┬───┘ └────┬─────┘
   │        │          │
   └────────┼──────────┘
            ▼
   ┌────────────────┐
   │  SQLAlchemy    │
   │  (pymysql)     │
   └───────┬────────┘
           ▼
   ┌────────────────┐
   │  MySQL 8.3.0   │
   │  DB: aps       │
   └────────────────┘
```

## 目录结构

```
智能排产POC/
├── docker-compose.yml              MySQL 容器配置
├── backend/
│   ├── main.py                     启动入口
│   ├── requirements.txt            Python 依赖
│   ├── alembic.ini                 数据库迁移配置
│   └── app/
│       ├── __init__.py             FastAPI 应用主体
│       ├── api/                    11 个 API 路由模块
│       │   ├── scheduling.py       快速排产调度
│       │   ├── material.py         物料 CRUD
│       │   ├── manufacture_bom.py  BOM CRUD
│       │   ├── process.py          工序 CRUD
│       │   ├── process_route.py    工艺路线 CRUD + DAG 校验
│       │   ├── production_resource.py  资源 CRUD
│       │   ├── work_calendar.py    工作日历 CRUD
│       │   ├── incoming_material_order.py  来料订单 CRUD
│       │   ├── production_order.py 生产订单 CRUD + 排产控制
│       │   ├── planning_strategy.py  排产策略 CRUD
│       │   └── smart_scheduling.py 智能排产（生成/进度/确认/预览）
│       ├── models/                 12 个 ORM 数据模型
│       │   ├── material.py         物料表
│       │   ├── manufacture_bom.py  制造BOM表
│       │   ├── process.py          工序表
│       │   ├── process_route.py    工艺路线表
│       │   ├── production_resource.py  生产资源表
│       │   ├── work_calendar.py    工作模式/工作日历/资源日历
│       │   ├── incoming_material_order.py  来料订单表
│       │   ├── production_order.py 生产订单表
│       │   ├── planning_strategy.py  排产策略表
│       │   ├── plan_task.py        排产任务表（正式+Pending）
│       │   ├── plan_task_order.py  任务-订单关联表（正式+Pending）
│       │   └── schemas.py          排产参数模型
│       ├── schemas/                12 个 Pydantic 数据校验
│       ├── services/               4 个业务服务
│       │   ├── mrp_service.py      MRP 物料需求计划
│       │   ├── task_generation_service.py  任务自动生成
│       │   ├── solve_service.py    异步求解编排
│       │   └── scheduling_service.py  排产调度服务
│       ├── algorithm/              3 个算法模块
│       │   ├── scheduler.py        班次排产模型
│       │   └── job_shop_scheduler.py  作业车间 CP-SAT 调度
│       ├── utils/                  3 个工具模块
│       │   ├── graph.py            图算法（拓扑排序/环检测）
│       │   └── time_calculator.py  工作日历时间计算
│       └── core/                   4 个核心模块
│           ├── config.py           配置管理
│           ├── database.py         数据库引擎
│           └── progress_tracker.py 异步进度追踪
└── frontend/
    ├── package.json                前端依赖
    ├── vite.config.js              Vite 配置（代理 /api → :8000）
    └── src/
        ├── router/index.jsx        路由配置（11 个路由）
        ├── api/api.js              API 封装
        ├── layouts/AppLayout.jsx   管理后台布局
        ├── pages/                  11 个页面
        │   ├── QuickSchedulingPage.jsx   快速排产（首页）
        │   ├── SchedulingPage.jsx        作业排产
        │   ├── MaterialPage.jsx          物料管理
        │   ├── BomPage.jsx               BOM 管理
        │   ├── ProcessPage.jsx           工序管理
        │   ├── ProcessRoutePage.jsx      工艺路线管理
        │   ├── ResourcePage.jsx          生产资源管理
        │   ├── CalendarPage.jsx          工作日历管理
        │   ├── IncomingOrderPage.jsx     来料订单管理
        │   ├── OrderPage.jsx             生产订单管理
        │   └── StrategyPage.jsx          排产策略配置
        └── components/             5 个组件
            ├── ParameterForm.jsx        排产参数表单
            ├── ProcessRouteEditor.jsx   DAG 编辑器（@xyflow/react）
            ├── ResultTable.jsx          排产结果表格
            ├── ResultCharts.jsx         排产结果图表
            └── SimpleGantt.jsx          简易甘特图
```

## 核心功能

### 一、基础数据管理

| 模块 | 功能 |
|------|------|
| 物料管理 | 物料 CRUD，支持原材料/半成品/成品类型，自制/外购来源，库存/安全库存/提前期/缓冲期 |
| BOM 管理 | 制造 BOM 维护，子件列表动态编辑 |
| 工序管理 | 工序定义，含产能格式（如 "5M" / "10/H" / "30M/P"）、ES/EE 工序关系、可用资源列表 |
| 工艺路线 | DAG 可视化编辑器（拖拽节点 + 连线），自动环检测与多终点校验 |
| 生产资源 | 资源 CRUD，含资源组/容量/产能/状态（正常/维护/报废） |
| 工作日历 | 工作模式 + 日历 + 资源日历三级管理，7位工作日位图，支持多优先级覆盖 |
| 来料订单 | 在途物料跟踪，预计到货时间，用于 MRP 库存齐套计算 |

### 二、生产管理

| 模块 | 功能 |
|------|------|
| 生产订单 | 订单生命周期管理，排产参与控制（Switch）、排序、补充订单 |
| 排产策略 | 可配置策略：方向（正向/逆向）、物料约束、订单排序规则、8 项优化目标权重 |

### 三、智能排产引擎

```
触发排产 → MRP 物料需求计划 → 任务自动生成 → CP-SAT 约束求解 → 结果预览 → 确认/放弃
```

1. **MRP 物料需求计划**：BOM 递归展开 → 库存齐套检查（在库+在途）→ 缺料 DAG 生成 → 自动创建补充生产订单

2. **任务自动生成**：缺料 DAG 拓扑排序 → 工艺路线 DAG 拓扑排序 → 任务链生成 → 前后置依赖建立（含跨物料依赖）

3. **作业车间调度 CP-SAT 模型**：
   - **决策变量**：每个任务的资源分配（`task_resource`）、开始时间（`task_start`）、结束时间（`task_end`）
   - **硬约束**：资源匹配、同资源不重叠（`AddNoOverlap`）、前后置时序约束
   - **软约束（可配置权重）**：最小化延期、尽早完成、最小化依赖间隔、均衡负载/任务数、按策略排序

4. **时间计算器**：工作日历感知的时间计算，支持三种产能格式解析（`5M`/`10/H`/`30M/P`）、ES/EE 工序关系处理

5. **异步求解**：后台任务执行，`ProgressTracker` 进度追踪，前端每 2 秒轮询进度

6. **双表确认机制**：排产结果先写入 Pending 表 → 预览 → 确认（原子转储至正式表）/ 放弃

### 四、快速排产

原有班次排产功能保留，支持按日产能规划排班组合。

## API 接口一览

| 路由前缀 | 功能 | 方法 |
|----------|------|------|
| `/api/schedule` | 快速排产计算 | POST |
| `/api/validate` | 排产参数校验 | POST |
| `/api/materials` | 物料 CRUD + 分页 | GET/POST/PUT/DELETE |
| `/api/manufacture-boms` | BOM CRUD + 分页 | GET/POST/PUT/DELETE |
| `/api/processes` | 工序 CRUD + 分页 | GET/POST/PUT/DELETE |
| `/api/process-routes` | 工艺路线 CRUD + DAG 校验 | GET/POST/PUT/DELETE |
| `/api/production-resources` | 生产资源 CRUD + 分页 | GET/POST/PUT/DELETE |
| `/api/work-modes` | 工作模式 CRUD | GET/POST/PUT/DELETE |
| `/api/work-calendars` | 工作日历 CRUD | GET/POST/PUT/DELETE |
| `/api/resource-calendars` | 资源日历 CRUD | GET/POST/PUT/DELETE |
| `/api/incoming-material-orders` | 来料订单 CRUD + 分页 | GET/POST/PUT/DELETE |
| `/api/production-orders` | 生产订单 CRUD + 参与控制 + 排序 | GET/POST/PUT/DELETE |
| `/api/planning-strategies` | 排产策略 CRUD + 启用控制 | GET/POST/PUT/DELETE |
| `/api/scheduling-rule/options` | 排序规则选项 | GET |
| `/api/smart-scheduling/generate` | 触发智能排产 | POST |
| `/api/smart-scheduling/plan/progress` | 查询排产进度 | GET |
| `/api/smart-scheduling/plan/pending/confirm` | 确认排产计划 | POST |
| `/api/smart-scheduling/plan/pending/cancel` | 放弃排产计划 | POST |
| `/api/smart-scheduling/preview/plan/tasks` | 预览任务列表 | POST |
| `/api/smart-scheduling/preview/plan/resource/gantt` | 预览甘特图数据 | POST |

完整 API 文档：`http://localhost:8000/docs`

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `jvs_material` | 物料表 |
| `jvs_manufacture_bom` | 制造BOM表 |
| `jvs_process` | 工序表 |
| `jvs_process_route` | 工艺路线表 |
| `jvs_production_resource` | 生产资源表 |
| `jvs_work_mode` | 工作模式表 |
| `jvs_work_calendar` | 工作日历表 |
| `jvs_resource_calendar` | 资源日历关联表 |
| `jvs_incoming_material_order` | 来料订单表 |
| `jvs_production_order` | 生产订单表 |
| `jvs_planning_strategy` | 排产策略表 |
| `jvs_plan_task` | 排产任务表（正式） |
| `jvs_plan_task_pending` | 排产任务表（待确认） |
| `jvs_plan_task_order` | 任务-订单关联表（正式） |
| `jvs_plan_task_order_pending` | 任务-订单关联表（待确认） |

## 使用流程

1. **配置基础数据** → 物料 → BOM → 工序 → 工艺路线 → 生产资源 → 工作日历
2. **创建生产订单** → 设置目标物料、数量、交期、优先级
3. **配置排产策略** → 选择排产方向、排序规则、优化权重
4. **触发智能排产** → 选择策略和订单 → 等待 MRP + 任务生成 + CP-SAT 求解
5. **预览结果** → 任务列表 / 甘特图 → 确认或放弃
6. **快速排产备选** → 使用原有班次排产快速验证

## 环境变量

通过 `backend/.env` 文件或系统环境变量配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MYSQL_HOST` | `localhost` | MySQL 主机 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_USER` | `root` | 数据库用户名 |
| `MYSQL_PASSWORD` | `root123` | 数据库密码 |
| `MYSQL_DATABASE` | `aps` | 数据库名 |

## 技术参考

- 技术报告：[技术报告.md](技术报告.md)
- 功能规格：[spec.md](.trae/specs/build-aps-phases-1-2-3/spec.md)
- 任务列表：[tasks.md](.trae/specs/build-aps-phases-1-2-3/tasks.md)
- 验证清单：[checklist.md](.trae/specs/build-aps-phases-1-2-3/checklist.md)
