from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PlanTaskCreate(BaseModel):
    code: str
    production_order_id: str
    scheduled_quantity: float
    process_code: str
    process_info: Optional[dict] = None
    front_task_codes: Optional[List[str]] = None
    next_task_codes: Optional[List[str]] = None
    main_order_id: Optional[str] = None
    start_task: Optional[bool] = False
    end_task: Optional[bool] = False
    input_materials: Optional[dict] = None


class PlanTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    merge_task_code: Optional[str] = None
    origin_task_code: Optional[str] = None
    main_order_id: Optional[str] = None
    production_order_id: str
    scheduled_quantity: Optional[float] = None
    process_code: str
    process_info: Optional[dict] = None
    front_task_codes: Optional[list] = None
    next_task_codes: Optional[list] = None
    main_resource_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    start_task: Optional[bool] = None
    end_task: Optional[bool] = None
    pinned: Optional[bool] = None
    merge_task: Optional[bool] = None
    input_materials: Optional[dict] = None
    task_status: Optional[str] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class PlanTaskPageResponse(BaseModel):
    items: List[PlanTaskResponse]
    total: int
    page: int
    page_size: int
