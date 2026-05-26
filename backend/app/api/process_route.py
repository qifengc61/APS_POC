from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.process_route import ProcessRoute
from app.schemas.process_route import (
    ProcessRouteCreate,
    ProcessRouteUpdate,
    ProcessRouteResponse,
    ProcessRoutePageResponse,
)
from app.utils.graph import build_graph_from_route_design, has_cycle, has_multiple_endpoints

router = APIRouter(prefix="/api/process-routes", tags=["process-routes"])


def _validate_route_design(route_design):
    if not route_design:
        return
    graph = build_graph_from_route_design(route_design)
    if has_cycle(graph):
        raise HTTPException(status_code=400, detail="工艺路线不允许存在环")
    if has_multiple_endpoints(graph):
        raise HTTPException(status_code=400, detail="工艺路线应只有一个终点节点")


@router.post("/", response_model=ProcessRouteResponse, status_code=201)
def create_process_route(data: ProcessRouteCreate, db: Session = Depends(get_db)):
    _validate_route_design(data.route_design)
    obj = ProcessRoute(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=ProcessRouteResponse)
def update_process_route(id: str, data: ProcessRouteUpdate, db: Session = Depends(get_db)):
    obj = db.query(ProcessRoute).filter(ProcessRoute.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    update_data = data.model_dump(exclude_unset=True)
    route_design = update_data.get("route_design", obj.route_design)
    _validate_route_design(route_design)
    for key, value in update_data.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=204)
def delete_process_route(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProcessRoute).filter(ProcessRoute.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    db.delete(obj)
    db.commit()


@router.get("/{id}", response_model=ProcessRouteResponse)
def get_process_route(id: str, db: Session = Depends(get_db)):
    obj = db.query(ProcessRoute).filter(ProcessRoute.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="工艺路线不存在")
    return obj


@router.get("/", response_model=ProcessRoutePageResponse)
def list_process_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    material_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ProcessRoute)
    if material_id:
        query = query.filter(ProcessRoute.material_id == material_id)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ProcessRoutePageResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/validate")
def validate_route_design(route_design: dict):
    _validate_route_design(route_design)
    return {"valid": True, "message": "工艺路线校验通过"}
