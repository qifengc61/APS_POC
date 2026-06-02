import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date
from ..database import get_db
from ..models.db_models import DeliveryPlan, ProductionLine, LineProduct, PlanMaterial, PlanLine, Product

router = APIRouter(prefix="/api/delivery-plans", tags=["delivery_plans"])

MAX_DAILY_SHIFTS = 3.0


class PlanMaterialItem(BaseModel):
    product_id: int
    initial_inventory: float = Field(default=0, ge=0)
    total_delivery: float = Field(default=0, ge=0)
    daily_deliveries: str = Field(default="", description="空格分隔的每日交货量")


class DeliveryPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    materials: List[PlanMaterialItem] = Field(..., min_length=1)
    start_date: date
    end_date: date


class PlanMaterialOut(BaseModel):
    line_product_id: int
    product_name: str
    product_code: str = ""
    initial_inventory: float
    safety_stock: float
    rated_output: float
    total_delivery: float
    daily_deliveries: str = ""

    class Config:
        from_attributes = True


class PlanLineOut(BaseModel):
    line_id: int
    line_name: str
    materials: List[PlanMaterialOut]

    class Config:
        from_attributes = True


class DeliveryPlanOut(BaseModel):
    id: int
    name: str
    lines: List[PlanLineOut]
    start_date: date
    end_date: date

    class Config:
        from_attributes = True


def _build_plan_out(plan: DeliveryPlan) -> DeliveryPlanOut:
    line_outs = []
    for pl in plan.lines:
        material_outs = []
        for pm in pl.materials:
            lp = pm.line_product
            dd = pm.daily_deliveries or ""
            material_outs.append(PlanMaterialOut(
                line_product_id=pm.line_product_id,
                product_name=lp.product.name,
                product_code=lp.product.code or "",
                initial_inventory=pm.initial_inventory,
                safety_stock=lp.safety_stock,
                rated_output=lp.rated_output,
                total_delivery=pm.total_delivery,
                daily_deliveries=dd,
            ))
        line_outs.append(PlanLineOut(
            line_id=pl.line_id,
            line_name=pl.line.name,
            materials=material_outs,
        ))
    return DeliveryPlanOut(
        id=plan.id,
        name=plan.name,
        lines=line_outs,
        start_date=plan.start_date,
        end_date=plan.end_date,
    )


def _parse_daily_deliveries(daily_str: str) -> str:
    if not daily_str or not daily_str.strip():
        return ""
    parts = daily_str.strip().split()
    nums = []
    for p in parts:
        try:
            nums.append(int(p))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"每日交货量格式错误: '{p}' 不是有效数字")
    return json.dumps(nums, ensure_ascii=False)


def _parse_daily_list(daily_str: str) -> List[int]:
    if not daily_str or not daily_str.strip():
        return []
    try:
        return json.loads(daily_str)
    except (json.JSONDecodeError, TypeError):
        return []


def _split_daily_deliveries(daily_list: List[int], first_total: int, second_total: int) -> List[List[int]]:
    n_days = len(daily_list)
    results = [[], []]
    for daily in daily_list:
        if first_total + second_total > 0:
            part = int(daily * first_total / (first_total + second_total))
        else:
            part = 0
        results[0].append(part)
        results[1].append(daily - part)
    return results


def _compute_line_required_shifts(line: ProductionLine, material_assignments: List[dict]) -> float:
    total = 0.0
    for ma in material_assignments:
        lp = ma["line_product"]
        total_delivery = ma["total_delivery"]
        init = ma["initial_inventory"]
        saf = ma["safety_stock"]
        rated = lp.rated_output
        net_demand = max(0, total_delivery - init + saf)
        if rated > 0:
            total += net_demand / rated
    return total


def _compute_line_delivery_shifts(line: ProductionLine, material_assignments: List[dict]) -> float:
    total = 0.0
    for ma in material_assignments:
        lp = ma["line_product"]
        rated = lp.rated_output
        if rated > 0:
            total += ma["total_delivery"] / rated
    return total


def _check_line_capacity(line: ProductionLine, material_assignments: List[dict], days: int) -> bool:
    for ma in material_assignments:
        lp = ma["line_product"]
        total_delivery = ma["total_delivery"]
        init = ma["initial_inventory"]
        saf = ma["safety_stock"]
        rated = lp.rated_output
        max_possible = days * MAX_DAILY_SHIFTS * rated
        net_demand = total_delivery - init + saf
        if net_demand > 0 and max_possible < net_demand:
            return False

    total_required = _compute_line_required_shifts(line, material_assignments)
    total_delivery_shifts = _compute_line_delivery_shifts(line, material_assignments)
    total_available = days * MAX_DAILY_SHIFTS
    if max(total_required, total_delivery_shifts) > total_available:
        return False

    daily_lists = []
    for ma in material_assignments:
        daily_list = _parse_daily_list(_parse_daily_deliveries(ma["daily_deliveries_str"]))
        if not daily_list:
            total_del = ma["total_delivery"]
            base = int(total_del) // days if days > 0 else 0
            extra = int(total_del) % days if days > 0 else 0
            daily_list = [base + (1 if i < extra else 0) for i in range(days)]
        daily_lists.append(daily_list)

    for k in range(days):
        cum_shift_needed = 0.0
        active_products = 0
        for ma_idx, ma in enumerate(material_assignments):
            lp = ma["line_product"]
            rated = lp.rated_output
            init = ma["initial_inventory"]
            saf = ma["safety_stock"]
            cum_del = sum(daily_lists[ma_idx][:k + 1])
            cum_need = cum_del - init + saf
            if cum_need > 0 and rated > 0:
                cum_shift_needed += cum_need / rated
                if daily_lists[ma_idx][k] > 0 or cum_need > 0:
                    active_products += 1
        min_discrete_shifts = float(active_products)
        cum_shift_available = (k + 1) * MAX_DAILY_SHIFTS
        if max(cum_shift_needed, min_discrete_shifts) > cum_shift_available:
            return False

    return True


def auto_assign_materials_to_lines(
    materials_input: List[PlanMaterialItem],
    all_lines: List[ProductionLine],
    days: int,
    db: Session,
) -> List[Dict]:
    product_ids = [m.product_id for m in materials_input]
    selected_product_ids = set(product_ids)

    line_capabilities: Dict[int, Dict] = {}
    for line in all_lines:
        lp_map = {}
        for lp in line.products:
            lp_map[lp.product_id] = lp
        line_capabilities[line.id] = {
            "line": line,
            "lp_map": lp_map,
            "product_ids": set(lp_map.keys()),
        }

    matching_lines = []
    for line in all_lines:
        cap = line_capabilities[line.id]
        if selected_product_ids.issubset(cap["product_ids"]):
            matching_lines.append(line)

    if matching_lines:
        matching_lines.sort(key=lambda l: len(l.products))
        for line in matching_lines:
            cap = line_capabilities[line.id]
            assignments = []
            for m in materials_input:
                lp = cap["lp_map"][m.product_id]
                total_del = m.total_delivery
                if total_del <= 0 and m.daily_deliveries and m.daily_deliveries.strip():
                    total_del = sum(int(p) for p in m.daily_deliveries.strip().split())
                assignments.append({
                    "product_id": m.product_id,
                    "line_product": lp,
                    "initial_inventory": m.initial_inventory,
                    "total_delivery": total_del,
                    "daily_deliveries_str": m.daily_deliveries,
                    "safety_stock": lp.safety_stock,
                })
            any_max_possible_fail = False
            for ma in assignments:
                lp = ma["line_product"]
                max_possible = days * MAX_DAILY_SHIFTS * lp.rated_output
                net_demand = ma["total_delivery"] - ma["initial_inventory"] + ma["safety_stock"]
                if net_demand > 0 and max_possible < net_demand:
                    any_max_possible_fail = True
                    break
            if any_max_possible_fail:
                continue
            if _check_line_capacity(line, assignments, days):
                return [{"line": line, "materials": assignments}]

    uncovered = set(selected_product_ids)
    selected_lines = []
    available_lines = list(all_lines)

    while uncovered:
        best_line = None
        best_coverage = 0
        best_capacity_score = 0
        for line in available_lines:
            if line in selected_lines:
                continue
            cap = line_capabilities[line.id]
            covered = uncovered & cap["product_ids"]
            coverage = len(covered)
            capacity_score = sum(cap["lp_map"][pid].rated_output for pid in covered if pid in cap["lp_map"])
            if coverage > best_coverage or (coverage == best_coverage and capacity_score > best_capacity_score):
                best_line = line
                best_coverage = coverage
                best_capacity_score = capacity_score
        if best_line is None or best_coverage == 0:
            missing_products = db.query(Product).filter(Product.id.in_(uncovered)).all()
            missing_names = ", ".join(p.name for p in missing_products)
            raise HTTPException(
                status_code=400,
                detail=f"以下物料不在任何产线的可生产列表中，无法创建交货计划：{missing_names}"
            )
        selected_lines.append(best_line)
        uncovered -= line_capabilities[best_line.id]["product_ids"]

    assignment: Dict[int, List[dict]] = {line.id: [] for line in selected_lines}
    line_load: Dict[int, float] = {line.id: 0.0 for line in selected_lines}

    for m in materials_input:
        total_del = m.total_delivery
        if total_del <= 0 and m.daily_deliveries and m.daily_deliveries.strip():
            total_del = sum(int(p) for p in m.daily_deliveries.strip().split())

        candidates = []
        total_available = days * MAX_DAILY_SHIFTS
        for line in selected_lines:
            cap = line_capabilities[line.id]
            if m.product_id in cap["product_ids"]:
                lp = cap["lp_map"][m.product_id]
                remaining = total_available - line_load[line.id]
                candidates.append((line, lp, remaining))

        candidates.sort(key=lambda x: (x[2], -x[1].rated_output))
        best_line, best_lp, _ = candidates[0]

        ma = {
            "product_id": m.product_id,
            "line_product": best_lp,
            "initial_inventory": m.initial_inventory,
            "total_delivery": total_del,
            "daily_deliveries_str": m.daily_deliveries,
            "safety_stock": best_lp.safety_stock,
        }
        assignment[best_line.id].append(ma)
        net_demand = max(0, total_del - m.initial_inventory + best_lp.safety_stock)
        if best_lp.rated_output > 0:
            line_load[best_line.id] += net_demand / best_lp.rated_output

    overloaded_lines = []
    for line in selected_lines:
        mat_list = assignment[line.id]
        total_required = _compute_line_required_shifts(line, mat_list)
        total_available = days * MAX_DAILY_SHIFTS
        if total_required > total_available:
            overloaded_lines.append(line)

    if overloaded_lines:
        assignment = _resolve_overload(
            assignment, overloaded_lines, line_capabilities,
            days, materials_input, db
        )

    result = []
    seen_line_ids = set()
    for line in selected_lines:
        mats = assignment.get(line.id, [])
        if mats and line.id not in seen_line_ids:
            result.append({"line": line, "materials": mats})
            seen_line_ids.add(line.id)

    for line_id, mats in assignment.items():
        if mats and line_id not in seen_line_ids:
            actual_line = line_capabilities[line_id]["line"]
            if actual_line:
                result.append({"line": actual_line, "materials": mats})
                seen_line_ids.add(line_id)

    return result


def _resolve_overload(
    assignment: Dict[int, List[dict]],
    overloaded_lines: List[ProductionLine],
    line_capabilities: Dict[int, Dict],
    days: int,
    materials_input: List[PlanMaterialItem],
    db: Session,
) -> Dict[int, List[dict]]:
    for line in overloaded_lines:
        max_iterations = 10
        for iteration in range(max_iterations):
            mat_list = assignment.get(line.id, [])
            total_required = _compute_line_required_shifts(line, mat_list)
            total_delivery_shifts = _compute_line_delivery_shifts(line, mat_list)
            total_available = days * MAX_DAILY_SHIFTS
            excess_shifts = max(total_required, total_delivery_shifts) - total_available
            if excess_shifts <= 0:
                break

            movable_materials = []
            for ma in mat_list:
                lp = ma["line_product"]
                product_id = ma["product_id"]
                alternative_lines = []
                for other_line_id, cap in line_capabilities.items():
                    other_line = cap["line"]
                    if other_line.id == line.id:
                        continue
                    if product_id in cap["product_ids"]:
                        other_mats = assignment.get(other_line.id, [])
                        other_total = _compute_line_required_shifts(other_line, other_mats)
                        other_available = days * MAX_DAILY_SHIFTS
                        remaining = other_available - other_total
                        if remaining > 0:
                            alternative_lines.append((other_line, remaining, cap["lp_map"][product_id]))

                if not alternative_lines:
                    continue
                alternative_lines.sort(key=lambda x: -x[1])
                net_demand = max(0, ma["total_delivery"] - ma["initial_inventory"] + ma["safety_stock"])
                shifts_needed = net_demand / lp.rated_output if lp.rated_output > 0 else 0
                movable_materials.append({
                    "ma": ma,
                    "shifts": shifts_needed,
                    "alternatives": alternative_lines,
                })

            movable_materials.sort(key=lambda x: -x["shifts"])

            for mv in movable_materials:
                if excess_shifts <= 0:
                    break
                ma = mv["ma"]
                for alt_line, available_capacity, alt_lp in mv["alternatives"]:
                    if available_capacity <= 0:
                        continue

                    lp = ma["line_product"]
                    net_demand = max(0, ma["total_delivery"] - ma["initial_inventory"] + ma["safety_stock"])
                    total_shifts = net_demand / lp.rated_output if lp.rated_output > 0 else 0
                    if total_shifts <= 0:
                        continue

                    alt_max_shifts = (days * MAX_DAILY_SHIFTS * alt_lp.rated_output) / lp.rated_output if lp.rated_output > 0 else 0
                    movable_ratio = min(
                        excess_shifts / total_shifts,
                        available_capacity / total_shifts,
                        alt_max_shifts / total_shifts if total_shifts > 0 else 0,
                        1.0,
                    )
                    if movable_ratio <= 0:
                        continue

                    original_delivery = int(ma["total_delivery"])
                    split_delivery = int(original_delivery * movable_ratio)
                    if split_delivery <= 0:
                        continue
                    remaining_delivery = original_delivery - split_delivery

                    daily_list = _parse_daily_list(_parse_daily_deliveries(ma["daily_deliveries_str"]))
                    if 0 < remaining_delivery < (len(daily_list) if daily_list else 1):
                        split_delivery = original_delivery
                        remaining_delivery = 0

                    orig_init = ma["initial_inventory"]
                    orig_safety = ma["safety_stock"]
                    ratio = split_delivery / original_delivery if original_delivery > 0 else 0.0

                    if daily_list:
                        if remaining_delivery <= 0:
                            daily_a = ""
                            daily_b = ma["daily_deliveries_str"]
                        else:
                            split_daily = _split_daily_deliveries(daily_list, remaining_delivery, split_delivery)
                            daily_a = " ".join(str(x) for x in split_daily[0])
                            daily_b = " ".join(str(x) for x in split_daily[1])
                    else:
                        daily_a = ""
                        daily_b = ""

                    if remaining_delivery <= 0:
                        assignment[line.id] = [m for m in assignment[line.id] if m is not ma]
                    else:
                        ma["total_delivery"] = float(remaining_delivery)
                        ma["initial_inventory"] = orig_init * (1.0 - ratio)
                        ma["safety_stock"] = orig_safety * (1.0 - ratio)
                        ma["daily_deliveries_str"] = daily_a

                    if alt_line.id not in assignment:
                        assignment[alt_line.id] = []
                    assignment[alt_line.id].append({
                        "product_id": ma["product_id"],
                        "line_product": alt_lp,
                        "initial_inventory": orig_init * ratio,
                        "total_delivery": float(split_delivery),
                        "daily_deliveries_str": daily_b,
                        "safety_stock": orig_safety * ratio,
                    })

                    excess_shift_reduction = movable_ratio * total_shifts
                    excess_shifts -= excess_shift_reduction
                    break

    return assignment


@router.get("", response_model=List[DeliveryPlanOut])
def list_plans(db: Session = Depends(get_db)):
    plans = db.query(DeliveryPlan).order_by(DeliveryPlan.id.desc()).all()
    return [_build_plan_out(p) for p in plans]


@router.get("/{plan_id}", response_model=DeliveryPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(DeliveryPlan).filter(DeliveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="交货计划不存在")
    return _build_plan_out(plan)


@router.post("", response_model=DeliveryPlanOut)
def create_plan(data: DeliveryPlanCreate, db: Session = Depends(get_db)):
    if data.end_date <= data.start_date:
        raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")

    product_ids = [m.product_id for m in data.materials]
    if len(set(product_ids)) != len(product_ids):
        raise HTTPException(status_code=400, detail="物料不能重复")

    for m in data.materials:
        product = db.query(Product).filter(Product.id == m.product_id).first()
        if not product:
            raise HTTPException(status_code=400, detail=f"物料ID {m.product_id} 不存在")

    days = (data.end_date - data.start_date).days + 1

    for m in data.materials:
        if m.daily_deliveries and m.daily_deliveries.strip():
            parts = m.daily_deliveries.strip().split()
            if len(parts) != days:
                product = db.query(Product).filter(Product.id == m.product_id).first()
                raise HTTPException(status_code=400, detail=f"物料 '{product.name}' 的每日交货量数量({len(parts)})与排产天数({days})不匹配")

    all_lines = db.query(ProductionLine).all()
    if not all_lines:
        raise HTTPException(status_code=400, detail="系统中暂无产线，请先创建产线")

    line_assignments = auto_assign_materials_to_lines(data.materials, all_lines, days, db)

    for la in line_assignments:
        line = la["line"]
        for ma in la["materials"]:
            lp = ma["line_product"]
            rated = lp.rated_output
            saf = ma["safety_stock"]
            init = ma["initial_inventory"]
            total_del = ma["total_delivery"]

            max_possible = days * MAX_DAILY_SHIFTS * rated
            net_demand = total_del - init + saf

            if net_demand > 0 and max_possible < net_demand:
                product = db.query(Product).filter(Product.id == ma["product_id"]).first()
                raise HTTPException(
                    status_code=400,
                    detail=f"产线 '{line.name}' 产能不足以满足物料 '{product.name}' 的交货需求。"
                           f"排产周期 {days} 天，最大产能 {max_possible:.0f}，净需求 {net_demand:.0f}"
                )

    for la in line_assignments:
        line = la["line"]
        if not _check_line_capacity(line, la["materials"], days):
            raise HTTPException(
                status_code=400,
                detail=f"产线 '{line.name}' 的交货需求在排产约束下不可行（前缀累积校验失败），"
                       f"请调整交货分布、增加初期库存或延长排产周期"
            )

    plan = DeliveryPlan(
        name=data.name,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(plan)
    db.flush()

    for line_idx, la in enumerate(line_assignments):
        line = la["line"]
        plan_line = PlanLine(
            plan_id=plan.id,
            line_id=line.id,
            sort_order=line_idx,
        )
        db.add(plan_line)
        db.flush()

        for mat_idx, ma in enumerate(la["materials"]):
            dd_json = _parse_daily_deliveries(ma["daily_deliveries_str"])
            total = ma["total_delivery"]
            if dd_json:
                vals = json.loads(dd_json)
                total = sum(vals)
            pm = PlanMaterial(
                plan_line_id=plan_line.id,
                line_product_id=ma["line_product"].id,
                initial_inventory=ma["initial_inventory"],
                safety_stock=ma["safety_stock"],
                total_delivery=total,
                daily_deliveries=dd_json or None,
                sort_order=mat_idx,
            )
            db.add(pm)

    db.commit()
    db.refresh(plan)
    return _build_plan_out(plan)


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(DeliveryPlan).filter(DeliveryPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="交货计划不存在")
    db.delete(plan)
    db.commit()
    return {"ok": True}
