from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.now)

    products = relationship("LineProduct", back_populates="line", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(50), nullable=True, unique=False)
    safety_stock = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.now)

    line_associations = relationship("LineProduct", back_populates="product", cascade="all, delete-orphan")


class LineProduct(Base):
    __tablename__ = "line_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_id = Column(Integer, ForeignKey("production_lines.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    initial_inventory = Column(Float, nullable=False, default=0)
    safety_stock = Column(Float, nullable=False, default=0)
    rated_output = Column(Float, nullable=False, default=0)

    line = relationship("ProductionLine", back_populates="products")
    product = relationship("Product", back_populates="line_associations")


class DeliveryPlan(Base):
    __tablename__ = "delivery_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    line_id = Column(Integer, ForeignKey("production_lines.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    line = relationship("ProductionLine")
    materials = relationship("PlanMaterial", back_populates="plan", cascade="all, delete-orphan", order_by="PlanMaterial.sort_order")


class PlanMaterial(Base):
    __tablename__ = "plan_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("delivery_plans.id", ondelete="CASCADE"), nullable=False)
    line_product_id = Column(Integer, ForeignKey("line_products.id", ondelete="CASCADE"), nullable=False)
    initial_inventory = Column(Float, nullable=False, default=0)
    total_delivery = Column(Float, nullable=False, default=0)
    daily_deliveries = Column(Text, nullable=True, default=None)
    sort_order = Column(Integer, nullable=False, default=0)

    plan = relationship("DeliveryPlan", back_populates="materials")
    line_product = relationship("LineProduct")
