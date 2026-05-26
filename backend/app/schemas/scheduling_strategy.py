from typing import List, Optional
from datetime import date
from pydantic import BaseModel


class SchedulingGenerateRequest(BaseModel):
    strategy_id: Optional[str] = None
    order_ids: Optional[List[str]] = None
    start_date: Optional[date] = None


class SchedulingGenerateResponse(BaseModel):
    task_id: str
    status: str


class SchedulingProgressResponse(BaseModel):
    status: str
    progress: Optional[float] = None
    step: Optional[str] = None
    logs: Optional[List[str]] = None


class SchedulingConfirmResponse(BaseModel):
    success: bool
    message: str


class GanttResource(BaseModel):
    id: str
    name: str
    tasks: List[dict]


class GanttDataResponse(BaseModel):
    resources: List[GanttResource]
