import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Enum, func

from app.core.database import Base


class ProductionResource(Base):
    __tablename__ = "jvs_production_resource"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False)
    resource_group = Column(String(100))
    capacity = Column(Numeric(18, 6), default=1)
    unit = Column(String(50))
    throughput = Column(String(200))
    resource_status = Column(
        Enum("NORMAL", "MAINTENANCE", "SCRAPPED", name="resource_status_enum"),
        default="NORMAL",
    )
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
