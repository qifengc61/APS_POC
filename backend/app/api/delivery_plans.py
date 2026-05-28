import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from ..database import get_db
from ..models.db_models import DeliveryPlan, ProductionLine, LineProduct

router = APIRouter(prefix="/api/delivery-plans", tags=["delivery_plans"])


class PlanMaterialItem(BaseModel):
    line_product_id: int
    initial_inventory: float = Field(default=0, ge=0)
    total_delivery: float = Field(default=0, ge=0)
    daily_deliveries: str = Field(default="", description="空格分隔的每日交货量")


class DeliveryPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    line_id: int
    materials: List[PlanMaterialItem] = Field(..., min_length=2, max_length=2)
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
    lpa = plan.line_product_1
    lpb = plan.line_product_2
    dd_1 = plan.daily_deliveries_1 or ""
    dd_2 = plan.daily_deliveries_2 or ""
    return DeliveryPlanOut(
        id=plan.id,
        name=plan.name,
        line_id=plan.line_id,
        line_name=plan.line.name,
        materials=[
            PlanMaterialOut(
                line_product_id=plan.product_1_id,
                product_name=lpa.product.name,
                product_code=lpa.product.code or "",
                initial_inventory=plan.initial_inventory_1,
                safety_stock=lpa.safety_stock,
                rated_output=lpa.rated_output,
                total_delivery=plan.total_delivery_1,
                daily_deliveries=dd_1,
            ),
            PlanMaterialOut(
                line_product_id=plan.product_2_id,
                product_name=lpb.product.name,
                product_code=lpb.product.code or "",
                initial_inventory=plan.initial_inventory_2,
                safety_stock=lpb.safety_stock,
                rated_output=lpb.rated_output,
                total_delivery=plan.total_delivery_2,
                daily_deliveries=dd_2,
            ),
        ],
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

    lps = []
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
        lps.append(lp)

    total_1 = data.materials[0].total_delivery
    total_2 = data.materials[1].total_delivery
    dd_json_1 = _parse_daily_deliveries(data.materials[0].daily_deliveries)
    dd_json_2 = _parse_daily_deliveries(data.materials[1].daily_deliveries)

    if dd_json_1:
        vals = json.loads(dd_json_1)
        total_1 = sum(vals)
    if dd_json_2:
        vals = json.loads(dd_json_2)
        total_2 = sum(vals)

    plan = DeliveryPlan(
        name=data.name,
        line_id=data.line_id,
        product_1_id=data.materials[0].line_product_id,
        product_2_id=data.materials[1].line_product_id,
        initial_inventory_1=data.materials[0].initial_inventory,
        initial_inventory_2=data.materials[1].initial_inventory,
        start_date=data.start_date,
        end_date=data.end_date,
        total_delivery_1=total_1,
        total_delivery_2=total_2,
        daily_deliveries_1=dd_json_1 or None,
        daily_deliveries_2=dd_json_2 or None,
    )
    db.add(plan)
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