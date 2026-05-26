import uuid

from sqlalchemy import Column, String, Integer, Date, DateTime, Boolean, func, JSON

from app.core.database import Base


class WorkMode(Base):
    __tablename__ = "jvs_work_mode"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    time_periods = Column(JSON)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())


class WorkCalendar(Base):
    __tablename__ = "jvs_work_calendar"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    work_mode_id = Column(String(36))
    begin_time = Column(Date)
    end_time = Column(Date)
    enabled = Column(Boolean, default=True)
    work_days = Column(String(7))
    priority = Column(Integer, default=0)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())


class ResourceCalendar(Base):
    __tablename__ = "jvs_resource_calendar"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    resource_id = Column(String(36), nullable=False)
    calendar_id = Column(String(36), nullable=False)
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
