from fastapi import APIRouter

from .scheduling import router as scheduling_router
from .material import router as material_router
from .manufacture_bom import router as manufacture_bom_router
from .process import router as process_router
from .process_route import router as process_route_router
from .production_resource import router as production_resource_router
from .work_calendar import router as work_calendar_router
from .incoming_material_order import router as incoming_material_order_router
from .production_order import router as production_order_router
from .planning_strategy import router as planning_strategy_router
from .smart_scheduling import router as smart_scheduling_router

router = APIRouter()

router.include_router(scheduling_router)
router.include_router(material_router)
router.include_router(manufacture_bom_router)
router.include_router(process_router)
router.include_router(process_route_router)
router.include_router(production_resource_router)
router.include_router(work_calendar_router)
router.include_router(incoming_material_order_router)
router.include_router(production_order_router)
router.include_router(planning_strategy_router)
router.include_router(smart_scheduling_router)

__all__ = ["router"]
