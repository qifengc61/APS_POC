import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.progress_tracker import ProgressTracker
from app.models.planning_strategy import PlanningStrategy
from app.models.production_order import ProductionOrder
from app.models.production_resource import ProductionResource
from app.models.plan_task import PlanTaskPending, PlanTask
from app.models.plan_task_order import PlanTaskOrderPending, PlanTaskOrder
from app.models.work_calendar import WorkCalendar, WorkMode, ResourceCalendar
from app.services.mrp_service import MRPService
from app.services.task_generation_service import TaskGenerationService
from app.algorithm.job_shop_scheduler import JobShopScheduler
from app.utils.time_calculator import WorkCalendarCalculator

logger = logging.getLogger("aps.solve")


class SolveService:

    @staticmethod
    def _run_sync(task_id: str, strategy_id: Optional[str], db_url: str, start_date: Optional[date] = None):
        engine = create_engine(db_url, pool_pre_ping=True)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = Session()
        try:
            strategy_config = {}
            optimize_rules = []
            planning_start = datetime.now()

            if strategy_id:
                ProgressTracker.update(task_id, progress=10, step="加载策略配置")
                strategy = db.query(PlanningStrategy).filter(
                    PlanningStrategy.id == strategy_id
                ).first()
                if not strategy:
                    raise ValueError(f"策略不存在: {strategy_id}")

                strategy_config = strategy.config or {}
                optimize_rules = strategy.optimize_rules or []
                planning_start = strategy.begin_time or datetime.now()
            else:
                ProgressTracker.update(task_id, progress=10, step="使用默认策略配置")

            strategy_config["optimize_rules"] = optimize_rules

            ProgressTracker.update(task_id, progress=20, step="MRP物料需求计划")
            orders = db.query(ProductionOrder).filter(
                ProductionOrder.can_schedule == True,
                ProductionOrder.order_status != "CANCELLED",
            ).all()
            order_ids = [o.id for o in orders]
            if not order_ids:
                raise ValueError("没有可排产的订单 (can_schedule=True 且 order_status!=CANCELLED)")

            logger.info("开始排产: strategy=%s, 可排产订单数=%d", strategy_id, len(order_ids))
            mrp_result = MRPService.run(db, order_ids)
            logger.info("MRP完成: 缺料DAG节点数=%d, 补充订单数=%d",
                        len(mrp_result.shortage_dag.nodes) if mrp_result.shortage_dag else 0,
                        len(mrp_result.supplement_orders))

            ProgressTracker.update(task_id, progress=40, step="生成排产任务")
            task_dicts = TaskGenerationService.generate(db, mrp_result, strategy_id)
            if not task_dicts:
                raise ValueError(
                    "未生成排产任务 — 请检查后端日志(aps.task_gen)了解详情。"
                    "常见原因: 1)物料未配置工艺路线 2)生产订单的material_code与BOM不匹配 3)缺料DAG为空"
                )

            ProgressTracker.update(task_id, progress=60, step="约束优化求解")
            resources = db.query(ProductionResource).all()
            resource_dicts = []
            for r in resources:
                resource_dicts.append({
                    "id": r.id,
                    "name": r.name,
                    "code": r.code,
                    "resource_group": r.resource_group,
                    "throughput": r.throughput,
                    "resource_status": r.resource_status,
                })

            logger.info("求解准备: 任务数=%d, 资源数=%d", len(task_dicts), len(resource_dicts))
            for r in resource_dicts:
                logger.info("  资源: id=%s code=%s name=%s status=%s throughput=%s group=%s",
                            r["id"][:8], r["code"], r["name"],
                            r.get("resource_status"), r.get("throughput"),
                            r.get("resource_group", "-"))

            delivery_times = {}
            for order in orders:
                if order.delivery_time:
                    delivery_times[order.id] = order.delivery_time

            calendars = db.query(WorkCalendar).filter(
                WorkCalendar.enabled == True
            ).all()
            work_modes = db.query(WorkMode).all()

            calendar_calculator = None
            if calendars and work_modes:
                calendar_dicts = []
                for cal in calendars:
                    calendar_dicts.append({
                        "id": cal.id,
                        "name": cal.name,
                        "work_mode_id": cal.work_mode_id,
                        "begin_time": cal.begin_time,
                        "end_time": cal.end_time,
                        "enabled": cal.enabled,
                        "work_days": cal.work_days,
                        "priority": cal.priority,
                    })
                work_mode_dicts = []
                for wm in work_modes:
                    work_mode_dicts.append({
                        "id": wm.id,
                        "name": wm.name,
                        "time_periods": wm.time_periods,
                    })
                calendar_calculator = WorkCalendarCalculator(calendar_dicts, work_mode_dicts)
                logger.info("工作日历已加载: %d个日历, %d个工作模式", len(calendar_dicts), len(work_mode_dicts))

                if start_date is not None:
                    check_dt = datetime(start_date.year, start_date.month, start_date.day, 12, 0)
                    if not calendar_calculator.is_work_day(check_dt):
                        raise ValueError(f"排产开始日期 {start_date} 不是工作日，请选择周一至周五")
                    planning_start = calendar_calculator.find_next_work_time(
                        datetime(start_date.year, start_date.month, start_date.day, 0, 0)
                    )
                elif not strategy_id:
                    tomorrow = datetime.now() + timedelta(days=1)
                    planning_start = calendar_calculator.find_next_work_time(
                        datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0)
                    )
            else:
                logger.warning("未配置工作日历或工作模式，排产将不考虑工作日约束")

            scheduler = JobShopScheduler(
                tasks=task_dicts,
                resources=resource_dicts,
                strategy_config=strategy_config,
                planning_start=planning_start,
                delivery_times=delivery_times,
                calendar_calculator=calendar_calculator,
            )
            solve_result = scheduler.solve()

            resource_assignments = {}
            for rt in solve_result.get("tasks", []):
                rid = rt.get("resource_id")
                if rid:
                    res_name = next(
                        (r["name"] for r in resource_dicts if r["id"] == rid), rid[:8]
                    )
                    resource_assignments[rt["task_code"]] = res_name
            logger.info("资源分配结果: %s", resource_assignments)

            if not solve_result.get("success"):
                raise ValueError(
                    f"求解失败: {solve_result.get('status')}。"
                    "请检查后端日志(aps.scheduler)了解详情。"
                    "常见原因: 1)工序未配置主资源 2)工序资源的resource_id与实际资源ID不匹配 "
                    "3)资源状态不是NORMAL 4)同资源上任务间隔约束冲突"
                )

            ProgressTracker.update(task_id, progress=80, step="保存排产结果")
            for result_task in solve_result.get("tasks", []):
                task_id_db = result_task["task_id"]
                pending = db.query(PlanTaskPending).filter(
                    PlanTaskPending.id == task_id_db
                ).first()
                if pending:
                    pending.main_resource_id = result_task.get("resource_id")
                    pending.start_time = result_task.get("start_time")
                    pending.end_time = result_task.get("end_time")
                    pending.pinned = result_task.get("pinned", False)

            db.flush()

            ProgressTracker.update(task_id, progress=90, step="完成")
            db.commit()
            ProgressTracker.complete(task_id)

        except Exception as e:
            db.rollback()
            ProgressTracker.fail(task_id, str(e))
        finally:
            db.close()
            engine.dispose()

    @staticmethod
    async def solve_async(task_id: str, strategy_id: Optional[str], db_url: str, start_date: Optional[date] = None):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            SolveService._run_sync,
            task_id,
            strategy_id,
            db_url,
            start_date,
        )
