import uuid

from sqlalchemy import Column, String, DateTime, func, JSON

from app.core.database import Base


class ManufactureBOM(Base):
    __tablename__ = "jvs_manufacture_bom"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    material_id = Column(String(36), nullable=False)
    child_materials = Column(JSON)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
