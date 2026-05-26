from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductionResourceCreate(BaseModel):
    name: str
    code: str
    resource_group: Optional[str] = None
    capacity: Optional[float] = None
    unit: Optional[str] = None
    throughput: Optional[str] = None
    resource_status: Optional[str] = None


class ProductionResourceUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    resource_group: Optional[str] = None
    capacity: Optional[float] = None
    unit: Optional[str] = None
    throughput: Optional[str] = None
    resource_status: Optional[str] = None


class ProductionResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    resource_group: Optional[str] = None
    capacity: Optional[float] = None
    unit: Optional[str] = None
    throughput: Optional[str] = None
    resource_status: Optional[str] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ProductionResourcePageResponse(BaseModel):
    items: List[ProductionResourceResponse]
    total: int
    page: int
    page_size: int
