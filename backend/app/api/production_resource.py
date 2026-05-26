from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.production_resource import ProductionResource
from app.schemas.production_resource import (
    ProductionResourceCreate,
    ProductionResourceUpdate,
    ProductionResourceResponse,
    ProductionResourcePageResponse,
)

router = APIRouter(prefix="/api/production-resources", tags=["production-resources"])


@router.post("/", response_model=ProductionResourceResponse, status_code=201)
def create_production_resource(data: ProductionResourceCreate, db: Session = Depends(get_db)):
    obj = ProductionResource(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=ProductionResourceResponse)
def update_production_resource(id: str, data: ProductionResourceUpdate, db: Session = Depends(get_db)):
    obj = db.query(ProductionResource).filter(ProductionResource.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="生产资源不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_production_resource(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProductionResource).filter(ProductionResource.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="生产资源不存在")
    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=ProductionResourceResponse)
def get_production_resource(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProductionResource).filter(ProductionResource.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="生产资源不存在")
    return obj


@router.get("/", response_model=ProductionResourcePageResponse)
def list_production_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    code: Optional[str] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ProductionResource)
    if code:
        query = query.filter(ProductionResource.code.contains(code))
    if name:
        query = query.filter(ProductionResource.name.contains(name))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ProductionResourcePageResponse(items=items, total=total, page=page, page_size=page_size)
