import uuid
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, deque

from sqlalchemy.orm import Session

from app.models.plan_task import PlanTaskPending
from app.models.plan_task_order import PlanTaskOrderPending
from app.models.process_route import ProcessRoute
from app.models.process import Process
from app.models.production_order import ProductionOrder
from app.models.material import Material
from app.utils.graph import Graph, topological_sort, build_graph_from_route_design
from app.schemas.mrp import MRPResult

logger = logging.getLogger("aps.task_gen")


class TaskGenerationService:

    @staticmethod
    def generate(db: Session, mrp_result: MRPResult, strategy_id: Optional[str] = None) -> List[dict]:
        shortage_dag = mrp_result.shortage_dag
        if not shortage_dag or not shortage_dag.nodes:
            logger.warning("缺料DAG为空或无节点，跳过任务生成")
            return []

        logger.info("缺料DAG: %d个节点, %d条边", len(shortage_dag.nodes), len(shortage_dag.edges))
        for node in shortage_dag.nodes:
            logger.info("  DAG节点: material=%s(%s) source=%s demand=%.2f orders=%s",
                        node.material_code, node.material_id, node.material_source,
                        node.net_demand, node.order_demands)

        material_node_map: Dict[str, dict] = {}
        for node in shortage_dag.nodes:
            material_node_map[node.material_id] = {
                "material_code": node.material_code,
                "material_name": node.material_name,
                "material_source": node.material_source,
                "net_demand": node.net_demand,
                "order_demands": node.order_demands,
            }

        shortage_graph = Graph()
        for node in shortage_dag.nodes:
            shortage_graph.add_node(node.material_id, {
                "material_code": node.material_code,
                "material_name": node.material_name,
                "material_source": node.material_source,
                "net_demand": node.net_demand,
            })
        for edge in shortage_dag.edges:
            shortage_graph.add_edge(edge.target_material_id, edge.source_material_id)

        sorted_material_ids = topological_sort(shortage_graph)
        logger.info("拓扑排序后物料顺序 (%d): %s", len(sorted_material_ids), sorted_material_ids)

        supplement_order_map: Dict[str, ProductionOrder] = {}
        supplement_order_by_code_and_parent: Dict[Tuple[str, str], ProductionOrder] = {}
        for sup_order in mrp_result.supplement_orders:
            existing = db.query(ProductionOrder).filter(
                ProductionOrder.code == sup_order["code"]
            ).first()
            if existing:
                supplement_order_map[sup_order["material_code"]] = existing
                supplement_order_by_code_and_parent[(sup_order["material_code"], sup_order["parent_order_code"])] = existing
                continue
            new_order = ProductionOrder(
                code=sup_order["code"],
                material_code=sup_order["material_code"],
                quantity=sup_order["quantity"],
                supplement=True,
                parent_order_code=sup_order["parent_order_code"],
                order_status="PENDING",
                scheduling_status="UNSCHEDULED",
            )
            db.add(new_order)
            db.flush()
            supplement_order_map[sup_order["material_code"]] = new_order
            supplement_order_by_code_and_parent[(sup_order["material_code"], sup_order["parent_order_code"])] = new_order

        all_original_orders = db.query(ProductionOrder).filter(
            ProductionOrder.supplement == False
        ).all()
        original_order_by_id: Dict[str, ProductionOrder] = {o.id: o for o in all_original_orders}

        material_task_map: Dict[str, List[PlanTaskPending]] = {}
        material_start_tasks: Dict[str, List[PlanTaskPending]] = {}
        material_end_tasks: Dict[str, List[PlanTaskPending]] = {}
        all_tasks: List[PlanTaskPending] = []
        all_order_records: List[PlanTaskOrderPending] = []
        task_code_counter: Dict[str, int] = defaultdict(int)

        for material_id in sorted_material_ids:
            node_info = material_node_map.get(material_id)
            if not node_info:
                continue

            material_code = node_info["material_code"]
            net_demand = node_info["net_demand"]
            order_demands = node_info.get("order_demands", {})

            route = db.query(ProcessRoute).filter(
                ProcessRoute.material_id == material_id
            ).first()
            if not route or not route.route_design:
                logger.warning("物料 %s(%s) 无工艺路线，跳过", material_code, material_id)
                continue

            if order_demands:
                order_entries = []
                for order_id, demand_qty in order_demands.items():
                    order = original_order_by_id.get(order_id)
                    if order:
                        order_entries.append((order, demand_qty))

                if not order_entries:
                    sup_order = supplement_order_map.get(material_code)
                    if sup_order:
                        order_entries = [(sup_order, net_demand)]

                for order, demand_qty in order_entries:
                    TaskGenerationService._generate_tasks_for_order(
                        db=db,
                        order=order,
                        material_id=material_id,
                        material_code=material_code,
                        demand_qty=demand_qty,
                        route=route,
                        material_task_map=material_task_map,
                        material_start_tasks=material_start_tasks,
                        material_end_tasks=material_end_tasks,
                        all_tasks=all_tasks,
                        all_order_records=all_order_records,
                        task_code_counter=task_code_counter,
                    )
            else:
                sup_order = supplement_order_map.get(material_code)
                if sup_order:
                    TaskGenerationService._generate_tasks_for_order(
                        db=db,
                        order=sup_order,
                        material_id=material_id,
                        material_code=material_code,
                        demand_qty=net_demand,
                        route=route,
                        material_task_map=material_task_map,
                        material_start_tasks=material_start_tasks,
                        material_end_tasks=material_end_tasks,
                        all_tasks=all_tasks,
                        all_order_records=all_order_records,
                        task_code_counter=task_code_counter,
                    )
                else:
                    logger.warning("物料 %s(%s) 无对应生产订单，跳过", material_code, material_id)

        for edge in shortage_dag.edges:
            child_material_id = edge.target_material_id
            parent_material_id = edge.source_material_id

            child_ends = material_end_tasks.get(child_material_id, [])
            parent_starts = material_start_tasks.get(parent_material_id, [])

            for child_end in child_ends:
                for parent_start in parent_starts:
                    if child_end.production_order_id != parent_start.production_order_id:
                        continue
                    child_next = list(child_end.next_task_codes or [])
                    if parent_start.code not in child_next:
                        child_next.append(parent_start.code)
                    child_end.next_task_codes = child_next

                    parent_front = list(parent_start.front_task_codes or [])
                    if child_end.code not in parent_front:
                        parent_front.append(child_end.code)
                    parent_start.front_task_codes = parent_front

        db.flush()

        result = []
        for task in all_tasks:
            result.append({
                "id": task.id,
                "code": task.code,
                "production_order_id": task.production_order_id,
                "scheduled_quantity": float(task.scheduled_quantity) if task.scheduled_quantity else 0,
                "process_code": task.process_code,
                "process_info": task.process_info,
                "front_task_codes": task.front_task_codes,
                "next_task_codes": task.next_task_codes,
                "main_order_id": task.main_order_id,
                "start_task": task.start_task,
                "end_task": task.end_task,
                "input_materials": task.input_materials,
            })

        logger.info("任务生成完成: 共生成 %d 个任务, %d 个订单关联记录", len(result), len(all_order_records))
        if not result:
            logger.warning("任务生成为空! 检查: 是否有工艺路线与物料正确匹配? 生产订单是否关联了正确的物料编码?")
        return result

    @staticmethod
    def _generate_tasks_for_order(
        db: Session,
        order: ProductionOrder,
        material_id: str,
        material_code: str,
        demand_qty: float,
        route: ProcessRoute,
        material_task_map: Dict[str, List[PlanTaskPending]],
        material_start_tasks: Dict[str, List[PlanTaskPending]],
        material_end_tasks: Dict[str, List[PlanTaskPending]],
        all_tasks: List[PlanTaskPending],
        all_order_records: List[PlanTaskOrderPending],
        task_code_counter: Dict[str, int],
    ):
        order_code = order.code
        production_order_id = order.id

        route_design = route.route_design
        route_graph = build_graph_from_route_design(route_design)
        sorted_process_ids = TaskGenerationService._topological_sort_route(route_design)

        process_data_map: Dict[str, dict] = {}
        for node_data in route_design.get("nodes", []):
            process_data_map[node_data["id"]] = node_data.get("data", {})

        process_task_map: Dict[str, PlanTaskPending] = {}
        material_tasks: List[PlanTaskPending] = []

        for idx, process_node_id in enumerate(sorted_process_ids):
            process_info = dict(process_data_map.get(process_node_id, {}))
            process_code = process_info.get("code", process_node_id)

            live_process = db.query(Process).filter(
                Process.code == process_code
            ).first()
            if live_process:
                if live_process.use_main_resources is not None:
                    process_info["use_main_resources"] = live_process.use_main_resources
                if live_process.use_auxiliary_resources is not None:
                    process_info["use_auxiliary_resources"] = live_process.use_auxiliary_resources
                logger.info("  工序 %s: 从数据库刷新主资源=%s",
                            process_code,
                            [r.get("resource_id", r)[:8] if isinstance(r, dict) else r[:8]
                             for r in (process_info.get("use_main_resources") or [])])

            task_code_counter[order_code] += 1
            seq = task_code_counter[order_code]
            task_code = f"TASK-{order_code}-{process_code}-{seq}"

            predecessors = route_graph.get_predecessors(process_node_id)
            successors = route_graph.get_successors(process_node_id)

            is_start = len(predecessors) == 0
            is_end = len(successors) == 0

            input_materials = process_info.get("use_materials")

            task = PlanTaskPending(
                code=task_code,
                production_order_id=production_order_id,
                scheduled_quantity=demand_qty,
                process_code=process_code,
                process_info=process_info if process_info else None,
                front_task_codes=[],
                next_task_codes=[],
                main_order_id=production_order_id,
                start_task=is_start,
                end_task=is_end,
                input_materials=input_materials,
            )
            db.add(task)
            db.flush()

            process_task_map[process_node_id] = task
            material_tasks.append(task)

            if is_start:
                material_start_tasks.setdefault(material_id, []).append(task)
            if is_end:
                material_end_tasks.setdefault(material_id, []).append(task)

        for edge_data in route_design.get("edges", []):
            source_id = edge_data["source"]
            target_id = edge_data["target"]
            source_task = process_task_map.get(source_id)
            target_task = process_task_map.get(target_id)
            if source_task and target_task:
                source_next = list(source_task.next_task_codes or [])
                if target_task.code not in source_next:
                    source_next.append(target_task.code)
                source_task.next_task_codes = source_next

                target_front = list(target_task.front_task_codes or [])
                if source_task.code not in target_front:
                    target_front.append(source_task.code)
                target_task.front_task_codes = target_front

        if material_id not in material_task_map:
            material_task_map[material_id] = []
        material_task_map[material_id].extend(material_tasks)
        all_tasks.extend(material_tasks)

        order_record = PlanTaskOrderPending(
            production_order_id=production_order_id,
            order_code=order_code,
            material_code=material_code,
            quantity=demand_qty,
            delivery_time=order.delivery_time,
            priority=order.priority,
        )
        db.add(order_record)
        all_order_records.append(order_record)

    @staticmethod
    def _topological_sort_route(route_design: dict) -> List[str]:
        graph = build_graph_from_route_design(route_design)
        return topological_sort(graph)
