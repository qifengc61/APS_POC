from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.process import Process
from app.schemas.process import (
    ProcessCreate,
    ProcessUpdate,
    ProcessResponse,
    ProcessPageResponse,
)

router = APIRouter(prefix="/api/processes", tags=["processes"])


@router.post("/", response_model=ProcessResponse, status_code=201)
def create_process(data: ProcessCreate, db: Session = Depends(get_db)):
    obj = Process(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=ProcessResponse)
def update_process(id: str, data: ProcessUpdate, db: Session = Depends(get_db)):
    obj = db.query(Process).filter(Process.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工序不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_process(id: str, db: Session = Depends(get_db)):
    obj = db.query(Process).filter(Process.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工序不存在")
    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=ProcessResponse)
def get_process(id: str, db: Session = Depends(get_db)):
    obj = db.query(Process).filter(Process.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工序不存在")
    return obj


@router.get("/", response_model=ProcessPageResponse)
def list_processes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    code: Optional[str] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Process)
    if code:
        query = query.filter(Process.code.contains(code))
    if name:
        query = query.filter(Process.name.contains(name))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ProcessPageResponse(items=items, total=total, page=page, page_size=page_size)
