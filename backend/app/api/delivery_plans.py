import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models.db_models import DeliveryPlan, ProductionLine, LineProduct, PlanMaterial

router = APIRouter(prefix="/api/delivery-plans", tags=["delivery_plans"])


class PlanMaterialItem(BaseModel):
    line_product_id: int
    initial_inventory: float = Field(default=0, ge=0)
    total_delivery: float = Field(default=0, ge=0)
    daily_deliveries: str = Field(default="", description="空格分隔的每日交货量")


class DeliveryPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    line_id: int
    materials: List[PlanMaterialItem] = Field(..., min_length=1, max_length=6)
    start_date: date
    end_date: date


class PlanMaterialOut(BaseModel):
    line_product_id: int
    product_name: str
    product_code: str = ""
    initial_inventory: float
    safety_stock: float
    rated_output: float
    total_delivery: float
    daily_deliveries: str = ""

    class Config:
        from_attributes = True


class DeliveryPlanOut(BaseModel):
    id: int
    name: str
    line_id: int
    line_name: str
    materials: List[PlanMaterialOut]
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


def _build_plan_out(plan: DeliveryPlan) -> DeliveryPlanOut:
    material_outs = []
    for pm in plan.materials:
        lp = pm.line_product
        dd = pm.daily_deliveries or ""
        material_outs.append(PlanMaterialOut(
            line_product_id=pm.line_product_id,
            product_name=lp.product.name,
            product_code=lp.product.code or "",
            initial_inventory=pm.initial_inventory,
            safety_stock=lp.safety_stock,
            rated_output=lp.rated_output,
            total_delivery=pm.total_delivery,
            daily_deliveries=dd,
        ))
    return DeliveryPlanOut(
        id=plan.id,
        name=plan.name,
        line_id=plan.line_id,
        line_name=plan.line.name,
        materials=material_outs,
        start_date=plan.start_date,
        end_date=plan.end_date,
    )


def _parse_daily_deliveries(daily_str: str) -> str:
    if not daily_str or not daily_str.strip():
        return ""
    parts = daily_str.strip().split()
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"每日交货量格式错误: '{p}' 不是有效数字")
    return json.dumps(nums, ensure_ascii=False)


@router.get("", response_model=List[DeliveryPlanOut])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(DeliveryPlan).order_by(DeliveryPlan.id.desc()).all()
    return [_build_plan_out(p) for p in plans]


@router.get("/{plan_id}", response_model=DeliveryPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(DeliveryPlan).filter(DeliveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="交货计划不存在")
    return _build_plan_out(plan)


@router.post("", response_model=DeliveryPlanOut)
def create_plan(data: DeliveryPlanCreate, db: Session = Depends(get_db)):
    line = db.query(ProductionLine).filter(ProductionLine.id == data.line_id).first()
    if not line:
        raise HTTPException(status_code=400, detail="产线不存在")
    if data.end_date <= data.start_date:
        raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")

    lp_ids = [m.line_product_id for m in data.materials]
    if len(set(lp_ids)) != len(lp_ids):
        raise HTTPException(status_code=400, detail="物料不能重复")

    days = (data.end_date - data.start_date).days + 1

    for m in data.materials:
        lp = db.query(LineProduct).filter(LineProduct.id == m.line_product_id).first()
        if not lp:
            raise HTTPException(status_code=400, detail=f"产线物料关联ID {m.line_product_id} 不存在")
        if lp.line_id != data.line_id:
            raise HTTPException(status_code=400, detail=f"物料 '{lp.product.name}' 不属于该产线")
        if m.daily_deliveries and m.daily_deliveries.strip():
            parts = m.daily_deliveries.strip().split()
            if len(parts) != days:
                raise HTTPException(status_code=400, detail=f"物料 '{lp.product.name}' 的每日交货量数量({len(parts)})与排产天数({days})不匹配")

    plan = DeliveryPlan(
        name=data.name,
        line_id=data.line_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(plan)
    db.flush()

    for idx, m in enumerate(data.materials):
        dd_json = _parse_daily_deliveries(m.daily_deliveries)
        total = m.total_delivery
        if dd_json:
            vals = json.loads(dd_json)
            total = sum(vals)
        pm = PlanMaterial(
            plan_id=plan.id,
            line_product_id=m.line_product_id,
            initial_inventory=m.initial_inventory,
            total_delivery=total,
            daily_deliveries=dd_json or None,
            sort_order=idx,
        )
        db.add(pm)

    db.commit()
    db.refresh(plan)
    return _build_plan_out(plan)


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(DeliveryPlan).filter(DeliveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="交货计划不存在")
    db.delete(plan)
    db.commit()
    return {"ok": True}
