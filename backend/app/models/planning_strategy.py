import uuid

from sqlalchemy import Column, String, DateTime, Boolean, Enum, func, JSON

from app.core.database import Base


class PlanningStrategy(Base):
    __tablename__ = "jvs_planning_strategy"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    begin_time = Column(DateTime)
    active = Column(Boolean, default=True)
    config = Column(JSON)
    order_scheduling_rules = Column(JSON)
    optimize_rules = Column(JSON)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
