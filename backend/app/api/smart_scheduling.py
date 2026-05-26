import asyncio
import uuid
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.progress_tracker import ProgressTracker
from app.models.plan_task import PlanTaskPending, PlanTask
from app.models.plan_task_order import PlanTaskOrderPending, PlanTaskOrder
from app.models.production_order import ProductionOrder
from app.models.production_resource import ProductionResource
from app.schemas.scheduling_strategy import (
    SchedulingGenerateRequest,
    SchedulingGenerateResponse,
    SchedulingProgressResponse,
    SchedulingConfirmResponse,
    GanttDataResponse,
)
from app.services.solve_service import SolveService

router = APIRouter(prefix="/api/smart-scheduling", tags=["smart-scheduling"])


@router.post("/generate", response_model=SchedulingGenerateResponse)
async def generate(request: SchedulingGenerateRequest, db: Session = Depends(get_db)):
    db.query(PlanTaskPending).delete()
    db.query(PlanTaskOrderPending).delete()
    db.commit()

    task_id = uuid.uuid4().hex
    ProgressTracker.create(task_id)
    db_url = settings.DATABASE_URL
    asyncio.create_task(
        SolveService.solve_async(task_id, request.strategy_id, db_url, request.start_date)
    )
    return SchedulingGenerateResponse(task_id=task_id, status="RUNNING")


@router.get("/plan/progress", response_model=SchedulingProgressResponse)
async def get_progress(task_id: str = Query(...)):
    data = ProgressTracker.get(task_id)
    return SchedulingProgressResponse(
        status=data.get("status", "NOT_FOUND"),
        progress=data.get("progress"),
        step=data.get("step"),
        logs=data.get("logs"),
    )


@router.post("/plan/pending/confirm", response_model=SchedulingConfirmResponse)
async def confirm_plan(db: Session = Depends(get_db)):
    try:
        pending_tasks = db.query(PlanTaskPending).all()
        for pt in pending_tasks:
            task = PlanTask(
                id=pt.id,
                code=pt.code,
                merge_task_code=pt.merge_task_code,
                origin_task_code=pt.origin_task_code,
                main_order_id=pt.main_order_id,
                production_order_id=pt.production_order_id,
                scheduled_quantity=pt.scheduled_quantity,
                process_code=pt.process_code,
                process_info=pt.process_info,
                front_task_codes=pt.front_task_codes,
                next_task_codes=pt.next_task_codes,
                main_resource_id=pt.main_resource_id,
                start_time=pt.start_time,
                end_time=pt.end_time,
                start_task=pt.start_task,
                end_task=pt.end_task,
                pinned=pt.pinned,
                merge_task=pt.merge_task,
                input_materials=pt.input_materials,
                task_status=pt.task_status,
                tenant_id=pt.tenant_id,
            )
            db.add(task)

        pending_orders = db.query(PlanTaskOrderPending).all()
        for po in pending_orders:
            order_record = PlanTaskOrder(
                id=po.id,
                production_order_id=po.production_order_id,
                order_code=po.order_code,
                material_code=po.material_code,
                quantity=po.quantity,
                delivery_time=po.delivery_time,
                priority=po.priority,
                tenant_id=po.tenant_id,
            )
            db.add(order_record)

        order_ids = set()
        for pt in pending_tasks:
            order_ids.add(pt.production_order_id)
        for po in pending_orders:
            order_ids.add(po.production_order_id)

        if order_ids:
            db.query(ProductionOrder).filter(
                ProductionOrder.id.in_(order_ids)
            ).update(
                {"scheduling_status": "SCHEDULED"},
                synchronize_session="fetch",
            )

        db.query(PlanTaskPending).delete()
        db.query(PlanTaskOrderPending).delete()

        db.commit()
        return SchedulingConfirmResponse(success=True, message="排产计划已确认")
    except Exception as e:
        db.rollback()
        raise e


@router.post("/plan/pending/cancel", response_model=SchedulingConfirmResponse)
async def cancel_plan(db: Session = Depends(get_db)):
    db.query(PlanTaskPending).delete()
    db.query(PlanTaskOrderPending).delete()
    db.commit()
    return SchedulingConfirmResponse(success=True, message="排产计划已放弃")


@router.post("/plan/clear", response_model=SchedulingConfirmResponse)
async def clear_plan(db: Session = Depends(get_db)):
    db.query(PlanTask).delete()
    db.query(PlanTaskOrder).delete()
    db.query(PlanTaskPending).delete()
    db.query(PlanTaskOrderPending).delete()
    db.query(ProductionOrder).update(
        {"scheduling_status": "UNSCHEDULED"}, synchronize_session="fetch"
    )
    db.commit()
    return SchedulingConfirmResponse(success=True, message="所有排产计划已清空")


@router.post("/preview/plan/tasks")
async def preview_tasks(
    page: Optional[int] = 1,
    page_size: Optional[int] = 20,
    db: Session = Depends(get_db),
):
    query = db.query(PlanTaskPending)
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": t.id,
                "code": t.code,
                "production_order_id": t.production_order_id,
                "scheduled_quantity": float(t.scheduled_quantity) if t.scheduled_quantity else 0,
                "process_code": t.process_code,
                "process_info": t.process_info,
                "front_task_codes": t.front_task_codes,
                "next_task_codes": t.next_task_codes,
                "main_resource_id": t.main_resource_id,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "start_task": t.start_task,
                "end_task": t.end_task,
                "pinned": t.pinned,
                "input_materials": t.input_materials,
                "task_status": t.task_status,
            }
            for t in items
        ],
    }


@router.post("/preview/plan/resource/gantt", response_model=GanttDataResponse)
async def preview_gantt(db: Session = Depends(get_db)):
    pending_tasks = db.query(PlanTaskPending).all()
    pending_orders = db.query(PlanTaskOrderPending).all()
    resources = db.query(ProductionResource).all()

    order_code_map = {}
    for po in pending_orders:
        order_code_map[po.production_order_id] = po.order_code

    material_code_map = {}
    for po in pending_orders:
        if po.production_order_id not in material_code_map:
            material_code_map[po.production_order_id] = po.material_code

    resource_map = {r.id: r for r in resources}
    resource_tasks = defaultdict(list)

    for t in pending_tasks:
        if t.main_resource_id:
            task_data = {
                "task_code": t.code,
                "process_code": t.process_code,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "order_id": t.production_order_id,
                "order_code": order_code_map.get(t.production_order_id, ""),
                "material_code": material_code_map.get(t.production_order_id, ""),
            }
            resource_tasks[t.main_resource_id].append(task_data)

    gantt_resources = []
    for r in resources:
        gantt_resources.append({
            "id": r.id,
            "name": r.name,
            "tasks": resource_tasks.get(r.id, []),
        })

    return GanttDataResponse(resources=gantt_resources)


@router.get("/plan/tasks")
async def get_confirmed_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    order_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(PlanTask)
    if order_id:
        query = query.filter(PlanTask.production_order_id == order_id)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(PlanTask.start_time.asc()).offset(offset).limit(page_size).all()

    resource_map = {}
    if items:
        resource_ids = set(t.main_resource_id for t in items if t.main_resource_id)
        if resource_ids:
            resources = db.query(ProductionResource).filter(
                ProductionResource.id.in_(resource_ids)
            ).all()
            resource_map = {r.id: r for r in resources}

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": t.id,
                "code": t.code,
                "production_order_id": t.production_order_id,
                "scheduled_quantity": float(t.scheduled_quantity) if t.scheduled_quantity else 0,
                "process_code": t.process_code,
                "process_info": t.process_info,
                "front_task_codes": t.front_task_codes,
                "next_task_codes": t.next_task_codes,
                "main_resource_id": t.main_resource_id,
                "resource_name": resource_map[t.main_resource_id].name if t.main_resource_id and t.main_resource_id in resource_map else None,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "start_task": t.start_task,
                "end_task": t.end_task,
                "pinned": t.pinned,
                "input_materials": t.input_materials,
                "task_status": t.task_status,
            }
            for t in items
        ],
    }


@router.post("/plan/resource/gantt", response_model=GanttDataResponse)
async def get_confirmed_gantt(
    order_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(PlanTask)
    if order_id:
        query = query.filter(PlanTask.production_order_id == order_id)

    tasks = query.all()
    confirmed_orders = db.query(PlanTaskOrder).all()
    resources = db.query(ProductionResource).all()

    order_code_map = {}
    material_code_map = {}
    for po in confirmed_orders:
        order_code_map[po.production_order_id] = po.order_code
        if po.production_order_id not in material_code_map:
            material_code_map[po.production_order_id] = po.material_code

    resource_map = {r.id: r for r in resources}
    resource_tasks = defaultdict(list)

    for t in tasks:
        if t.main_resource_id:
            task_data = {
                "task_code": t.code,
                "process_code": t.process_code,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "end_time": t.end_time.isoformat() if t.end_time else None,
                "order_id": t.production_order_id,
                "order_code": order_code_map.get(t.production_order_id, ""),
                "material_code": material_code_map.get(t.production_order_id, ""),
            }
            resource_tasks[t.main_resource_id].append(task_data)

    gantt_resources = []
    for r in resources:
        gantt_resources.append({
            "id": r.id,
            "name": r.name,
            "tasks": resource_tasks.get(r.id, []),
        })

    return GanttDataResponse(resources=gantt_resources)
