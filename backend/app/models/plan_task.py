import uuid

from sqlalchemy import Column, String, Numeric, DateTime, Integer, Boolean, Enum, func, JSON

from app.core.database import Base


class PlanTask(Base):
    __tablename__ = "jvs_plan_task"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    code = Column(String(100), nullable=False)
    merge_task_code = Column(String(100))
    origin_task_code = Column(String(100))
    main_order_id = Column(String(36))
    production_order_id = Column(String(36), nullable=False)
    scheduled_quantity = Column(Numeric(18, 6), nullable=False)
    process_code = Column(String(100), nullable=False)
    process_info = Column(JSON)
    front_task_codes = Column(JSON)
    next_task_codes = Column(JSON)
    main_resource_id = Column(String(36))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    start_task = Column(Boolean, default=False)
    end_task = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False)
    merge_task = Column(Boolean, default=False)
    input_materials = Column(JSON)
    task_status = Column(
        Enum("PENDING", "PARTIALLY_COMPLETED", "COMPLETED", name="task_status_enum"),
        default="PENDING",
    )
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())


class PlanTaskPending(Base):
    __tablename__ = "jvs_plan_task_pending"

    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    code = Column(String(100), nullable=False)
    merge_task_code = Column(String(100))
    origin_task_code = Column(String(100))
    main_order_id = Column(String(36))
    production_order_id = Column(String(36), nullable=False)
    scheduled_quantity = Column(Numeric(18, 6), nullable=False)
    process_code = Column(String(100), nullable=False)
    process_info = Column(JSON)
    front_task_codes = Column(JSON)
    next_task_codes = Column(JSON)
    main_resource_id = Column(String(36))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    start_task = Column(Boolean, default=False)
    end_task = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False)
    merge_task = Column(Boolean, default=False)
    input_materials = Column(JSON)
    task_status = Column(
        Enum("PENDING", "PARTIALLY_COMPLETED", "COMPLETED", name="task_status_enum"),
        default="PENDING",
    )
    tenant_id = Column(String(36), default="default")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
