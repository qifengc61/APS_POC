import uuid

from sqlalchemy import Column, String, DateTime, Boolean, func, JSON

from app.core.database import Base


class ProcessRoute(Base):
    __tablename__ = "jvs_process_route"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    material_id = Column(String(36), nullable=False)
    route_design = Column(JSON)
    enabled = Column(Boolean, default=True)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
