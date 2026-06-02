from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date


class ProductParams(BaseModel):
    initial_inventory: float = Field(..., ge=0, description="初期库存")
    safety_stock: float = Field(..., ge=0, description="安全库存")
    rated_output: float = Field(..., gt=0, description="单班基础额定产量")
    total_delivery: float = Field(..., ge=0, description="周期计划总交货量")
    daily_deliveries: Optional[List[dict]] = Field(default=None, description="每日交货量明细")


class SchedulingParams(BaseModel):
    products: List[ProductParams] = Field(..., min_length=1, description="物品参数列表(至少1个)")
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
    max_time_seconds: int = Field(default=30, ge=10, le=60, description="求解限时(秒)")


class SchedulingRequest(BaseModel):
    params: SchedulingParams
    config: AlgorithmConfig = AlgorithmConfig()
