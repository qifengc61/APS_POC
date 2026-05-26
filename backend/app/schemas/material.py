from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MaterialCreate(BaseModel):
    code: str
    name: str
    type: str
    source: str
    quantity: Optional[float] = None
    safety_stock: Optional[float] = None
    unit: Optional[str] = None
    lead_time: Optional[str] = None
    buffer_time: Optional[str] = None


class MaterialUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    source: Optional[str] = None
    quantity: Optional[float] = None
    safety_stock: Optional[float] = None
    unit: Optional[str] = None
    lead_time: Optional[str] = None
    buffer_time: Optional[str] = None


class MaterialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    type: str
    source: str
    quantity: Optional[float] = None
    safety_stock: Optional[float] = None
    unit: Optional[str] = None
    lead_time: Optional[str] = None
    buffer_time: Optional[str] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class MaterialPageResponse(BaseModel):
    items: List[MaterialResponse]
    total: int
    page: int
    page_size: int
