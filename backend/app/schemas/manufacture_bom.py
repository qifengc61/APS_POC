from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ManufactureBOMCreate(BaseModel):
    material_id: str
    child_materials: Optional[Any] = None


class ManufactureBOMUpdate(BaseModel):
    material_id: Optional[str] = None
    child_materials: Optional[Any] = None


class ManufactureBOMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    material_id: str
    child_materials: Optional[Any] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ManufactureBOMPageResponse(BaseModel):
    items: List[ManufactureBOMResponse]
    total: int
    page: int
    page_size: int
