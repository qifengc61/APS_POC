from typing import Dict, List
from pydantic import BaseModel


class ShortageNode(BaseModel):
    material_id: str
    material_code: str
    material_name: str
    material_source: str
    gross_demand: float
    available_inventory: float
    in_transit_quantity: float
    net_demand: float
    order_demands: Dict[str, float] = {}


class ShortageEdge(BaseModel):
    source_material_id: str
    target_material_id: str


class ShortageDAG(BaseModel):
    nodes: List[ShortageNode]
    edges: List[ShortageEdge]

class MRPResult(BaseModel):
    shortage_dag: ShortageDAG
    supplement_orders: List[dict]
    total_materials_checked: int
    total_shortages: int
