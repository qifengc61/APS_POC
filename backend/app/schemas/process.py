from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProcessCreate(BaseModel):
    name: str
    code: str
    pre_interval_duration: Optional[str] = None
    post_interval_duration: Optional[str] = None
    process_relationship: Optional[str] = None
    buffer_time: Optional[str] = None
    batch_strategy: Optional[Any] = None
    use_main_resources: Optional[Any] = None
    use_auxiliary_resources: Optional[Any] = None
    use_materials: Optional[Any] = None


class ProcessUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    pre_interval_duration: Optional[str] = None
    post_interval_duration: Optional[str] = None
    process_relationship: Optional[str] = None
    buffer_time: Optional[str] = None
    batch_strategy: Optional[Any] = None
    use_main_resources: Optional[Any] = None
    use_auxiliary_resources: Optional[Any] = None
    use_materials: Optional[Any] = None


class ProcessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    pre_interval_duration: Optional[str] = None
    post_interval_duration: Optional[str] = None
    process_relationship: Optional[str] = None
    buffer_time: Optional[str] = None
    batch_strategy: Optional[Any] = None
    use_main_resources: Optional[Any] = None
    use_auxiliary_resources: Optional[Any] = None
    use_materials: Optional[Any] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ProcessPageResponse(BaseModel):
    items: List[ProcessResponse]
    total: int
    page: int
    page_size: int
