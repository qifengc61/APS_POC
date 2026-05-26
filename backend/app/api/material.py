from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.material import Material
from app.schemas.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialResponse,
    MaterialPageResponse,
)

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.post("/", response_model=MaterialResponse, status_code=201)
def create_material(data: MaterialCreate, db: Session = Depends(get_db)):
    existing = db.query(Material).filter(Material.code == data.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="物料编码已存在")
    obj = Material(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=MaterialResponse)
def update_material(id: str, data: MaterialUpdate, db: Session = Depends(get_db)):
    obj = db.query(Material).filter(Material.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="物料不存在")
    update_data = data.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"] != obj.code:
        existing = db.query(Material).filter(Material.code == update_data["code"]).first()
        if existing:
            raise HTTPException(status_code=409, detail="物料编码已存在")
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_material(id: str, db: Session = Depends(get_db)):
    obj = db.query(Material).filter(Material.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="物料不存在")
    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=MaterialResponse)
def get_material(id: str, db: Session = Depends(get_db)):
    obj = db.query(Material).filter(Material.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="物料不存在")
    return obj


@router.get("/", response_model=MaterialPageResponse)
def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    code: Optional[str] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Material)
    if code:
        query = query.filter(Material.code.contains(code))
    if name:
        query = query.filter(Material.name.contains(name))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return MaterialPageResponse(items=items, total=total, page=page, page_size=page_size)
