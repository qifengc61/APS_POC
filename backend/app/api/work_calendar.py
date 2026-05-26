from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.work_calendar import WorkMode, WorkCalendar, ResourceCalendar
from app.schemas.work_calendar import (
    WorkModeCreate,
    WorkModeUpdate,
    WorkModeResponse,
    WorkCalendarCreate,
    WorkCalendarUpdate,
    WorkCalendarResponse,
    ResourceCalendarCreate,
    ResourceCalendarUpdate,
    ResourceCalendarResponse,
)

router = APIRouter(prefix="/api", tags=["work-calendar"])


@router.post("/work-modes", response_model=WorkModeResponse, status_code=201)
def create_work_mode(data: WorkModeCreate, db: Session = Depends(get_db)):
    obj = WorkMode(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/work-modes/{id}", response_model=WorkModeResponse)
def update_work_mode(id: str, data: WorkModeUpdate, db: Session = Depends(get_db)):
    obj = db.query(WorkMode).filter(WorkMode.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工作模式不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/work-modes/{id}", status_code=204)
def delete_work_mode(id: str, db: Session = Depends(get_db)):
    obj = db.query(WorkMode).filter(WorkMode.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工作模式不存在")
    db.delete(obj)
    db.commit()


@router.get("/work-modes/{id}", response_model=WorkModeResponse)
def get_work_mode(id: str, db: Session = Depends(get_db)):
    obj = db.query(WorkMode).filter(WorkMode.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工作模式不存在")
    return obj


@router.get("/work-modes", response_model=list[WorkModeResponse])
def list_work_modes(db: Session = Depends(get_db)):
    return db.query(WorkMode).all()


@router.post("/work-calendars", response_model=WorkCalendarResponse, status_code=201)
def create_work_calendar(data: WorkCalendarCreate, db: Session = Depends(get_db)):
    resource_ids = data.resource_ids or []
    cal_data = data.model_dump(exclude={"resource_ids"})
    obj = WorkCalendar(**cal_data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _sync_resources(db, obj.id, resource_ids)
    return _calendar_with_resources(db, obj)


@router.put("/work-calendars/{id}", response_model=WorkCalendarResponse)
def update_work_calendar(id: str, data: WorkCalendarUpdate, db: Session = Depends(get_db)):
    obj = db.query(WorkCalendar).filter(WorkCalendar.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工作日历不存在")
    resource_ids = data.resource_ids
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("resource_ids", None)
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    if resource_ids is not None:
        _sync_resources(db, obj.id, resource_ids)
    return _calendar_with_resources(db, obj)


@router.delete("/work-calendars/{id}", status_code=204)
def delete_work_calendar(id: str, db: Session = Depends(get_db)):
    obj = db.query(WorkCalendar).filter(WorkCalendar.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工作日历不存在")
    db.query(ResourceCalendar).filter(ResourceCalendar.calendar_id == id).delete()
    db.delete(obj)
    db.commit()


@router.get("/work-calendars/{id}", response_model=WorkCalendarResponse)
def get_work_calendar(id: str, db: Session = Depends(get_db)):
    obj = db.query(WorkCalendar).filter(WorkCalendar.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工作日历不存在")
    return _calendar_with_resources(db, obj)


@router.get("/work-calendars", response_model=list[WorkCalendarResponse])
def list_work_calendars(db: Session = Depends(get_db)):
    calendars = db.query(WorkCalendar).all()
    return [_calendar_with_resources(db, c) for c in calendars]


def _sync_resources(db: Session, calendar_id: str, resource_ids: list):
    db.query(ResourceCalendar).filter(ResourceCalendar.calendar_id == calendar_id).delete()
    for rid in resource_ids:
        db.add(ResourceCalendar(resource_id=rid, calendar_id=calendar_id))
    db.commit()


def _calendar_with_resources(db: Session, cal: WorkCalendar):
    linked = db.query(ResourceCalendar.resource_id).filter(
        ResourceCalendar.calendar_id == cal.id
    ).all()
    result = WorkCalendarResponse.model_validate(cal)
    result.resource_ids = [r[0] for r in linked]
    return result


@router.post("/resource-calendars", response_model=ResourceCalendarResponse, status_code=201)
def create_resource_calendar(data: ResourceCalendarCreate, db: Session = Depends(get_db)):
    obj = ResourceCalendar(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/resource-calendars/{id}", response_model=ResourceCalendarResponse)
def update_resource_calendar(id: str, data: ResourceCalendarUpdate, db: Session = Depends(get_db)):
    obj = db.query(ResourceCalendar).filter(ResourceCalendar.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="资源日历不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/resource-calendars/{id}", status_code=204)
def delete_resource_calendar(id: str, db: Session = Depends(get_db)):
    obj = db.query(ResourceCalendar).filter(ResourceCalendar.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="资源日历不存在")
    db.delete(obj)
    db.commit()


@router.get("/resource-calendars/{id}", response_model=ResourceCalendarResponse)
def get_resource_calendar(id: str, db: Session = Depends(get_db)):
    obj = db.query(ResourceCalendar).filter(ResourceCalendar.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="资源日历不存在")
    return obj


@router.get("/resource-calendars", response_model=list[ResourceCalendarResponse])
def list_resource_calendars(db: Session = Depends(get_db)):
    return db.query(ResourceCalendar).all()
