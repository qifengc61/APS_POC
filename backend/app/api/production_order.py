from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.production_order import ProductionOrder
from app.models.plan_task import PlanTask, PlanTaskPending
from app.models.plan_task_order import PlanTaskOrder, PlanTaskOrderPending
from app.schemas.production_order import (
    ProductionOrderCreate,
    ProductionOrderUpdate,
    ProductionOrderResponse,
    ProductionOrderPageResponse,
)

router = APIRouter(prefix="/api/production-orders", tags=["production-orders"])


@router.post("/", response_model=ProductionOrderResponse, status_code=201)
def create_production_order(data: ProductionOrderCreate, db: Session = Depends(get_db)):
    existing = db.query(ProductionOrder).filter(ProductionOrder.code == data.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="订单编码已存在")
    obj = ProductionOrder(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=ProductionOrderResponse)
def update_production_order(id: str, data: ProductionOrderUpdate, db: Session = Depends(get_db)):
    obj = db.query(ProductionOrder).filter(ProductionOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"] != obj.code:
        existing = db.query(ProductionOrder).filter(ProductionOrder.code == update_data["code"]).first()
        if existing:
            raise HTTPException(status_code=409, detail="订单编码已存在")
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_production_order(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProductionOrder).filter(ProductionOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="订单不存在")

    db.query(PlanTask).filter(PlanTask.production_order_id == id).delete(synchronize_session="fetch")
    db.query(PlanTaskPending).filter(PlanTaskPending.production_order_id == id).delete(synchronize_session="fetch")
    db.query(PlanTaskOrder).filter(PlanTaskOrder.production_order_id == id).delete(synchronize_session="fetch")
    db.query(PlanTaskOrderPending).filter(PlanTaskOrderPending.production_order_id == id).delete(synchronize_session="fetch")

    supplements = db.query(ProductionOrder).filter(
        ProductionOrder.parent_order_code == obj.code,
        ProductionOrder.supplement == True,
    ).all()
    for sup in supplements:
        db.query(PlanTask).filter(PlanTask.production_order_id == sup.id).delete(synchronize_session="fetch")
        db.query(PlanTaskPending).filter(PlanTaskPending.production_order_id == sup.id).delete(synchronize_session="fetch")
        db.query(PlanTaskOrder).filter(PlanTaskOrder.production_order_id == sup.id).delete(synchronize_session="fetch")
        db.query(PlanTaskOrderPending).filter(PlanTaskOrderPending.production_order_id == sup.id).delete(synchronize_session="fetch")
        db.delete(sup)

    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=ProductionOrderResponse)
def get_production_order(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProductionOrder).filter(ProductionOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    return obj


@router.get("/", response_model=ProductionOrderPageResponse)
def list_production_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    code: Optional[str] = None,
    material_code: Optional[str] = None,
    order_status: Optional[str] = None,
    scheduling_status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ProductionOrder)
    if code:
        query = query.filter(ProductionOrder.code.contains(code))
    if material_code:
        query = query.filter(ProductionOrder.material_code.contains(material_code))
    if order_status:
        query = query.filter(ProductionOrder.order_status == order_status)
    if scheduling_status:
        query = query.filter(ProductionOrder.scheduling_status == scheduling_status)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ProductionOrderPageResponse(items=items, total=total, page=page, page_size=page_size)


class CanScheduleUpdate(BaseModel):
    can_schedule: bool


@router.put("/{id}/can-schedule", response_model=ProductionOrderResponse)
def update_can_schedule(id: str, data: CanScheduleUpdate, db: Session = Depends(get_db)):
    obj = db.query(ProductionOrder).filter(ProductionOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    obj.can_schedule = data.can_schedule
    db.commit()
    db.refresh(obj)
    return obj


class SortItem(BaseModel):
    id: str
    sequence: int


@router.put("/sort", status_code=200)
def update_sort(items: List[SortItem], db: Session = Depends(get_db)):
    for item in items:
        obj = db.query(ProductionOrder).filter(ProductionOrder.id == item.id).first()
        if obj:
            obj.sequence = item.sequence
    db.commit()
    return {"message": "排序更新成功"}


@router.get("/{id}/supplement-orders", response_model=List[ProductionOrderResponse])
def get_supplement_orders(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProductionOrder).filter(ProductionOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="订单不存在")
    supplements = db.query(ProductionOrder).filter(
        ProductionOrder.parent_order_code == obj.code,
        ProductionOrder.supplement == True,
    ).all()
    return supplements
