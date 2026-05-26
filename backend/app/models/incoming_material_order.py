import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Enum, func

from app.core.database import Base


class IncomingMaterialOrder(Base):
    __tablename__ = "jvs_incoming_material_order"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    material_id = Column(String(36), nullable=False)
    quantity = Column(Numeric(18, 6), nullable=False)
    expected_arrival_time = Column(DateTime)
    order_code = Column(String(100))
    status = Column(
        Enum("PENDING", "ARRIVED", "CANCELLED", name="incoming_order_status_enum"),
        default="PENDING",
    )
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
