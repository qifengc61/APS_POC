import json, traceback
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from datetime import date, timedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from ..models.schemas import SchedulingRequest, SchedulingResult, ProductParams, SchedulingParams, AlgorithmConfig
from ..services import SchedulingService
from ..algorithm import TwoProductScheduler
from ..database import get_db
from ..models.db_models import DeliveryPlan

router = APIRouter(prefix="/api", tags=["scheduling"])


def _parse_holidays(holiday_strs: list) -> list:
    holidays = []
    for h in holiday_strs:
        if isinstance(h, str):
            holidays.append(date.fromisoformat(h))
        elif isinstance(h, date):
            holidays.append(h)
    return holidays


def _format_error(e: Exception) -> str:
    msg = str(e)
    if not msg or len(msg) < 5:
        msg = f"{type(e).__name__}: {repr(e)}"
    return msg


@router.post("/schedule", response_model=SchedulingResult)
async def calculate_schedule(request: SchedulingRequest):
    try:
        params = request.params
        config = request.config
        holidays = _parse_holidays(params.holidays)
        result = SchedulingService.calculate(params, config, holidays)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_format_error(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"排产计算异常: {_format_error(e)}")


class ScheduleByPlanRequest(BaseModel):
    delivery_plan_id: int
    config: AlgorithmConfig = AlgorithmConfig()


@router.post("/schedule/by-plan", response_model=SchedulingResult)
async def calculate_schedule_by_plan(request: ScheduleByPlanRequest, db: Session = Depends(get_db)):
    try:
        plan = db.query(DeliveryPlan).filter(DeliveryPlan.id == request.delivery_plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="交货计划不存在")

        lpa = plan.line_product_1
        lpb = plan.line_product_2

        def _parse_dd(dd_str, start_date, end_date):
            if not dd_str:
                return None
            try:
                vals = json.loads(dd_str)
            except (json.JSONDecodeError, TypeError):
                return None
            days = (end_date - start_date).days + 1
            if len(vals) != days:
                return None
            return [{"date": (start_date + timedelta(days=i)).isoformat(), "quantity": vals[i]} for i in range(days)]

        product_1 = ProductParams(
            initial_inventory=plan.initial_inventory_1,
            safety_stock=lpa.safety_stock,
            rated_output=lpa.rated_output,
            total_delivery=plan.total_delivery_1,
            daily_deliveries=_parse_dd(plan.daily_deliveries_1, plan.start_date, plan.end_date),
        )
        product_2 = ProductParams(
            initial_inventory=plan.initial_inventory_2,
            safety_stock=lpb.safety_stock,
            rated_output=lpb.rated_output,
            total_delivery=plan.total_delivery_2,
            daily_deliveries=_parse_dd(plan.daily_deliveries_2, plan.start_date, plan.end_date),
        )
        params = SchedulingParams(
            product_1=product_1,
            product_2=product_2,
            start_date=plan.start_date,
            end_date=plan.end_date,
        )
        result = SchedulingService.calculate(params, request.config, [])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=_format_error(e))
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"排产计算异常: {_format_error(e)}")


@router.post("/validate")
async def validate_params(request: SchedulingRequest):
    try:
        params = request.params
        holidays = _parse_holidays(params.holidays)
        scheduler = TwoProductScheduler(
            product_1=params.product_1,
            product_2=params.product_2,
            start_date=params.start_date,
            end_date=params.end_date,
            holidays=holidays,
        )
        work_days = sum(1 for i in range(scheduler.days) if not scheduler.rest_flags[i])
        rest_days = scheduler.days - work_days
        max_capacity_all = scheduler.days * 3.0 * (params.product_1.rated_output + params.product_2.rated_output)
        max_capacity_work = work_days * 3.0 * (params.product_1.rated_output + params.product_2.rated_output)
        total_delivery = params.product_1.total_delivery + params.product_2.total_delivery
        return {
            "valid": True,
            "message": "参数校验通过",
            "total_days": scheduler.days,
            "work_days": work_days,
            "rest_days": rest_days,
            "max_possible_output": max_capacity_all,
            "max_workday_output": max_capacity_work,
            "delivery_ratio": round(total_delivery / max_capacity_all * 100, 2) if max_capacity_all > 0 else 0,
        }
    except ValueError as e:
        return {"valid": False, "message": _format_error(e)}


class ExportResultItem(BaseModel):
    code: str = ""
    name: str = ""
    initial_inventory: float = 0
    safety_stock: float = 0
    rated_output: float = 0
    total_delivery: float = 0


class ExportRequest(BaseModel):
    result: dict
    plan_info: Optional[dict] = None


@router.post("/schedule/export")
async def export_schedule(request: ExportRequest):
    try:
        buffer = SchedulingService.export_excel(request.result, request.plan_info)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=schedule_result.xlsx"},
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {_format_error(e)}")
