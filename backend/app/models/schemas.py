from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class SchedulingParams(BaseModel):
    initial_inventory: float = Field(..., gt=0, description="初期库存")
    safety_stock: float = Field(..., gt=0, description="安全库存")
    rated_output: float = Field(..., gt=0, description="单班基础额定产量")
    total_delivery: float = Field(..., gt=0, description="周期计划总交货量")
    start_date: date = Field(..., description="排产开始日期")
    end_date: date = Field(..., description="排产结束日期")
    holidays: List[str] = Field(default_factory=list, description="节假日列表(YYYY-MM-DD)")
    daily_deliveries: Optional[List[dict]] = Field(default=None, description="每日交货量明细")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("结束日期必须晚于开始日期")
        return v

    @field_validator("safety_stock")
    @classmethod
    def validate_safety_stock(cls, v, info):
        if info.data.get("initial_inventory") and v > info.data["initial_inventory"]:
            raise ValueError("安全库存不能大于初期库存")
        return v


class AlgorithmConfig(BaseModel):
    overtime_shift_weight: float = Field(default=50.0, ge=0.0, le=100.0, description="加班班次权重")
    overtime_day_weight: float = Field(default=50.0, ge=0.0, le=100.0, description="加班天数权重")
    rest_day_weight: float = Field(default=50.0, ge=0.0, le=100.0, description="占用休息日权重")
    max_consecutive_work_days: int = Field(default=7, ge=3, le=14, description="最大连续工作天数")
    max_time_seconds: int = Field(default=10, ge=10, le=60, description="求解限时(秒)")


class SchedulingRequest(BaseModel):
    params: SchedulingParams
    config: AlgorithmConfig = AlgorithmConfig()


class DailyResult(BaseModel):
    date: str
    is_holiday: bool
    is_rest: bool
    is_adjusted_workday: bool
    combo: int
    shift1: float
    shift2: float
    shift_label: str
    prod1: int
    prod2: int
    prod_label: str
    work_hours: float
    daily_output: int
    daily_delivery: int
    closing_inventory: int
    inventory_violation: bool


class SchedulingResult(BaseModel):
    success: bool
    message: str
    daily_results: List[DailyResult]
    total_production_days: int
    overtime_days: int
    overtime_shifts: int = 0
    holiday_production_days: int
    min_inventory: int
    final_inventory: int = 0
    delivery_fulfilled: bool
    solver_status: str = ""
    solve_time: float = 0.0
