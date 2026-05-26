from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.manufacture_bom import ManufactureBOM
from app.schemas.manufacture_bom import (
    ManufactureBOMCreate,
    ManufactureBOMUpdate,
    ManufactureBOMResponse,
    ManufactureBOMPageResponse,
)

router = APIRouter(prefix="/api/manufacture-boms", tags=["manufacture-boms"])


@router.post("/", response_model=ManufactureBOMResponse, status_code=201)
def create_manufacture_bom(data: ManufactureBOMCreate, db: Session = Depends(get_db)):
    obj = ManufactureBOM(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=ManufactureBOMResponse)
def update_manufacture_bom(id: str, data: ManufactureBOMUpdate, db: Session = Depends(get_db)):
    obj = db.query(ManufactureBOM).filter(ManufactureBOM.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="制造BOM不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_manufacture_bom(id: str, db: Session = Depends(get_db)):
    obj = db.query(ManufactureBOM).filter(ManufactureBOM.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="制造BOM不存在")
    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=ManufactureBOMResponse)
def get_manufacture_bom(id: str, db: Session = Depends(get_db)):
    obj = db.query(ManufactureBOM).filter(ManufactureBOM.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="制造BOM不存在")
    return obj


@router.get("/", response_model=ManufactureBOMPageResponse)
def list_manufacture_boms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    material_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ManufactureBOM)
    if material_id:
        query = query.filter(ManufactureBOM.material_id == material_id)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ManufactureBOMPageResponse(items=items, total=total, page=page, page_size=page_size)
