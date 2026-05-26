import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Enum, UniqueConstraint, func, JSON

from app.core.database import Base


class Material(Base):
    __tablename__ = "jvs_material"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False)
    type = Column(
        Enum("RAW_MATERIAL", "SEMI_FINISHED", "FINISHED", name="material_type_enum"),
        nullable=False,
    )
    source = Column(
        Enum("PRODUCED", "PURCHASED", name="material_source_enum"),
        nullable=False,
    )
    quantity = Column(Numeric(18, 6), default=0)
    safety_stock = Column(Numeric(18, 6), default=0)
    unit = Column(String(50))
    lead_time = Column(String(50))
    buffer_time = Column(String(50))
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("code", "tenant_id", name="uq_material_code_tenant"),
    )
