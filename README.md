# 智能排产系统

基于 **Google OR-Tools CP-SAT** 约束优化的智能生产排产系统，采用 Python FastAPI + React 前后端分离架构。

## 项目结构

```
POC/
├── backend/                  # 后端 - FastAPI
│   ├── main.py               # 入口文件 (uvicorn 启动)
│   └── app/
│       ├── __init__.py        # FastAPI 应用初始化 & CORS 配置
│       ├── algorithm/
│       │   └── scheduler.py   # OR-Tools CP-SAT 排产算法核心
│       ├── api/
│       │   └── scheduling.py  # API 路由（排产计算/校验）
│       ├── models/
│       │   └── schemas.py     # Pydantic 数据模型
│       └── services/
│           └── scheduling_service.py  # 业务逻辑
├── frontend/                 # 前端 - React + Vite
│   ├── package.json
│   ├── vite.config.js        # Vite 配置（端口3000，/api 代理到8000）
│   └── src/
│       ├── App.jsx
│       ├── api/api.js         # Axios 请求封装
│       └── components/
│           ├── ParameterForm.jsx   # 参数配置面板
│           ├── ResultTable.jsx     # 排产结果表格
│           └── ResultCharts.jsx    # 产量/库存趋势图
└── README.md
```

## 环境要求

- **Conda**（Miniconda 或 Anaconda）
- **Python**: 3.11（由 conda 环境管理）
- **Node.js**: >= 18（由 conda 环境管理）

## 环境搭建

> 以下命令从项目根目录 `POC/` 执行。需先安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)。

```powershell
conda create -n smart-scheduling python=3.11 -y
conda run -n smart-scheduling pip install fastapi uvicorn ortools pydantic chinese-calendar python-multipart
conda run -n smart-scheduling conda install nodejs -y
conda run -n smart-scheduling --cwd frontend npm install
```

> 环境已存在时跳过 `conda create`，直接执行后续 `conda run` 命令即可。

## 启动方式

> 需分别启动后端和前端，使用两个终端窗口。

| 服务 | 启动命令 | 地址 |
|------|---------|------|
| 后端 | `conda run -n smart-scheduling python backend/main.py` | http://localhost:8000 （API 文档：/docs） |
| 前端 | `conda run -n smart-scheduling --cwd frontend npm run dev` | http://localhost:3000 （/api 自动代理至后端） |

关闭服务：终端中 `Ctrl + C`

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/schedule` | 执行排产计算 |
| POST | `/api/validate` | 参数可行性校验 |

请求体结构：

```json
{
  "params": {
    "initial_inventory": 500,
    "safety_stock": 100,
    "rated_output": 200,
    "total_delivery": 5000,
    "start_date": "2026-05-01",
    "end_date": "2026-05-31",
    "holidays": [],
    "daily_deliveries": null
  },
  "config": {
    "overtime_shift_weight": 50,
    "overtime_day_weight": 50,
    "rest_day_weight": 50,
    "max_consecutive_work_days": 7,
    "max_time_seconds": 10
  }
}
```

响应体新增字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `solver_status` | string | 求解器状态：`"OPTIMAL"`（最优解）、`"FEASIBLE"`（可行解） |
| `solve_time` | float | 求解实际耗时（秒） |

### 前端权重映射

前端暴露五个用户可配置参数，前端不再有自动派生字段：

| 前端显示 | 默认值 | 可选范围 | 对应后端字段 | 映射规则 |
|---------|--------|---------|------------|---------|
| 规避加班权重 | 50 | 0~100（每10一档） | `overtime_shift_weight` | 直接等于 |
| 规避加班天数权重 | 50 | 0~100（每10一档） | `overtime_day_weight` | 直接等于 |
| 规避休息日上班权重 | 50 | 0~100（每10一档） | `rest_day_weight` | 直接等于 |
| 最大连续工作天数 | 7 | 3~14天（每1天一档） | `max_consecutive_work_days` | 直接等于 |
| 求解限时 | 10s | 10~60s（每10秒一档） | `max_time_seconds` | 直接等于 |

## 算法说明

使用 Google OR-Tools CP-SAT 约束求解器，单阶段优化目标函数。

### 班次模型

每天从 6 种班次组合中选择一种：

| combo | 班次1 | 班次2 | 标签 | 日产量（×额定产量） |
|-------|-------|-------|------|-------------------|
| 0 | 0 | 0 | 休息 | 0 |
| 1 | 1.0 | 0 | 1班 | 1.0 |
| 2 | 1.0 | 0.5 | 1班+0.5班 | 1.5 |
| 3 | 1.0 | 1.0 | 1班+1班 | 2.0 |
| 4 | 1.5 | 1.0 | 1.5班+1班 | 2.5 |
| 5 | 1.5 | 1.5 | 1.5班+1.5班 | 3.0 |

### 硬约束

- **库存平衡约束**：每日结存库存 = 前日结存库存 + 当日产量 - 当日交货量（首日 = 初始库存 + 当日产量 - 当日交货量）
- **库存安全约束**：每日结存库存 ≥ 安全库存
- **连续工作约束**：不允许连续工作超过 `max_consecutive_work_days` 天（硬约束）
- **可行性校验**：在考虑最大连续工作天数约束下，所有满负荷的最大产能需 ≥ 净需求（总交货量 - 初始库存 + 安全库存），否则直接报错无可行方案

### 目标函数

最小化以下加权和：

```
目标 = 5 × 最终库存超出安全库存的部分（×缩放因子2，等效真实权重10）
     + overtime_shift_weight × 总加班班次数
     + overtime_day_weight × 总加班天数
     + rest_day_weight × 占用休息日天数
     + 5 × 产量平滑惩罚
     + 60 × 长连续工作天数窗口数
```

所有权重经过内部归一化处理，以保证各项对求解器的实际影响力在合理范围内。
以默认值（加班权重=50，休息日权重=50，30天排产）为例，各惩罚项的最大贡献占比：
- **加班班次惩罚** ≈ 51%
- **占用休息日惩罚** ≈ 16%
- **长连续工作惩罚** ≈ 16%
- **产量平滑惩罚** ≈ 13%
- **过量生产惩罚** ≈ 5%
- **加班天数惩罚** ≈ 3%

- **过量生产惩罚**（固定权重 5，等效10）：仅作为基本防御，防止无限过量生产，不再主导目标函数
- **加班班次惩罚**（可配置，默认 50）：每次加班班次的惩罚。内部除以6归一化（一天最多6个半班次）
- **加班天数惩罚**（可配置，默认 50）：每个有加班生产的日子的惩罚。与加班班次权重各自独立配置，不再自动派生
- **占用休息日惩罚**（可配置，默认 50）：每个休息日被安排生产的惩罚。内部乘以2放大
- **产量平滑惩罚**（固定权重 5）：相邻两天 combo 等级差的绝对值之和，鼓励产量平稳过渡。权重5使该项在典型排产中贡献约5%的影响力
- **长连续工作惩罚**（固定权重 60）：对 `(max_consecutive_work_days - 1)` 天的连续工作窗口进行计数，每个窗口施加惩罚。配合硬约束使用，在不涉及额外占用休息日时引导算法主动拆分长连续工作段

### 加班计数规则

工作日和休息日（周末/节假日）采用不同的加班计数标准：

| combo | 班次组合 | 工作日加班班次 | 工作日是否加班天 | 休息日加班班次 | 休息日是否加班天 |
|-------|---------|-------------|---------------|-------------|---------------|
| 0 | 休息 | 0 | 否 | 0 | 否 |
| 1 | 1班 | 0 | 否 | 2 | 是 |
| 2 | 1班+0.5班 | 0 | 否 | 3 | 是 |
| 3 | 1班+1班 | 0 | 否 | 4 | 是 |
| 4 | 1.5班+1班 | 1 | 是 | 5 | 是 |
| 5 | 1.5班+1.5班 | 2 | 是 | 6 | 是 |

**计数逻辑**：

- **休息日**：所有半班次均计为加班。1.5班 = 3个半班次，1.0班 = 2个半班次，0.5班 = 1个半班次。因此休息日 (1.5, 1.5) = 3+3 = 6 次加班，(1.5, 1.0) = 3+2 = 5 次加班。只要安排了生产（combo ≥ 1），即计为加班天。
- **工作日**：仅超出1班的部分计为加班。0.5班 = 1次加班，1.5班 = 1次加班。因此工作日 (1.5, 1.5) = 1+1 = 2 次加班，(1.5, 1.0) = 1+0 = 1 次加班。仅 combo ≥ 4 时计为加班天。

### 占用休息日计数

休息日（周末/法定节假日）被安排了生产（combo > 0）即计为占用休息日。目标函数中 `rest_day_weight` 对每个占用休息日施加惩罚，权重越大求解器越倾向于避免在休息日排产。

### 日历识别

通过 `chinese_calendar` 库自动识别中国法定节假日、周末和调休上班日：

- **休息日判定**：`chinese_calendar.is_workday(d)` 返回 False 的日期
- **法定假日标记**：`chinese_calendar.is_holiday(d)` 返回 True 的日期
- **调休上班标记**：原本是周末（weekday ≥ 5）但 `chinese_calendar.is_workday(d)` 返回 True 的日期

### 交货量分配

- 若提供 `daily_deliveries` 参数，则按指定日期和数量交货
- 否则按整数均匀分配：`base = 总交货量 // 排产天数`，余数 `extra = 总交货量 % 排产天数`，前 `extra` 天交货 `base + 1`，其余天交货 `base`。交货量和结存库存均为整数

## 算法优化

模型构建采用以下优化手段加速求解：

- **AddElement 约束**：使用 `model.AddElement(index, values, target)` 替代传统 6-flag OnlyEnforceIf 展开模式，将每天 ~24 条约束减少为 4 条，消除所有辅助 BoolVar
- **预计算查表**：根据每日是否为休息日预计算查表，消除 `is_rest` BoolVar 及其分支约束
- **缩放因子**：缩放因子 `scale=2`，大幅缩小整数变量值域
- **权重归一化**：加班班次/天数权重除以6（一天最多6个半班次），休息日权重乘以2（缩放到与缩放因子一致），使各项实际影响力均衡
- **收紧变量界**：库存变量采用逐天收紧的上下界，帮助求解器快速剪枝

## 调试模式

前端右上角提供 🛠 **调试模式** 切换按钮。开启后，排产结果上方会显示求解器调试面板，包含：

- **求解器状态**：`OPTIMAL`（绿色）或 `FEASIBLE`（黄色）
- **求解耗时**：精确到毫秒级

用于排查求解性能问题，判断是否需要调整求解限时。
