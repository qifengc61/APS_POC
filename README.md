# 智能排产系统 V2.1

基于 **Google OR-Tools CP-SAT** 约束优化的智能生产排产系统，支持 **1~6 物料共享单条产线**，采用 Python FastAPI + React 前后端分离架构，数据持久化使用 MySQL。

## 项目结构

```
智能排产POC/
├── backend/                          # 后端 - FastAPI
│   ├── main.py                       # 入口文件 (uvicorn 启动)
│   └── app/
│       ├── __init__.py               # FastAPI 应用初始化、CORS、路由注册、数据库自动建表+迁移
│       ├── database.py               # SQLAlchemy 连接配置（MySQL，连接池）
│       ├── algorithm/
│       │   └── scheduler.py          # OR-Tools CP-SAT 排产算法核心（1~6物料）
│   ├── api/
│   │   ├── __init__.py           # API 路由注册（导出 scheduling router）
│   │   ├── scheduling.py         # 排产计算/校验/导出 API
│   │   ├── production_lines.py   # 产线 & 物料 CRUD API
│   │   └── delivery_plans.py     # 交货计划 CRUD API
│       ├── models/
│       │   ├── schemas.py            # Pydantic 数据模型（排产请求/响应）
│       │   └── db_models.py          # SQLAlchemy ORM 模型（4 张表）
│   └── services/
│       ├── __init__.py              # 服务层模块导出
│       └── scheduling_service.py # 排产业务逻辑 + Excel 导出
├── frontend/                         # 前端 - React + Vite
│   ├── index.html                    # HTML 入口
│   ├── package.json                  # 依赖及脚本配置
│   ├── vite.config.js                # Vite 配置（端口3000，/api 代理到8000）
│   └── src/
│       ├── main.jsx               # React 入口（createRoot 挂载）
│       ├── index.css              # 全局基础样式
│       ├── App.jsx                   # 根组件（左侧导航栏 + React Router）
│       ├── App.css
│       ├── api/api.js                # Axios 请求封装（14 个 API 函数）
│       ├── components/
│       │   ├── ParameterForm.jsx     # [V1遗留] 参数表单组件（当前未使用）
│       │   ├── ResultTable.jsx       # 排产结果明细表格（含导出按钮）
│       │   └── ResultCharts.jsx      # 趋势图表 + 统计卡片
│       └── pages/
│           ├── MaterialManagement.jsx # 物料管理页面
│           ├── LineManagement.jsx     # 产线管理页面
│           ├── DeliveryPlan.jsx       # 交货计划页面
│           └── Scheduling.jsx         # 排产计算页面
├── README.md
└── 导出模板.xlsx                      # Excel 导出模板
```

## 技术栈

| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | FastAPI | ^0.104.1 | REST API |
| 算法引擎 | Google OR-Tools CP-SAT | - | 约束求解 |
| 数据库 | MySQL | 8.0 | 数据持久化 |
| ORM | SQLAlchemy | ^2.0.23 | 数据库操作 |
| 前端框架 | React | ^19.2.6 | UI 构建 |
| 构建工具 | Vite | ^8.0.12 | 前端构建 |
| 路由 | React Router | ^7.15.1 | SPA 路由 |
| 图表 | Recharts | ^3.8.1 | 数据可视化 |
| 日期处理 | Day.js | ^1.11.20 | 日期格式化 |
| HTTP 客户端 | Axios | ^1.16.1 | API 请求 |
| 日历库 | chinese-calendar | - | 中国法定节假日/调休识别 |
| Excel 导出 | openpyxl | - | 排产结果导出 |

## 环境要求

- **Conda**（Miniconda 或 Anaconda）
- **Python**: 3.11（由 conda 环境管理）
- **Node.js**: >= 18（由 conda 环境管理）
- **Docker Desktop**（运行 MySQL 容器）

## 环境搭建

以下命令从项目根目录 `智能排产POC/` 执行。需先安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 和 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

### 1. 启动 MySQL 容器

```powershell
docker run -d --name scheduling-mysql -p 3307:3306 -e MYSQL_ROOT_PASSWORD=scheduling123 -e MYSQL_DATABASE=smart_scheduling -v scheduling-mysql-data:/var/lib/mysql mysql:8.0 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

> 如本地 3307 端口被占用，可改为其他端口，同时修改 `backend/app/database.py` 中的连接配置。

### 2. 创建 Conda 环境并安装依赖

```powershell
conda create -n smart-scheduling python=3.11 -y
conda run -n smart-scheduling pip install fastapi uvicorn ortools pydantic chinese-calendar python-multipart openpyxl requests sqlalchemy pymysql cryptography
conda run -n smart-scheduling conda install nodejs -y
conda run -n smart-scheduling --cwd frontend npm install
```

> 环境已存在时跳过 `conda create`，直接执行后续 `conda run` 命令即可。

## 启动方式

需先确保 Docker Desktop 和 MySQL 容器已启动，然后分别启动后端和前端，使用两个终端窗口。

| 服务 | 启动命令 | 地址 |
|------|---------|------|
| 后端 | `conda run -n smart-scheduling python backend/main.py` | http://localhost:8000 （API 文档：/docs） |
| 前端 | `conda run -n smart-scheduling --cwd frontend npm run dev` | http://localhost:3000 （/api 自动代理至后端） |

关闭服务：终端中 `Ctrl + C`

## 前端页面

系统采用左侧深色导航栏 + 多页面路由架构，共 4 个页面：

| 页面 | 路由 | 功能 |
|------|------|------|
| 🚀 排产计算 | `/` | 选择交货计划 + 配置算法参数 → 一键排产，查看结果表格/图表，导出 Excel |
| 📦 物料管理 | `/materials` | 管理物料基础信息（名称、编码、安全库存） |
| 🏭 产线管理 | `/lines` | 管理产线，为产线添加可生产物料及 8H 班产量 |
| 📋 交货计划 | `/delivery-plans` | 创建交货计划，选择产线 + 物料，输入每日交货量 |

### 使用流程

1. **物料管理**：添加物料（名称、编码、安全库存）
2. **产线管理**：创建产线，添加可生产物料并设定 8H 班产量
3. **交货计划**：选择产线，为每个物料输入每日交货量（空格分隔，自动校验天数匹配，自动计算总交货量）
4. **排产计算**：选择交货计划，调整算法配置，点击"开始排产"，查看结果并导出

## 数据库设计

使用 MySQL 持久化存储，SQLAlchemy ORM 自动建表。应用启动时自动执行增量迁移（新增字段、拆分表等），无需手动执行 SQL。主要迁移包括：为 `products` 表新增 `code` 列、删除 `initial_inventory` 列；将 `delivery_plans` 中的双物料字段拆分为独立的 `plan_materials` 子表。

### 表结构

#### `products` — 物料基础信息

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, 自增 | 主键 |
| name | String(100) | NOT NULL, UNIQUE | 物料名称 |
| code | String(50) | nullable, 非唯一 | 物料编码 |
| safety_stock | Float | NOT NULL, default=0 | 安全库存 |
| created_at | DateTime | default=now | 创建时间 |

#### `production_lines` — 产线

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, 自增 | 主键 |
| name | String(100) | NOT NULL, UNIQUE | 产线名称 |
| created_at | DateTime | default=now | 创建时间 |

#### `line_products` — 产线-物料关联

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, 自增 | 主键 |
| line_id | Integer | FK → production_lines, CASCADE | 所属产线 |
| product_id | Integer | FK → products, CASCADE | 关联物料 |
| initial_inventory | Float | NOT NULL, default=0 | 初期库存 |
| safety_stock | Float | NOT NULL, default=0 | 安全库存 |
| rated_output | Float | NOT NULL, default=0 | 8H 班产量 |

#### `delivery_plans` — 交货计划

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, 自增 | 主键 |
| name | String(200) | NOT NULL | 计划名称 |
| line_id | Integer | FK → production_lines, CASCADE | 所属产线 |
| start_date | Date | NOT NULL | 排产开始日期 |
| end_date | Date | NOT NULL | 排产结束日期 |
| created_at | DateTime | default=now | 创建时间 |

#### `plan_materials` — 交货计划物料明细

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | Integer | PK, 自增 | 主键 |
| plan_id | Integer | FK → delivery_plans, CASCADE | 所属交货计划 |
| line_product_id | Integer | FK → line_products, CASCADE | 关联的产线物料 |
| initial_inventory | Float | NOT NULL, default=0 | 初期库存 |
| total_delivery | Float | NOT NULL, default=0 | 总交货量 |
| daily_deliveries | Text | nullable | 每日交货量（JSON 数组字符串，如 `[125,55,220]`） |
| sort_order | Integer | NOT NULL, default=0 | 排序顺序 |

### 数据关系

```
products ──1:N──> line_products ──N:1──> production_lines
                                        │
delivery_plans ──1:N──> plan_materials ──N:1──> line_products
```

## API 接口

### 系统

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 系统信息（版本号） |

### 物料管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/lines/products` | 获取物料列表 |
| POST | `/api/lines/products` | 创建物料 |
| PUT | `/api/lines/products/{id}` | 更新物料（后端已实现，前端暂未使用） |
| DELETE | `/api/lines/products/{id}` | 删除物料 |

### 产线管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/lines` | 获取产线列表（含可生产物料） |
| POST | `/api/lines` | 创建产线（同时添加可生产物料及 8H 班产量，安全库存继承自物料基础信息） |
| DELETE | `/api/lines/{id}` | 删除产线（级联删除关联及交货计划） |

### 交货计划

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/delivery-plans` | 获取交货计划列表 |
| GET | `/api/delivery-plans/{id}` | 获取单个交货计划详情 |
| POST | `/api/delivery-plans` | 创建交货计划 |
| DELETE | `/api/delivery-plans/{id}` | 删除交货计划 |

#### 创建交货计划请求体

```json
{
  "name": "5月排产计划",
  "line_id": 1,
  "materials": [
    {
      "line_product_id": 1,
      "initial_inventory": 500,
      "daily_deliveries": "125 55 220 179 181 16 268 240 237 103 240 140 99 0 171 163 100 57 108 132 0 0 0 130 92 151 100 100 77 72 90",
      "total_delivery": 0
    },
    {
      "line_product_id": 2,
      "initial_inventory": 300,
      "daily_deliveries": "50 60 70 80 90 100 110 120 130 140 50 60 70 80 90 100 110 120 130 140 50 60 70 80 90 100 110 120 130 140 50",
      "total_delivery": 0
    }
  ],
  "start_date": "2026-05-01",
  "end_date": "2026-05-31"
}
```

> `daily_deliveries` 为空格分隔的每日交货量，数量必须与排产天数匹配，`total_delivery` 传入 0 时由后端自动求和计算。交货计划支持 **1~6 个物料**，且物料不能重复、必须属于指定产线。每个物料可单独指定 `initial_inventory`（初期库存）。

### 排产计算

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/schedule` | 直接传入参数执行排产计算 |
| POST | `/api/schedule/by-plan` | 通过交货计划 ID 执行排产计算 |
| POST | `/api/validate` | 参数可行性校验（仅校验产能是否足够，不执行求解） |
| POST | `/api/schedule/export` | 导出排产结果为 Excel 文件 |

#### by-plan 请求体

```json
{
  "delivery_plan_id": 1,
  "config": {
    "rest_day_weight": 50,
    "max_consecutive_work_days": 7,
    "max_time_seconds": 10
  }
}
```

### 响应体关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 是否找到可行解 |
| `message` | string | 结果描述信息（无解时包含失败原因说明） |
| `solver_status` | string | `"OPTIMAL"`（最优解） / `"FEASIBLE"`（可行解） |
| `solve_time` | float | 求解实际耗时（秒） |
| `daily_results` | array | 每日排产明细 |
| `daily_results[].date` | string | 日期（ISO 格式） |
| `daily_results[].is_holiday` | bool | 是否为法定假日或用户指定假日 |
| `daily_results[].is_rest` | bool | 是否为休息日 |
| `daily_results[].is_adjusted_workday` | bool | 是否为调休上班日 |
| `daily_results[].total_work_hours` | float | 当日产线总工时 |
| `daily_results[].products` | array | 当日各物料明细（数组，按物料顺序） |
| `daily_results[].products[].combo` | int | 班次组合编号（0~5） |
| `daily_results[].products[].shift1` | float | 班次1系数 |
| `daily_results[].products[].shift2` | float | 班次2系数 |
| `daily_results[].products[].shift_label` | string | 班次标签（如"1班+1班"） |
| `daily_results[].products[].prod1` | int | 班次1产量 |
| `daily_results[].products[].prod2` | int | 班次2产量 |
| `daily_results[].products[].prod_label` | string | 产量标签（如"200+100"） |
| `daily_results[].products[].work_hours` | float | 当日工时 |
| `daily_results[].products[].daily_output` | int | 当日产量 |
| `daily_results[].products[].daily_delivery` | int | 当日交货量 |
| `daily_results[].products[].closing_inventory` | int | 当日结存库存 |
| `daily_results[].products[].inventory_violation` | bool | 是否违反安全库存 |
| `total_production_days` | int | 产线运行天数（共享） |
| `rest_days_occupied` | int | 产线休息日占用天数（共享） |
| `num_products` | int | 物料数量 |
| `product_stats` | array | 各物料汇总统计（数组，按物料顺序） |
| `product_stats[].total_production_days` | int | 该物料独立生产天数 |
| `product_stats[].min_inventory` | int | 该物料最低库存 |
| `product_stats[].final_inventory` | int | 该物料期末库存 |
| `product_stats[].delivery_fulfilled` | bool | 该物料是否达到交货量 |
| `product_stats[].holiday_production_days` | int | 该物料休息日生产天数 |

### 算法配置参数

| 前端显示 | 默认值 | 可选范围 | 对应后端字段 | 映射规则 |
|---------|--------|---------|------------|---------|
| 规避休息日上班权重 | 50 | 0~100（每10一档） | `rest_day_weight` | 直接等于 |
| 最大连续工作天数 | 7 | 3~14天（每1天一档） | `max_consecutive_work_days` | 直接等于 |
| 求解限时 | 10s | 10~60s（每10秒一档） | `max_time_seconds` | 直接等于 |

## 算法说明

使用 Google OR-Tools CP-SAT 约束求解器，单阶段优化目标函数，多线程并行搜索（`num_workers = min(8, cpu_count)`）。

### 多物料共享产线模型

- **一条产线**同时生产 **1~6 个物料**，每天最多 **24 小时**（= 3.0 班，每班 8 小时）
- 最小分配单位 **4 小时**（= 0.5 班）
- 每个物料各有一个 **combo** 变量（0~5），各自独立决定当天的前后班次组合
- 所有物料的总工时 ≤ 24h（`sum(shift_i) ≤ 3.0` 班）
- 每个物料有**独立**的初期库存、安全库存、8H 班产量和每日交货量

### 班次模型

每个物料每天从 6 种班次组合中选择一种：

| combo | 班次1 | 班次2 | 标签 | 日产量（×8H班产量） | 工时（h） |
|-------|-------|-------|------|---------------------|----------|
| 0 | 0 | 0 | 休息 | 0 | 0 |
| 1 | 1.0 | 0 | 1班 | 1.0 | 8 |
| 2 | 1.0 | 0.5 | 1班+0.5班 | 1.5 | 12 |
| 3 | 1.0 | 1.0 | 1班+1班 | 2.0 | 16 |
| 4 | 1.5 | 1.0 | 1.5班+1班 | 2.5 | 20 |
| 5 | 1.5 | 1.5 | 1.5班+1.5班 | 3.0 | 24 |

### 硬约束

- **24h 共享工时约束**：`sum(shift_i) ≤ 3.0`（= 24h），每天所有物料的总工时不能超过 24h
- **库存平衡约束**：每个物料各自独立，每日结存库存 = 前日结存 + 当日产量 - 当日交货
- **库存安全约束**：每个物料各自独立，每日结存库存 ≥ 安全库存
- **连续工作约束**：不允许产线连续运行超过 `max_consecutive_work_days` 天（产线级别硬约束，任一物料生产即算产线运行）
- **可行性校验**（求解前预检查）：
  - 每个物料单独校验：最大产能 ≥ 净需求
  - 所有物料合计校验：总最大产能 ≥ 合计净需求

### 目标函数

最小化以下加权和（内部缩放因子 `scale=2`，将浮点数转为整数运算）：

| 惩罚项 | 内部权重 | 用户可配 | 作用范围 | 说明 |
|-------|---------|---------|---------|------|
| 过量生产惩罚 | 1 | 否 | **物料级**（求和） | 防止无限过量生产，每个物料各自计算 `期末库存-安全库存` 后加总 |
| 占用休息日惩罚 | 用户值×2 | 是（默认50） | **产线级**（共享） | 休息日产线有任一物料生产即计为 1 次占用 |
| 产量平滑惩罚 | 5 | 否 | **物料级**（求和） | 相邻两天 combo 等级差的绝对值之和，各物料独立计算后加总 |
| 长连续工作惩罚 | 60 | 否 | **产线级**（共享） | 连续工作 `max_consecutive_work_days-1` 天的窗口数（窗口长度为 `max_consecutive_work_days-1`，全为工作日时计数+1） |

#### 惩罚粒度说明

| 惩罚项 | 计算方式 |
|-------|---------|
| **物料级（求和）** | 各物料的指标独立计算，加总后计入目标函数 |
| **产线级（共享）** | 使用共享的 `is_work_day[i]` 布尔变量（当天任一物料开工即标记），指标在产线层面统一计算 |

### 日历识别

通过 `chinese_calendar` 库自动识别中国法定节假日、周末和调休上班日：

- **休息日判定**：`chinese_calendar.is_workday(d)` 返回 False 的日期，或用户自定义假日
- **法定假日标记**：`chinese_calendar.is_holiday(d)` 返回 True 的日期，或用户自定义假日
- **调休上班标记**：原本是周末（weekday ≥ 5）但 `chinese_calendar.is_workday(d)` 返回 True 的日期

### 交货量分配

- 每个物料可独立指定 `daily_deliveries` 参数（`[{"date": "YYYY-MM-DD", "quantity": N}, ...]` 格式），按指定日期和数量交货
- 未指定日期的交货量按整数均匀分配：`base = 剩余总量 // 未指定天数`，余数 `extra = 剩余总量 % 未指定天数`，前 `extra` 天交货 `base + 1`，其余天交货 `base`
- 通过交货计划创建时，前端输入空格分隔的每日交货量字符串，后端自动转为 JSON 数组存储

## 算法优化

模型构建采用以下优化手段加速求解：

- **AddElement 约束**：使用 `model.AddElement(index, values, target)` 替代传统 6-flag OnlyEnforceIf 展开模式，每天每个物料 2 条查表约束（production + shift），消除所有辅助 BoolVar
- **预计算查表**：根据休息日状态预计算查表，消除条件分支约束
- **缩放因子**：`scale=2` 将浮点数转为整数运算
- **权重归一化**：休息日权重乘以 2（缩放到与缩放因子一致）
- **收紧变量界**：库存变量采用逐天收紧的上下界，帮助求解器快速剪枝
- **多线程并行**：`num_workers = min(8, cpu_count)`，充分利用多核 CPU 并行搜索

## 功能特性

### Excel 导出

排产结果支持一键导出为 Excel 文件（`排产结果.xlsx`），基于 `导出模板.xlsx` 模板填充：

- 动态列数（根据排产天数自动扩展/收缩）
- 周数合并单元格、日期/星期行
- 休息日粉色高亮标记
- 合计列、班次合计列
- 自动清除超出范围的残留格式和批注

### 调试模式

排产计算页面提供 🛠 **调试模式** 切换按钮。开启后，排产结果上方会显示求解器调试面板，包含：

- **求解器状态**：`OPTIMAL`（绿色）或 `FEASIBLE`（黄色）
- **求解耗时**：精确到毫秒级

### 前端校验

交货计划页面提供实时输入校验：

- 每日交货量天数匹配检查
- 非负整数格式校验
- 总交货量自动计算
- 重复物料检测
- 至少需要 1 个物料
- 物料必须属于所选产线

## 版本变更

| 版本 | 说明 |
|------|------|
| V1.0 | 单物料单产线，支持 6 种班次组合，含加班惩罚 |
| V2.0 | **双物料共享单产线**，每天 24h 工时竞争，独立库存/产量/交货，删除加班惩罚 |
| V2.1 | 前端重构为四页面 + 左侧导航栏，后端集成 MySQL 持久化，交货计划支持每日交货量输入，Excel 导出，数据库自动迁移 |
| V2.1.1 | **数据结构重构**：响应体字段从动态后缀格式（`total_production_days_1`/`_2`）改为数组结构（`product_stats[]`/`daily_results[].products[]`），交货计划物料数从强制 2 个改为 1~6 个，支持任意数量物料 |
