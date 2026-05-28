from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from ..database import get_db
from ..models.db_models import ProductionLine, Product, LineProduct

router = APIRouter(prefix="/api/lines", tags=["production_lines"])


class LineProductCreate(BaseModel):
    product_id: int
    rated_output: float = Field(..., gt=0)


class LineProductOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    initial_inventory: float
    safety_stock: float
    rated_output: float

    class Config:
        from_attributes = True


class LineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    products: List[LineProductCreate] = Field(default_factory=list)


class LineOut(BaseModel):
    id: int
    name: str
    products: List[LineProductOut] = []

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(default="", max_length=50, description="物料代码")
    safety_stock: float = Field(default=0, ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    code: str | None = ""
    safety_stock: float

    class Config:
        from_attributes = True


@router.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()


@router.post("/products", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"物料名称 '{data.name}' 已存在")
    p = Product(name=data.name, code=data.code, safety_stock=data.safety_stock)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="物料不存在")
    conflict = db.query(Product).filter(Product.name == data.name, Product.id != product_id).first()
    if conflict:
        raise HTTPException(status_code=400, detail=f"物料名称 '{data.name}' 已存在")
    p.name = data.name
    p.code = data.code
    p.safety_stock = data.safety_stock
    db.commit()
    db.refresh(p)
    return p


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="物料不存在")
    db.delete(p)
    db.commit()
    return {"ok": True}


@router.get("", response_model=List[LineOut])
def list_lines(db: Session = Depends(get_db)):
    lines = db.query(ProductionLine).order_by(ProductionLine.id).all()
    result = []
    for line in lines:
        lp_list = []
        for lp in line.products:
            lp_list.append(LineProductOut(
                id=lp.id,
                product_id=lp.product_id,
                product_name=lp.product.name,
                initial_inventory=lp.initial_inventory,
                safety_stock=lp.safety_stock,
                rated_output=lp.rated_output,
            ))
        result.append(LineOut(id=line.id, name=line.name, products=lp_list))
    return result


@router.post("", response_model=LineOut)
def create_line(data: LineCreate, db: Session = Depends(get_db)):
    existing = db.query(ProductionLine).filter(ProductionLine.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"产线名称 '{data.name}' 已存在")
    line = ProductionLine(name=data.name)
    db.add(line)
    db.flush()
    for pc in data.products:
        product = db.query(Product).filter(Product.id == pc.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"物料ID {pc.product_id} 不存在")
        lp = LineProduct(
            line_id=line.id,
            product_id=pc.product_id,
            initial_inventory=0,
            safety_stock=product.safety_stock,
            rated_output=pc.rated_output,
        )
        db.add(lp)
    db.commit()
    db.refresh(line)
    lp_list = []
    for lp in line.products:
        lp_list.append(LineProductOut(
            id=lp.id,
            product_id=lp.product_id,
            product_name=lp.product.name,
            initial_inventory=lp.initial_inventory,
            safety_stock=lp.safety_stock,
            rated_output=lp.rated_output,
        ))
    return LineOut(id=line.id, name=line.name, products=lp_list)


@router.delete("/{line_id}")
def delete_line(line_id: int, db: Session = Depends(get_db)):
    line = db.query(ProductionLine).filter(ProductionLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="产线不存在")
    db.delete(line)
    db.commit()
    return {"ok": True}
