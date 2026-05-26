import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Integer, func

from app.core.database import Base


class PlanTaskOrder(Base):
    __tablename__ = "jvs_plan_task_order"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    production_order_id = Column(String(36), nullable=False)
    order_code = Column(String(100))
    material_code = Column(String(100))
    quantity = Column(Numeric(18, 6))
    delivery_time = Column(DateTime)
    priority = Column(Integer, default=0)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())


class PlanTaskOrderPending(Base):
    __tablename__ = "jvs_plan_task_order_pending"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    production_order_id = Column(String(36), nullable=False)
    order_code = Column(String(100))
    material_code = Column(String(100))
    quantity = Column(Numeric(18, 6))
    delivery_time = Column(DateTime)
    priority = Column(Integer, default=0)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
