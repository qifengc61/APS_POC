from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.incoming_material_order import IncomingMaterialOrder
from app.schemas.incoming_material_order import (
    IncomingMaterialOrderCreate,
    IncomingMaterialOrderUpdate,
    IncomingMaterialOrderResponse,
    IncomingMaterialOrderPageResponse,
)

router = APIRouter(prefix="/api/incoming-material-orders", tags=["incoming-material-orders"])


@router.post("/", response_model=IncomingMaterialOrderResponse, status_code=201)
def create_incoming_material_order(data: IncomingMaterialOrderCreate, db: Session = Depends(get_db)):
    obj = IncomingMaterialOrder(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=IncomingMaterialOrderResponse)
def update_incoming_material_order(id: str, data: IncomingMaterialOrderUpdate, db: Session = Depends(get_db)):
    obj = db.query(IncomingMaterialOrder).filter(IncomingMaterialOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="来料订单不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_incoming_material_order(id: str, db: Session = Depends(get_db)):
    obj = db.query(IncomingMaterialOrder).filter(IncomingMaterialOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="来料订单不存在")
    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=IncomingMaterialOrderResponse)
def get_incoming_material_order(id: str, db: Session = Depends(get_db)):
    obj = db.query(IncomingMaterialOrder).filter(IncomingMaterialOrder.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="来料订单不存在")
    return obj


@router.get("/", response_model=IncomingMaterialOrderPageResponse)
def list_incoming_material_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    material_id: Optional[str] = None,
    order_code: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(IncomingMaterialOrder)
    if material_id:
        query = query.filter(IncomingMaterialOrder.material_id == material_id)
    if order_code:
        query = query.filter(IncomingMaterialOrder.order_code.contains(order_code))
    if status:
        query = query.filter(IncomingMaterialOrder.status == status)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return IncomingMaterialOrderPageResponse(items=items, total=total, page=page, page_size=page_size)
