from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class IncomingMaterialOrderCreate(BaseModel):
    material_id: str
    quantity: float
    expected_arrival_time: Optional[datetime] = None
    order_code: Optional[str] = None
    status: Optional[str] = None


class IncomingMaterialOrderUpdate(BaseModel):
    material_id: Optional[str] = None
    quantity: Optional[float] = None
    expected_arrival_time: Optional[datetime] = None
    order_code: Optional[str] = None
    status: Optional[str] = None


class IncomingMaterialOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    material_id: str
    quantity: float
    expected_arrival_time: Optional[datetime] = None
    order_code: Optional[str] = None
    status: Optional[str] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class IncomingMaterialOrderPageResponse(BaseModel):
    items: List[IncomingMaterialOrderResponse]
    total: int
    page: int
    page_size: int
