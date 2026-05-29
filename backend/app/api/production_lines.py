from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from ..database import get_db
from ..models.db_models import ProductionLine, Product, LineProduct

router = APIRouter(prefix="/api/lines", tags=["production_lines"])


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(default="", max_length=50)
    safety_stock: float = Field(default=0, ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    code: str = ""
    safety_stock: float

    class Config:
        from_attributes = True


class LineProductCreate(BaseModel):
    product_id: int
    rated_output: float = Field(..., gt=0)
    initial_inventory: float = Field(default=0, ge=0)
    safety_stock: float = Field(default=0, ge=0)


class LineProductOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_code: str = ""
    initial_inventory: float
    safety_stock: float
    rated_output: float

    class Config:
        from_attributes = True


class LineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    products: List[LineProductCreate] = Field(..., min_length=1, max_length=6)


class LineOut(BaseModel):
    id: int
    name: str
    products: List[LineProductOut]

    class Config:
        from_attributes = True


@router.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


@router.post("/products", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"物料名称 '{data.name}' 已存在")
    product = Product(name=data.name, code=data.code or None, safety_stock=data.safety_stock)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="物料不存在")
    existing = db.query(Product).filter(Product.name == data.name, Product.id != product_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"物料名称 '{data.name}' 已存在")
    product.name = data.name
    product.code = data.code or None
    product.safety_stock = data.safety_stock
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="物料不存在")
    db.delete(product)
    db.commit()
    return {"ok": True}


@router.get("", response_model=List[LineOut])
def list_lines(db: Session = Depends(get_db)):
    lines = db.query(ProductionLine).all()
    result = []
    for line in lines:
        lp_outs = []
        for lp in line.products:
            lp_outs.append(LineProductOut(
                id=lp.id,
                product_id=lp.product_id,
                product_name=lp.product.name,
                product_code=lp.product.code or "",
                initial_inventory=lp.initial_inventory,
                safety_stock=lp.safety_stock,
                rated_output=lp.rated_output,
            ))
        result.append(LineOut(id=line.id, name=line.name, products=lp_outs))
    return result


@router.post("", response_model=LineOut)
def create_line(data: LineCreate, db: Session = Depends(get_db)):
    existing = db.query(ProductionLine).filter(ProductionLine.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"产线名称 '{data.name}' 已存在")

    product_ids = [p.product_id for p in data.products]
    if len(set(product_ids)) != len(product_ids):
        raise HTTPException(status_code=400, detail="物料不能重复")

    for p in data.products:
        product = db.query(Product).filter(Product.id == p.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"物料ID {p.product_id} 不存在")

    line = ProductionLine(name=data.name)
    db.add(line)
    db.flush()

    for p in data.products:
        product = db.query(Product).filter(Product.id == p.product_id).first()
        lp = LineProduct(
            line_id=line.id,
            product_id=p.product_id,
            initial_inventory=0,
            safety_stock=product.safety_stock if product else 0,
            rated_output=p.rated_output,
        )
        db.add(lp)

    db.commit()
    db.refresh(line)

    lp_outs = []
    for lp in line.products:
        lp_outs.append(LineProductOut(
            id=lp.id,
            product_id=lp.product_id,
            product_name=lp.product.name,
            product_code=lp.product.code or "",
            initial_inventory=lp.initial_inventory,
            safety_stock=lp.safety_stock,
            rated_output=lp.rated_output,
        ))
    return LineOut(id=line.id, name=line.name, products=lp_outs)


@router.delete("/{line_id}")
def delete_line(line_id: int, db: Session = Depends(get_db)):
    line = db.query(ProductionLine).filter(ProductionLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="产线不存在")
    db.delete(line)
    db.commit()
    return {"ok": True}
