import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Integer, Boolean, Enum, func

from app.core.database import Base


class ProductionOrder(Base):
    __tablename__ = "jvs_production_order"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    code = Column(String(100), nullable=False)
    material_code = Column(String(100), nullable=False)
    quantity = Column(Numeric(18, 6), nullable=False)
    delivery_time = Column(DateTime)
    priority = Column(Integer, default=0)
    sequence = Column(Integer, default=0)
    type = Column(Enum("MANUFACTURE", name="order_type_enum"), default="MANUFACTURE")
    order_status = Column(Enum("PENDING", "COMPLETED", "CANCELLED", name="order_status_enum"), default="PENDING")
    scheduling_status = Column(Enum("UNSCHEDULED", "SCHEDULED", "COMPLETED", "NO_SCHEDULED", name="scheduling_status_enum"), default="UNSCHEDULED")
    can_schedule = Column(Boolean, default=True)
    supplement = Column(Boolean, default=False)
    parent_order_code = Column(String(100))
    color = Column(String(20))
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
