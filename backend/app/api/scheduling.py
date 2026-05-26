from fastapi import APIRouter, HTTPException
from datetime import date
from ..models.schemas import SchedulingRequest, SchedulingResult
from ..services import SchedulingService
import traceback

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


@router.post("/validate")
async def validate_params(request: SchedulingRequest):
    try:
        from ..algorithm import ORToolsScheduler

        params = request.params
        holidays = _parse_holidays(params.holidays)
        scheduler = ORToolsScheduler(
            initial_inventory=params.initial_inventory,
            safety_stock=params.safety_stock,
            rated_output=params.rated_output,
            total_delivery=params.total_delivery,
            start_date=params.start_date,
            end_date=params.end_date,
            holidays=holidays,
            daily_deliveries=params.daily_deliveries,
        )
        work_days = sum(1 for i in range(scheduler.days) if not scheduler.rest_flags[i])
        rest_days = scheduler.days - work_days
        max_capacity_all = scheduler.days * 3.0 * params.rated_output
        max_capacity_work = work_days * 3.0 * params.rated_output
        return {
            "valid": True,
            "message": "参数校验通过",
            "total_days": scheduler.days,
            "work_days": work_days,
            "rest_days": rest_days,
            "max_possible_output": max_capacity_all,
            "max_workday_output": max_capacity_work,
            "delivery_ratio": round(params.total_delivery / max_capacity_all * 100, 2) if max_capacity_all > 0 else 0,
        }
    except ValueError as e:
        return {"valid": False, "message": _format_error(e)}
