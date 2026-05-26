from typing import Optional, List, Any
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class WorkModeCreate(BaseModel):
    name: str
    time_periods: Optional[Any] = None


class WorkModeUpdate(BaseModel):
    name: Optional[str] = None
    time_periods: Optional[Any] = None


class WorkModeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    time_periods: Optional[Any] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class WorkCalendarCreate(BaseModel):
    name: str
    work_mode_id: Optional[str] = None
    begin_time: Optional[date] = None
    end_time: Optional[date] = None
    enabled: Optional[bool] = None
    work_days: Optional[str] = None
    priority: Optional[int] = None
    resource_ids: Optional[List[str]] = None


class WorkCalendarUpdate(BaseModel):
    name: Optional[str] = None
    work_mode_id: Optional[str] = None
    begin_time: Optional[date] = None
    end_time: Optional[date] = None
    enabled: Optional[bool] = None
    work_days: Optional[str] = None
    priority: Optional[int] = None
    resource_ids: Optional[List[str]] = None


class WorkCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    work_mode_id: Optional[str] = None
    begin_time: Optional[date] = None
    end_time: Optional[date] = None
    enabled: Optional[bool] = None
    work_days: Optional[str] = None
    priority: Optional[int] = None
    resource_ids: Optional[List[str]] = None
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ResourceCalendarCreate(BaseModel):
    resource_id: str
    calendar_id: str


class ResourceCalendarUpdate(BaseModel):
    resource_id: Optional[str] = None
    calendar_id: Optional[str] = None


class ResourceCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_id: str
    calendar_id: str
    tenant_id: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
