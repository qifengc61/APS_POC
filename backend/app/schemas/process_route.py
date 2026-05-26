from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProcessRouteCreate(BaseModel):
    material_id: str
    route_design: Optional[Any] = None
    enabled: Optional[bool] = None


class ProcessRouteUpdate(BaseModel):
    material_id: Optional[str] = None
    route_design: Optional[Any] = None
    enabled: Optional[bool] = None


class ProcessRouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    material_id: str
    route_design: Optional[Any] = None
    enabled: Optional[bool] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ProcessRoutePageResponse(BaseModel):
    items: List[ProcessRouteResponse]
    total: int
    page: int
    page_size: int
