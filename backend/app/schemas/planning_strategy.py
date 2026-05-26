from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PlanningStrategyCreate(BaseModel):
    name: str
    begin_time: Optional[datetime] = None
    active: Optional[bool] = True
    config: Optional[dict] = None
    order_scheduling_rules: Optional[List[dict]] = None
    optimize_rules: Optional[List[dict]] = None


class PlanningStrategyUpdate(BaseModel):
    name: Optional[str] = None
    begin_time: Optional[datetime] = None
    active: Optional[bool] = None
    config: Optional[dict] = None
    order_scheduling_rules: Optional[List[dict]] = None
    optimize_rules: Optional[List[dict]] = None


class PlanningStrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    begin_time: Optional[datetime] = None
    active: Optional[bool] = None
    config: Optional[dict] = None
    order_scheduling_rules: Optional[List[dict]] = None
    optimize_rules: Optional[List[dict]] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class PlanningStrategyPageResponse(BaseModel):
    items: List[PlanningStrategyResponse]
    total: int
    page: int
    page_size: int


class SchedulingRuleOption(BaseModel):
    field_key: str
    label: str
    sort_rule: str = "ASC"
