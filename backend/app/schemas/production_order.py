from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductionOrderCreate(BaseModel):
    code: str
    material_code: str
    quantity: float
    delivery_time: Optional[datetime] = None
    priority: Optional[int] = 0
    sequence: Optional[int] = 0
    can_schedule: Optional[bool] = True
    supplement: Optional[bool] = False
    parent_order_code: Optional[str] = None
    color: Optional[str] = None
    order_status: Optional[str] = "PENDING"
    scheduling_status: Optional[str] = "UNSCHEDULED"


class ProductionOrderUpdate(BaseModel):
    code: Optional[str] = None
    material_code: Optional[str] = None
    quantity: Optional[float] = None
    delivery_time: Optional[datetime] = None
    priority: Optional[int] = None
    sequence: Optional[int] = None
    can_schedule: Optional[bool] = None
    supplement: Optional[bool] = None
    parent_order_code: Optional[str] = None
    color: Optional[str] = None
    order_status: Optional[str] = None
    scheduling_status: Optional[str] = None


class ProductionOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    material_code: str
    quantity: Optional[float] = None
    delivery_time: Optional[datetime] = None
    priority: Optional[int] = None
    sequence: Optional[int] = None
    type: Optional[str] = None
    order_status: Optional[str] = None
    scheduling_status: Optional[str] = None
    can_schedule: Optional[bool] = None
    supplement: Optional[bool] = None
    parent_order_code: Optional[str] = None
    color: Optional[str] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ProductionOrderPageResponse(BaseModel):
    items: List[ProductionOrderResponse]
    total: int
    page: int
    page_size: int
