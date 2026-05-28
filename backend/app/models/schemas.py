from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class ProductParams(BaseModel):
    initial_inventory: float = Field(..., gt=0, description="初期库存")
    safety_stock: float = Field(..., gt=0, description="安全库存")
    rated_output: float = Field(..., gt=0, description="单班基础额定产量")
    total_delivery: float = Field(..., gt=0, description="周期计划总交货量")
    daily_deliveries: Optional[List[dict]] = Field(default=None, description="每日交货量明细")

    @field_validator("safety_stock")
    @classmethod
    def validate_safety_stock(cls, v, info):
        if info.data.get("initial_inventory") and v > info.data["initial_inventory"]:
            raise ValueError("安全库存不能大于初期库存")
        return v


class SchedulingParams(BaseModel):
    product_1: ProductParams = Field(..., description="物品1参数")
    product_2: ProductParams = Field(..., description="物品2参数")
    start_date: date = Field(..., description="排产开始日期")
    end_date: date = Field(..., description="排产结束日期")
    holidays: List[str] = Field(default_factory=list, description="节假日列表(YYYY-MM-DD)")

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v, info):
        if info.data.get("start_date") and v <= info.data["start_date"]:
            raise ValueError("结束日期必须晚于开始日期")
        return v


class AlgorithmConfig(BaseModel):
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
    combo_1: int
    shift1_1: float
    shift2_1: float
    shift_label_1: str
    prod1_1: int
    prod2_1: int
    prod_label_1: str
    work_hours_1: float
    daily_output_1: int
    daily_delivery_1: int
    closing_inventory_1: int
    inventory_violation_1: bool
    combo_2: int
    shift1_2: float
    shift2_2: float
    shift_label_2: str
    prod1_2: int
    prod2_2: int
    prod_label_2: str
    work_hours_2: float
    daily_output_2: int
    daily_delivery_2: int
    closing_inventory_2: int
    inventory_violation_2: bool
    total_work_hours: float


class SchedulingResult(BaseModel):
    success: bool
    message: str
    daily_results: List[DailyResult]
    total_production_days: int
    rest_days_occupied: int
    total_production_days_1: int
    min_inventory_1: int
    final_inventory_1: int
    delivery_fulfilled_1: bool
    holiday_production_days_1: int
    total_production_days_2: int
    min_inventory_2: int
    final_inventory_2: int
    delivery_fulfilled_2: bool
    holiday_production_days_2: int
    solver_status: str = ""
    solve_time: float = 0.0
