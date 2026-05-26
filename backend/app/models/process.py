import uuid

from sqlalchemy import Column, String, DateTime, Enum, func, JSON

from app.core.database import Base


class Process(Base):
    __tablename__ = "jvs_process"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    code = Column(String(100), nullable=False)
    pre_interval_duration = Column(String(50))
    post_interval_duration = Column(String(50))
    process_relationship = Column(
        Enum("ES", "EE", name="process_relationship_enum"),
        default="ES",
    )
    buffer_time = Column(String(50))
    batch_strategy = Column(JSON)
    use_main_resources = Column(JSON)
    use_auxiliary_resources = Column(JSON)
    use_materials = Column(JSON)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
