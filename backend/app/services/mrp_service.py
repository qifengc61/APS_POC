from typing import List, Dict, Set, Tuple
import logging
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.manufacture_bom import ManufactureBOM
from app.models.incoming_material_order import IncomingMaterialOrder
from app.models.production_order import ProductionOrder
from app.schemas.mrp import MRPResult, ShortageDAG, ShortageNode, ShortageEdge

logger = logging.getLogger("aps.mrp")


class MRPService:

    @staticmethod
    def run(db: Session, order_ids: List[str]) -> MRPResult:
        orders = db.query(ProductionOrder).filter(
            ProductionOrder.id.in_(order_ids)
        ).all()

        valid_orders = [
            o for o in orders
            if o.can_schedule and o.order_status != "CANCELLED"
        ]

        shortage_node_map: Dict[str, dict] = {}
        edge_set: Set[Tuple[str, str]] = set()
        shortage_edges: List[ShortageEdge] = []
        total_materials_checked = 0
        order_shortage_map: Dict[str, Dict[str, float]] = {}
        order_own_material_ids: Dict[str, str] = {}

        for order in valid_orders:
            logger.info("处理订单: code=%s material_code=%s quantity=%.0f",
                        order.code, order.material_code, order.quantity)

            material = db.query(Material).filter(
                Material.code == order.material_code
            ).first()
            if not material:
                logger.warning("订单 %s 的 material_code=%s 在物料表中找不到匹配记录",
                               order.code, order.material_code)
                continue

            logger.info("  匹配物料: id=%s code=%s name=%s source=%s",
                        material.id, material.code, material.name, material.source)

            order_own_material_ids[order.code] = material.id

            bom = db.query(ManufactureBOM).filter(
                ManufactureBOM.material_id == material.id
            ).first()
            if not bom:
                logger.warning("物料 %s(%s) 无BOM，跳过", material.code, material.id)
                continue
            if not bom.child_materials:
                logger.warning("物料 %s(%s) BOM的子件列表为空，跳过", material.code, material.id)
                continue

            logger.info("  BOM子件数=%d, 可用库存=%.0f",
                        len(bom.child_materials), float(material.quantity or 0))

            order_shortage_map[order.code] = {}

            if material.id not in shortage_node_map:
                shortage_node_map[material.id] = {
                    "material_code": material.code,
                    "material_name": material.name,
                    "material_source": material.source,
                    "gross_demand": float(order.quantity),
                    "available_inventory": float(material.quantity or 0),
                    "in_transit_quantity": 0.0,
                    "net_demand": float(order.quantity),
                    "order_demands": {order.id: float(order.quantity)},
                }
                logger.info("  订单物料 %s 加入DAG, 需求量=%.0f",
                            material.code, float(order.quantity))
            else:
                shortage_node_map[material.id]["gross_demand"] += float(order.quantity)
                shortage_node_map[material.id]["net_demand"] += float(order.quantity)
                shortage_node_map[material.id]["order_demands"][order.id] = float(order.quantity)

            if order.code in order_shortage_map:
                order_shortage_map[order.code][material.id] = shortage_node_map[material.id]["net_demand"]

            for child in bom.child_materials:
                child_material_id = child.get("material_id")
                child_quantity = float(child.get("quantity", 0))
                gross_demand = child_quantity * float(order.quantity)

                total_materials_checked = MRPService._expand_bom(
                    db=db,
                    material_id=child_material_id,
                    demand_quantity=gross_demand,
                    shortage_node_map=shortage_node_map,
                    edge_set=edge_set,
                    shortage_edges=shortage_edges,
                    parent_material_id=material.id,
                    visited=set(),
                    order_code=order.code,
                    order_id=order.id,
                    order_shortage_map=order_shortage_map,
                    total_materials_checked=total_materials_checked,
                )

        shortage_nodes = []
        for mid, data in shortage_node_map.items():
            shortage_nodes.append(ShortageNode(
                material_id=mid,
                material_code=data["material_code"],
                material_name=data["material_name"],
                material_source=data["material_source"],
                gross_demand=data["gross_demand"],
                available_inventory=data["available_inventory"],
                in_transit_quantity=data["in_transit_quantity"],
                net_demand=data["net_demand"],
                order_demands=data.get("order_demands", {}),
            ))

        supplement_orders = []
        for order_code, material_demands in order_shortage_map.items():
            own_mid = order_own_material_ids.get(order_code)
            for mid, net_demand in material_demands.items():
                if mid == own_mid:
                    continue
                data = shortage_node_map[mid]
                if data["material_source"] == "PRODUCED":
                    supplement_orders.append({
                        "code": f"SUP-{order_code}-{data['material_code']}",
                        "material_code": data["material_code"],
                        "quantity": net_demand,
                        "supplement": True,
                        "parent_order_code": order_code,
                    })

        shortage_dag = ShortageDAG(
            nodes=shortage_nodes,
            edges=shortage_edges,
        )

        return MRPResult(
            shortage_dag=shortage_dag,
            supplement_orders=supplement_orders,
            total_materials_checked=total_materials_checked,
            total_shortages=len(shortage_node_map),
        )

    @staticmethod
    def _expand_bom(
        db: Session,
        material_id: str,
        demand_quantity: float,
        shortage_node_map: Dict[str, dict],
        edge_set: Set[Tuple[str, str]],
        shortage_edges: List[ShortageEdge],
        parent_material_id: str,
        visited: Set[str],
        order_code: str,
        order_id: str,
        order_shortage_map: Dict[str, Dict[str, float]],
        total_materials_checked: int,
    ) -> int:
        if material_id in visited:
            return total_materials_checked

        material = db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return total_materials_checked

        total_materials_checked += 1

        available_inventory = float(material.quantity or 0)
        safety_stock = float(material.safety_stock or 0)

        in_transit_orders = db.query(IncomingMaterialOrder).filter(
            IncomingMaterialOrder.material_id == material_id,
            IncomingMaterialOrder.status == "PENDING",
        ).order_by(IncomingMaterialOrder.expected_arrival_time).all()

        in_transit_quantity = sum(float(o.quantity or 0) for o in in_transit_orders)

        remaining = demand_quantity + safety_stock - available_inventory
        if remaining > 0:
            for ito in in_transit_orders:
                remaining -= float(ito.quantity or 0)
                if remaining <= 0:
                    break

        net_demand = max(0.0, remaining)

        if net_demand > 0:
            edge_key = (parent_material_id, material_id)
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                shortage_edges.append(ShortageEdge(
                    source_material_id=parent_material_id,
                    target_material_id=material_id,
                ))

            if material_id in shortage_node_map:
                old_net = shortage_node_map[material_id]["net_demand"]
                shortage_node_map[material_id]["gross_demand"] += demand_quantity
                total_gross = shortage_node_map[material_id]["gross_demand"]
                new_net = max(
                    0.0, total_gross + safety_stock - available_inventory - in_transit_quantity
                )
                shortage_node_map[material_id]["net_demand"] = new_net
                delta = new_net - old_net
                od = shortage_node_map[material_id].get("order_demands", {})
                od[order_id] = od.get(order_id, 0.0) + delta
                shortage_node_map[material_id]["order_demands"] = od
            else:
                shortage_node_map[material_id] = {
                    "material_code": material.code,
                    "material_name": material.name,
                    "material_source": material.source,
                    "gross_demand": demand_quantity,
                    "available_inventory": available_inventory,
                    "in_transit_quantity": in_transit_quantity,
                    "net_demand": net_demand,
                    "order_demands": {order_id: net_demand},
                }

            if order_code in order_shortage_map:
                if material_id in order_shortage_map[order_code]:
                    order_shortage_map[order_code][material_id] += net_demand
                else:
                    order_shortage_map[order_code][material_id] = net_demand

            if material.source == "PRODUCED":
                bom = db.query(ManufactureBOM).filter(
                    ManufactureBOM.material_id == material_id
                ).first()
                if bom and bom.child_materials:
                    visited_copy = visited | {material_id}
                    for child in bom.child_materials:
                        child_material_id = child.get("material_id")
                        child_quantity = float(child.get("quantity", 0))
                        child_gross_demand = child_quantity * net_demand

                        total_materials_checked = MRPService._expand_bom(
                            db=db,
                            material_id=child_material_id,
                            demand_quantity=child_gross_demand,
                            shortage_node_map=shortage_node_map,
                            edge_set=edge_set,
                            shortage_edges=shortage_edges,
                            parent_material_id=material_id,
                            visited=visited_copy,
                            order_code=order_code,
                            order_id=order_id,
                            order_shortage_map=order_shortage_map,
                            total_materials_checked=total_materials_checked,
                        )

        return total_materials_checked
