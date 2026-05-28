# Tasks

## 阶段一：数据基础层

- [x] Task 1: 搭建数据库基础设施
  - [x] 1.1 创建 docker-compose.yml，配置 MySQL 8.0 服务（端口3306，数据库aps，字符集utf8mb4）
  - [x] 1.2 创建 backend/requirements.txt，添加 sqlalchemy, alembic, pymysql, cryptography 依赖
  - [x] 1.3 创建 backend/alembic.ini 和 backend/alembic/ 迁移目录
  - [x] 1.4 创建 backend/app/core/database.py（SQLAlchemy引擎、SessionLocal、Base、get_db依赖）
  - [x] 1.5 创建 backend/app/core/config.py（数据库连接等配置，从环境变量读取）
  - [x] 1.6 生成初始迁移脚本并验证数据库连接

- [x] Task 2: 创建核心数据模型（SQLAlchemy ORM）
  - [x] 2.1 创建 backend/app/models/material.py（Material模型，含 code/name/type/source/quantity/safety_stock/unit/lead_time/buffer_time/tenant_id）
  - [x] 2.2 创建 backend/app/models/manufacture_bom.py（ManufactureBOM模型，含 material_id/child_materials JSON）
  - [x] 2.3 创建 backend/app/models/process.py（Process模型，含 name/code/pre_interval/post_interval/process_relationship/buffer_time/batch_strategy/use_main_resources/use_auxiliary_resources/use_materials JSON字段）
  - [x] 2.4 创建 backend/app/models/process_route.py（ProcessRoute模型，含 material_id/route_design JSON/enabled）
  - [x] 2.5 创建 backend/app/models/production_resource.py（ProductionResource模型，含 name/code/resource_group/capacity/unit/throughput/resource_status）
  - [x] 2.6 创建 backend/app/models/work_calendar.py（WorkCalendar + WorkMode + ResourceCalendar 三个模型）
  - [x] 2.7 创建 backend/app/models/incoming_material_order.py（IncomingMaterialOrder模型）
  - [x] 2.8 创建 backend/app/models/__init__.py 统一导出所有模型
  - [x] 2.9 生成迁移脚本并验证所有表创建成功

- [x] Task 3: 实现基础数据 CRUD API
  - [x] 3.1 创建 backend/app/schemas/ 目录，为每个实体创建 Pydantic Schema（Create/Update/Response）
  - [x] 3.2 创建 backend/app/api/material.py（物料CRUD：POST/PUT/DELETE/GET/page）
  - [x] 3.3 创建 backend/app/api/manufacture_bom.py（BOM CRUD）
  - [x] 3.4 创建 backend/app/api/process.py（工序CRUD）
  - [x] 3.5 创建 backend/app/api/process_route.py（工艺路线CRUD + DAG校验接口）
  - [x] 3.6 创建 backend/app/api/production_resource.py（资源CRUD）
  - [x] 3.7 创建 backend/app/api/work_calendar.py（日历+工作模式+资源日历CRUD）
  - [x] 3.8 创建 backend/app/api/incoming_material_order.py（来料订单CRUD）
  - [x] 3.9 更新 backend/app/api/__init__.py 注册所有路由

- [x] Task 4: 实现图算法工具
  - [x] 4.1 创建 backend/app/utils/graph.py（Graph数据结构、拓扑排序Kahn算法、环检测、多终点检测）
  - [x] 4.2 在工艺路线API中集成DAG校验（保存前自动检测环和多终点）

- [x] Task 5: 前端基础设施搭建
  - [x] 5.1 安装前端依赖：react-router-dom, antd, @ant-design/icons, dayjs
  - [x] 5.2 创建前端布局组件（AppLayout：侧边栏+顶部栏+内容区）
  - [x] 5.3 配置 React Router 路由（基础数据、订单、策略、排产等路由模块）
  - [x] 5.4 重构 frontend/src/api/api.js，添加基础数据API调用函数
  - [x] 5.5 将现有排产页面移至 /quick-scheduling 路由

- [x] Task 6: 前端基础数据管理页面
  - [x] 6.1 创建物料管理页面（MaterialPage：表格+新增/编辑弹窗+删除确认）
  - [x] 6.2 创建BOM管理页面（BomPage：表格+子件编辑）
  - [x] 6.3 创建工序管理页面（ProcessPage：表格+JSON字段编辑）
  - [x] 6.4 创建生产资源管理页面（ResourcePage：表格+表单）
  - [x] 6.5 创建工作日历管理页面（CalendarPage：日历+工作模式+资源关联）
  - [x] 6.6 创建来料订单管理页面（IncomingOrderPage：表格+表单）

- [x] Task 7: 前端工艺路线DAG编辑器
  - [x] 7.1 安装 @xyflow/react（React Flow）依赖
  - [x] 7.2 创建 ProcessRouteEditor 组件（节点拖拽、连线、删除）
  - [x] 7.3 创建工艺路线管理页面（ProcessRoutePage：列表+DAG编辑器弹窗）
  - [x] 7.4 集成DAG校验反馈（环检测、多终点检测错误提示）

## 阶段二：订单与策略

- [x] Task 8: 后端订单与策略模型
  - [x] 8.1 创建 backend/app/models/production_order.py（ProductionOrder模型，含全部字段）
  - [x] 8.2 创建 backend/app/models/planning_strategy.py（PlanningStrategy模型，含config/order_scheduling_rules/optimize_rules JSON字段）
  - [x] 8.3 生成迁移脚本

- [x] Task 9: 后端订单与策略API
  - [x] 9.1 创建 backend/app/schemas/production_order.py（订单Create/Update/Response Schema）
  - [x] 9.2 创建 backend/app/schemas/planning_strategy.py（策略Create/Update/Response Schema）
  - [x] 9.3 创建 backend/app/api/production_order.py（订单CRUD + 排序 + 排产参与控制 + 补充订单查询）
  - [x] 9.4 创建 backend/app/api/planning_strategy.py（策略CRUD + 排序规则选项接口）
  - [x] 9.5 注册路由

- [x] Task 10: 前端订单与策略管理页面
  - [x] 10.1 创建生产订单管理页面（OrderPage：表格+筛选+排序+新增/编辑弹窗+排产参与开关）
  - [x] 10.2 创建排产策略配置页面（StrategyPage：策略列表+编辑弹窗含方向选择/排序规则拖拽/优化权重滑块）

## 阶段三：核心引擎

- [x] Task 11: MRP物料需求计划
  - [x] 11.1 创建 backend/app/services/mrp_service.py（BOM递归展开、库存齐套检查、缺料DAG生成、补充订单自动创建）
  - [x] 11.2 创建 backend/app/schemas/mrp.py（MRP输入输出Schema）

- [x] Task 12: 任务自动生成
  - [x] 12.1 创建 backend/app/models/plan_task.py（PlanTask模型 + PlanTaskPending模型，双表设计）
  - [x] 12.2 创建 backend/app/models/plan_task_order.py（PlanTaskOrder + PlanTaskOrderPending模型）
  - [x] 12.3 生成迁移脚本
  - [x] 12.4 创建 backend/app/services/task_generation_service.py（缺料DAG拓扑排序→工艺路线拓扑排序→任务链生成→前后置依赖建立→跨物料依赖）
  - [x] 12.5 创建 backend/app/schemas/plan_task.py（任务相关Schema）

- [x] Task 13: 时间计算器
  - [x] 13.1 创建 backend/app/utils/time_calculator.py（工作日历感知时间计算、三种产能格式解析、ES/EE工序关系处理、工作时间段跳过逻辑）

- [x] Task 14: 作业车间调度CP-SAT模型
  - [x] 14.1 创建 backend/app/algorithm/job_shop_scheduler.py（新调度器：决策变量task_resource/task_start/task_end，硬约束，软约束，可配置权重）
  - [x] 14.2 创建 backend/app/schemas/scheduling_strategy.py（排产请求/结果Schema，包含策略ID和排产方向）

- [x] Task 15: 异步求解与进度追踪
  - [x] 15.1 创建 backend/app/services/solve_service.py（编排MRP→任务生成→CP-SAT求解的完整流程）
  - [x] 15.2 创建 backend/app/core/progress_tracker.py（内存进度追踪：状态/百分比/步骤/日志，心跳超时检测）
  - [x] 15.3 创建 backend/app/api/smart_scheduling.py（排产触发/进度轮询/Pending确认/Pending放弃/预览接口）

- [x] Task 16: 前端排产触发与结果页面
  - [x] 16.1 创建排产触发页面（SchedulingPage：选择策略→触发排产→进度展示→结果预览）
  - [x] 16.2 创建排产结果预览组件（任务列表视图 + 资源甘特图视图 + 确认/放弃按钮）
  - [x] 16.3 创建简易甘特图组件（基于CSS/SVG的资源维度甘特图）

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 2
- Task 6 depends on Task 5
- Task 7 depends on Task 5, Task 4
- Task 8 depends on Task 2
- Task 9 depends on Task 8
- Task 10 depends on Task 5, Task 9
- Task 11 depends on Task 3
- Task 12 depends on Task 11, Task 4
- Task 13 depends on Task 3
- Task 14 depends on Task 13
- Task 15 depends on Task 14, Task 12
- Task 16 depends on Task 10, Task 15
