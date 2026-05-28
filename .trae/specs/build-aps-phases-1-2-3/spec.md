# 智能排产系统阶段1-3升级 Spec

## Why
当前POC系统仅支持单一产能规划（每天排几班），缺乏持久化层、基础数据管理、MRP物料需求计划和真正的作业车间调度能力。需要将其升级为具备完整基础数据CRUD、订单与策略管理、以及核心排产引擎的智能排产系统，技术栈保持 Python FastAPI + React + Google OR-Tools CP-SAT。

## What Changes
- **新增 MySQL 数据库层**：使用 SQLAlchemy + Alembic，通过 Docker Desktop 运行 MySQL 8.0
- **新增 13 张核心数据表**：物料、BOM、工序、工艺路线、生产资源、工作日历、工作模式、资源日历关联、生产订单、排产策略、来料订单、排产计划任务（正式+待确认）
- **新增基础数据 CRUD API**：物料、BOM、工序、工艺路线、资源、日历、工作模式、资源日历
- **新增工艺路线 DAG 校验**：环检测、多终点检测
- **新增生产订单管理 API**：订单CRUD、排序、参与排产控制、补充订单
- **新增排产策略管理 API**：策略CRUD、排序规则选项、优化权重配置
- **新增来料订单管理 API**
- **重写 CP-SAT 约束模型**：从"班次组合"模型升级为"任务→资源→时间"的作业车间调度模型
- **新增 MRP 物料需求计划**：BOM展开、库存齐套检查、缺料DAG生成
- **新增任务自动生成**：工艺路线DAG拓扑排序→任务链、前后置依赖建立
- **新增异步求解与进度追踪**：后台任务求解、进度轮询API
- **新增双表确认机制**：Pending表→预览→确认/放弃
- **前端重构**：引入 React Router + Ant Design，搭建管理后台布局
- **新增前端页面**：基础数据管理、订单管理、策略配置、排产触发与进度、结果预览
- **保留现有排产功能**：原有的班次排产功能作为"快速排产"保留

## Impact
- Affected code: backend/app/ 全部模块需重构扩展, frontend/src/ 全部重构
- **BREAKING**: 前端API调用方式变更，新增数据库依赖

## ADDED Requirements

### Requirement: 数据库基础设施
系统 SHALL 使用 MySQL 8.0 作为持久化存储，通过 Docker Compose 管理服务生命周期。系统 SHALL 使用 SQLAlchemy 作为 ORM，Alembic 管理数据库迁移。

#### Scenario: MySQL 服务启动
- **WHEN** 执行 `docker compose up -d`
- **THEN** MySQL 8.0 服务在 3306 端口可用，自动创建 `aps` 数据库

#### Scenario: 数据库迁移
- **WHEN** 执行 `alembic upgrade head`
- **THEN** 所有核心表被正确创建，包含索引和约束

### Requirement: 物料管理
系统 SHALL 提供物料的 CRUD 操作，支持字段：编码(租户级唯一)、名称、类型(原材料/半成品/成品)、来源(自制/外购)、当前库存、安全库存、计量单位、提前期、缓冲期。

#### Scenario: 创建物料
- **WHEN** 用户提交物料数据（code="M001", name="钢板", type="RAW_MATERIAL", source="PURCHASED"）
- **THEN** 系统创建物料记录并返回201，重复编码返回409

#### Scenario: 物料分页查询
- **WHEN** 用户请求 GET /api/materials?page=1&page_size=20
- **THEN** 返回分页结果，包含总数和当前页数据

### Requirement: 制造BOM管理
系统 SHALL 提供制造BOM的 CRUD 操作，BOM关联一个成品物料ID，子件列表以JSON数组存储 [{materialId, quantity}]。

#### Scenario: 创建BOM
- **WHEN** 用户为物料M001创建BOM，子件为 [{materialId: "M002", quantity: 2}, {materialId: "M003", quantity: 1}]
- **THEN** 系统创建BOM记录，验证子件物料存在

### Requirement: 工序管理
系统 SHALL 提供工序的 CRUD 操作，支持字段：名称、编码、前间隔时长、后间隔时长、工序关系(ES/EE)、缓冲时长、批量策略(JSON)、可用主资源列表(JSON)、可用辅助资源(JSON)、输入物料(JSON)。

#### Scenario: 创建工序
- **WHEN** 用户创建工序，指定可用主资源列表和产能信息
- **THEN** 系统创建工序记录，JSON字段正确存储

### Requirement: 工艺路线管理
系统 SHALL 提供工艺路线的 CRUD 操作，工艺路线以JSON DAG结构存储（nodes + edges），每个物料对应一条工艺路线。

#### Scenario: 创建工艺路线
- **WHEN** 用户为物料M001创建工艺路线，包含3个工序节点和2条边
- **THEN** 系统创建工艺路线记录

#### Scenario: 工艺路线环检测
- **WHEN** 用户保存的工艺路线存在环
- **THEN** 系统返回400错误，提示"工艺路线不允许存在环"

#### Scenario: 工艺路线多终点检测
- **WHEN** 用户保存的工艺路线存在多个终点（出度为0的节点>1）
- **THEN** 系统返回400错误，提示"工艺路线应只有一个终点节点"

### Requirement: 生产资源管理
系统 SHALL 提供生产资源的 CRUD 操作，支持字段：名称、编码、资源组、容量(并行处理能力)、容量单位、默认产能、资源状态(正常/维护/报废)。

### Requirement: 工作日历管理
系统 SHALL 提供工作日历和工作模式的 CRUD 操作。工作日历包含：名称、关联工作模式、有效期间、是否启用、工作日位图(7位，周日→周六)、优先级。工作模式定义一天中的工作时间段。

### Requirement: 资源日历关联
系统 SHALL 支持将工作日历关联到生产资源，一个资源可关联多个日历（按优先级覆盖）。

### Requirement: 生产订单管理
系统 SHALL 提供生产订单的完整生命周期管理，支持字段：编码、物料编码、需求数量、交付期限、优先级、排序序号、订单状态(待处理/已完成/已取消)、排产状态(未排/已排/完成/不排)、是否参与排产、是否补充订单、父订单编码、甘特图颜色。

#### Scenario: 创建订单
- **WHEN** 用户创建生产订单（material_code="M001", quantity=100, delivery_time="2026-06-30"）
- **THEN** 系统创建订单，初始状态为 PENDING/UNSCHEDULED

#### Scenario: 修改排产参与状态
- **WHEN** 用户修改订单的 can_schedule 字段
- **THEN** 系统更新订单状态，不参与排产的订单在排产时被排除

### Requirement: 排产策略管理
系统 SHALL 提供排产策略的 CRUD 操作，策略包含：名称、排产开始时间、是否有效、策略配置JSON(direction: FORWARD/BACKWARD, materialConstrained, maxNoImprovementTime)、订单排序规则JSON数组、优化规则权重JSON数组。

#### Scenario: 获取排序规则选项
- **WHEN** 用户请求 GET /api/planning-strategies/scheduling-rule/options
- **THEN** 返回可用的排序规则列表（如：按优先级、按交期、按创建时间等）

### Requirement: 来料订单管理
系统 SHALL 提供来料订单的 CRUD 操作，记录物料在途数量和预计到货时间，用于MRP库存齐套计算。

### Requirement: MRP物料需求计划
系统 SHALL 实现MRP物料需求计划算法：从生产订单目标物料开始，按BOM层级递归展开，计算净需求=毛需求-可用库存-在途数量，生成缺料DAG图。

#### Scenario: BOM展开与齐套检查
- **WHEN** 触发MRP计算，订单需要100个成品M001，M001的BOM需要2个M002
- **THEN** 系统递归展开BOM，扣减库存和在途，生成缺料节点和依赖边

#### Scenario: 补充订单生成
- **WHEN** MRP发现缺料且物料为自制件(source=PRODUCED)
- **THEN** 系统自动创建补充生产订单

### Requirement: 任务自动生成
系统 SHALL 从缺料DAG和工艺路线DAG自动生成排产任务。对缺料DAG进行拓扑排序，为每个缺料物料的工艺路线DAG再进行拓扑排序，生成任务链并建立前后置依赖关系。

#### Scenario: 从工艺路线生成任务
- **WHEN** 物料M001的工艺路线包含工序A→B→C
- **THEN** 系统生成3个任务，A的前置为空，B的前置为A，C的前置为B

#### Scenario: 跨物料依赖
- **WHEN** M001的BOM需要M002，M002的末道工序任务应先于M001的首道工序任务
- **THEN** 系统建立跨物料的前后置依赖关系

### Requirement: 作业车间调度CP-SAT模型
系统 SHALL 实现基于CP-SAT的作业车间调度模型，将每个任务分配到资源和时间槽。

**决策变量**：
- task_resource[task]：任务分配的资源索引
- task_start[task]：任务开始时间（分钟级时间戳）
- task_end[task]：任务结束时间

**硬约束**：
- 任务工序必须在分配资源的可用工序列表中
- 同一资源上任务时间段不重叠（AddNoOverlap）
- 前后置任务时序约束
- 每个任务必须分配资源并有明确时间

**软约束**（可配置权重）：
- 最小化延期总时长
- 最小化延期任务数量
- 优先安排临近交期的订单
- 最小化依赖任务间间隔
- 尽早完成所有任务
- 均衡各资源任务数量
- 均衡各资源工作负载
- 按策略排序规则排列

#### Scenario: 排产求解成功
- **WHEN** 触发排产，CP-SAT求解器找到可行解
- **THEN** 每个任务被分配到合法资源，时间不重叠，前后置依赖满足

#### Scenario: 排产无可行解
- **WHEN** 约束过紧无法满足
- **THEN** 返回失败信息，提示调整参数

### Requirement: 时间计算器
系统 SHALL 实现工作日历感知的时间计算，支持三种产能格式：处理单个需要多久("5M")、单位时间处理多少("10/H")、一批需要多久("30M/P")。支持ES(结束-开始)和EE(结束-结束)两种工序关系。

#### Scenario: 工作日历感知计算
- **WHEN** 任务开始时间落在非工作时间段
- **THEN** 自动调整到下一个工作时间段开始

#### Scenario: 产能格式解析
- **WHEN** 工序产能格式为"10/H"，数量为100
- **THEN** 任务持续时长 = 100/10 = 10小时

### Requirement: 异步求解与进度追踪
系统 SHALL 支持异步排产求解，使用后台任务执行求解，提供进度轮询API。进度信息包含：状态(RUNNING/SUCCESS/FAILED)、进度百分比、步骤数、开始时间、日志列表。

#### Scenario: 触发异步排产
- **WHEN** 用户触发排产
- **THEN** 立即返回任务ID，后台开始求解

#### Scenario: 轮询进度
- **WHEN** 前端轮询 GET /api/smart-scheduling/plan/progress?task_id=xxx
- **THEN** 返回当前进度状态和百分比

### Requirement: 双表确认机制
系统 SHALL 使用双表设计管理排产结果：排产完成后先写入Pending表，用户确认后转储至正式表。

#### Scenario: 排产结果写入Pending
- **WHEN** 排产求解完成
- **THEN** 结果写入 jvs_plan_task_pending 和 jvs_plan_task_order_pending 表

#### Scenario: 用户确认计划
- **WHEN** 用户调用 POST /api/smart-scheduling/plan/pending/confirm
- **THEN** Pending表数据原子转储至正式表，清除Pending数据

#### Scenario: 用户放弃计划
- **WHEN** 用户调用 POST /api/smart-scheduling/plan/pending/cancel
- **THEN** 清除Pending表数据

### Requirement: 前端管理后台布局
系统前端 SHALL 使用 React Router + Ant Design 搭建管理后台布局，包含侧边栏导航、顶部标题栏、内容区域。

### Requirement: 前端基础数据管理页面
系统前端 SHALL 提供物料、BOM、工序、工艺路线、生产资源、工作日历的管理页面，每个页面包含列表展示、新增、编辑、删除功能。

### Requirement: 前端工艺路线DAG编辑器
系统前端 SHALL 提供工艺路线的DAG可视化编辑器，支持节点拖拽、连线、删除，以及环检测提示。

### Requirement: 前端订单与策略管理页面
系统前端 SHALL 提供生产订单管理页面（列表、新增、编辑、排序、排产参与控制）和排产策略配置页面（方向选择、排序规则配置、优化权重滑块）。

### Requirement: 前端排产触发与进度页面
系统前端 SHALL 提供排产触发面板（选择策略→触发排产）和进度展示组件（进度条、状态、日志）。

### Requirement: 前端排产结果预览页面
系统前端 SHALL 提供排产结果预览，包含任务列表视图和甘特图视图（资源维度），支持确认/放弃操作。

## MODIFIED Requirements

### Requirement: 现有排产功能保留
原有的班次排产功能（/api/schedule 和 /api/validate）SHALL 作为"快速排产"模式保留，与新的作业车间调度模式并存。前端SHALL在导航中提供两种排产模式的入口。

## REMOVED Requirements
无移除项。
