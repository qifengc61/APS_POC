from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.planning_strategy import PlanningStrategy
from app.schemas.planning_strategy import (
    PlanningStrategyCreate,
    PlanningStrategyUpdate,
    PlanningStrategyResponse,
    PlanningStrategyPageResponse,
    SchedulingRuleOption,
)

router = APIRouter(prefix="/api/planning-strategies", tags=["planning-strategies"])


@router.post("/", response_model=PlanningStrategyResponse, status_code=201)
def create_planning_strategy(data: PlanningStrategyCreate, db: Session = Depends(get_db)):
    obj = PlanningStrategy(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=PlanningStrategyResponse)
def update_planning_strategy(id: str, data: PlanningStrategyUpdate, db: Session = Depends(get_db)):
    obj = db.query(PlanningStrategy).filter(PlanningStrategy.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="策略不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


class ActiveUpdate(BaseModel):
    active: bool


@router.put("/{id}/active", response_model=PlanningStrategyResponse)
def update_active(id: str, data: ActiveUpdate, db: Session = Depends(get_db)):
    obj = db.query(PlanningStrategy).filter(PlanningStrategy.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="策略不存在")
    obj.active = data.active
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_planning_strategy(id: str, db: Session = Depends(get_db)):
    obj = db.query(PlanningStrategy).filter(PlanningStrategy.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="策略不存在")
    db.delete(obj)
    db.commit()


@router.get("/", response_model=PlanningStrategyPageResponse)
def list_planning_strategies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(PlanningStrategy)
    if name:
        query = query.filter(PlanningStrategy.name.contains(name))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return PlanningStrategyPageResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{id}", response_model=PlanningStrategyResponse)
def get_planning_strategy(id: str, db: Session = Depends(get_db)):
    obj = db.query(PlanningStrategy).filter(PlanningStrategy.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="策略不存在")
    return obj


@router.get("/scheduling-rule/options", response_model=List[SchedulingRuleOption])
def get_scheduling_rule_options():
    return [
        SchedulingRuleOption(field_key="priority", label="按优先级", sort_rule="DESC"),
        SchedulingRuleOption(field_key="delivery_time", label="按交期", sort_rule="ASC"),
        SchedulingRuleOption(field_key="quantity", label="按数量", sort_rule="DESC"),
        SchedulingRuleOption(field_key="create_time", label="按创建时间", sort_rule="ASC"),
    ]
