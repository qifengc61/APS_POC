import sys
import os
import json
import traceback
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.models.db_models import (
    Product, ProductionLine, LineProduct, DeliveryPlan, PlanLine, PlanMaterial
)
from app.models.schemas import AlgorithmConfig, SchedulingParams, ProductParams
from app.services.scheduling_service import SchedulingService
from app.api.delivery_plans import (
    PlanMaterialItem, auto_assign_materials_to_lines, _parse_daily_deliveries, MAX_DAILY_SHIFTS
)


def get_or_create_product(db, name, code="", safety_stock=0):
    existing = db.query(Product).filter(Product.name == name).first()
    if existing:
        return existing
    p = Product(name=name, code=code, safety_stock=safety_stock)
    db.add(p)
    db.flush()
    return p


def get_or_create_line(db, name):
    existing = db.query(ProductionLine).filter(ProductionLine.name == name).first()
    if existing:
        return existing
    line = ProductionLine(name=name)
    db.add(line)
    db.flush()
    return line


def get_or_create_line_product(db, line_id, product_id, rated_output, safety_stock=0, initial_inventory=0):
    existing = db.query(LineProduct).filter(
        LineProduct.line_id == line_id,
        LineProduct.product_id == product_id,
    ).first()
    if existing:
        existing.rated_output = rated_output
        existing.safety_stock = safety_stock
        existing.initial_inventory = initial_inventory
        db.flush()
        return existing
    lp = LineProduct(
        line_id=line_id,
        product_id=product_id,
        rated_output=rated_output,
        safety_stock=safety_stock,
        initial_inventory=initial_inventory,
    )
    db.add(lp)
    db.flush()
    return lp


def ensure_no_plan(db, name):
    existing = db.query(DeliveryPlan).filter(DeliveryPlan.name == name).first()
    if existing:
        db.delete(existing)
        db.flush()


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


def create_delivery_plan(db, name, materials_data, start_date, end_date, config=None):
    ensure_no_plan(db, name)
    if config is None:
        config = AlgorithmConfig(max_time_seconds=30, rest_day_weight=50.0)

    days = (end_date - start_date).days + 1
    materials = []
    for md in materials_data:
        materials.append(PlanMaterialItem(
            product_id=md["product_id"],
            initial_inventory=md["initial_inventory"],
            total_delivery=md["total_delivery"],
            daily_deliveries=md.get("daily_deliveries", ""),
        ))

    all_lines = db.query(ProductionLine).all()
    line_assignments = auto_assign_materials_to_lines(materials, all_lines, days, db)

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
                raise Exception(
                    f"产线 '{line.name}' 产能不足以满足物料 '{product.name}' 的交货需求。"
                    f"排产周期 {days} 天，最大产能 {max_possible:.0f}，净需求 {net_demand:.0f}"
                )

    plan = DeliveryPlan(name=name, start_date=start_date, end_date=end_date)
    db.add(plan)
    db.flush()

    for line_idx, la in enumerate(line_assignments):
        line = la["line"]
        plan_line = PlanLine(plan_id=plan.id, line_id=line.id, sort_order=line_idx)
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

    print(f"\n  ✅ 计划 '{name}' 创建成功 (ID={plan.id})")
    print(f"     排产周期: {days} 天  ({start_date} ~ {end_date})")
    for la in line_assignments:
        line = la["line"]
        print(f"     产线: {line.name}")
        for ma in la["materials"]:
            lp = ma["line_product"]
            product = db.query(Product).filter(Product.id == ma["product_id"]).first()
            dd_str = ma.get("daily_deliveries_str", "")
            print(f"       └ {product.name}: "
                  f"总交货={ma['total_delivery']:.0f}, "
                  f"初期库存={ma['initial_inventory']:.0f}, "
                  f"安全库存={ma['safety_stock']:.0f}, "
                  f"班产={lp.rated_output:.0f}")

    # ── 运行排产计算 ──
    print(f"\n  🧮 运行排产计算...")
    line_results = []
    for plan_line in plan.lines:
        product_params_list = []
        for pm in plan_line.materials:
            lp = pm.line_product
            pp = ProductParams(
                initial_inventory=pm.initial_inventory,
                safety_stock=lp.safety_stock,
                rated_output=lp.rated_output,
                total_delivery=pm.total_delivery,
                daily_deliveries=_parse_dd(pm.daily_deliveries, plan.start_date, plan.end_date),
            )
            product_params_list.append(pp)

        params = SchedulingParams(
            products=product_params_list,
            start_date=plan.start_date,
            end_date=plan.end_date,
        )
        result = SchedulingService.calculate(params, config, [])
        result["line_id"] = plan_line.line_id
        result["line_name"] = plan_line.line.name
        line_results.append(result)

    overall_success = all(r["success"] for r in line_results)
    if overall_success:
        print(f"  🟢 排产成功! ({len(line_results)} 条产线)")
    else:
        print(f"  🔴 排产失败! ({len(line_results)} 条产线)")

    for lr in line_results:
        status = "🟢" if lr["success"] else "🔴"
        print(f"      {status} {lr['line_name']}: "
              f"solver={lr.get('solver_status','?')}, "
              f"耗时={lr.get('solve_time',0):.1f}s, "
              f"生产天数={lr.get('total_production_days',0)}, "
              f"占用休息日={lr.get('rest_days_occupied',0)}")
        for psi, ps in enumerate(lr.get("product_stats", [])):
            print(f"         物料{psi+1}: "
                  f"最低库存={ps.get('min_inventory',0):.0f}, "
                  f"期末库存={ps.get('final_inventory',0):.0f}, "
                  f"假日生产={ps.get('holiday_production_days',0)}天, "
                  f"交付达成={'✅' if ps.get('delivery_fulfilled') else '❌'}")

    return plan


def main():
    init_db()
    db = SessionLocal()

    try:
        print("=" * 60)
        print("🚀 智能排产 POC — 测试数据 + 排产计算")
        print("=" * 60)

        config = AlgorithmConfig(max_time_seconds=30, rest_day_weight=50.0)

        # ── 1. 创建物料 ──
        print("\n📦 创建测试物料...")
        pA = get_or_create_product(db, "P-测试A", code="TA", safety_stock=100)
        pB = get_or_create_product(db, "P-测试B", code="TB", safety_stock=200)
        pC = get_or_create_product(db, "P-测试C", code="TC", safety_stock=150)
        pD = get_or_create_product(db, "P-测试D", code="TD", safety_stock=50)
        print(f"   P-测试A (id={pA.id}, safety=100)")
        print(f"   P-测试B (id={pB.id}, safety=200)")
        print(f"   P-测试C (id={pC.id}, safety=150)")
        print(f"   P-测试D (id={pD.id}, safety=50)")

        # ── 2. 创建产线 ──
        print("\n🏭 创建测试产线...")
        l1 = get_or_create_line(db, "L-测试线1")
        l2 = get_or_create_line(db, "L-测试线2")
        l3 = get_or_create_line(db, "L-测试线3")
        print(f"   L-测试线1 (id={l1.id})")
        print(f"   L-测试线2 (id={l2.id})")
        print(f"   L-测试线3 (id={l3.id})")

        # ── 3. 关联产线与物料 ──
        print("\n🔗 关联产线-物料 (LineProduct)...")
        get_or_create_line_product(db, l1.id, pA.id, rated_output=200, safety_stock=100)
        get_or_create_line_product(db, l1.id, pB.id, rated_output=180, safety_stock=200)
        print(f"   L-测试线1 ← A(rated=200,safety=100), B(rated=180,safety=200)")

        get_or_create_line_product(db, l2.id, pA.id, rated_output=100, safety_stock=100)
        get_or_create_line_product(db, l2.id, pB.id, rated_output=80, safety_stock=200)
        get_or_create_line_product(db, l2.id, pC.id, rated_output=120, safety_stock=150)
        print(f"   L-测试线2 ← A(rated=100), B(rated=80), C(rated=120)")

        get_or_create_line_product(db, l3.id, pA.id, rated_output=60, safety_stock=100)
        get_or_create_line_product(db, l3.id, pC.id, rated_output=90, safety_stock=150)
        get_or_create_line_product(db, l3.id, pD.id, rated_output=200, safety_stock=50)
        print(f"   L-测试线3 ← A(rated=60), C(rated=90), D(rated=200)")

        db.commit()

        base = date(2026, 6, 1)

        # ── 场景1: 单产线单物料 ──
        print("\n" + "=" * 60)
        print("📋 场景1: 单产线单物料 — 只有产线3能生产D")
        print("=" * 60)
        create_delivery_plan(db, "测试-单产线单物料",
            materials_data=[
                {"product_id": pD.id, "initial_inventory": 300, "total_delivery": 1800},
            ],
            start_date=base,
            end_date=base + timedelta(days=14),
            config=config,
        )

        # ── 场景2: 单产线双物料完全匹配 ──
        print("\n" + "=" * 60)
        print("📋 场景2: 单产线双物料 — 产线1完全覆盖A和B")
        print("=" * 60)
        create_delivery_plan(db, "测试-单产线双物料",
            materials_data=[
                {"product_id": pA.id, "initial_inventory": 1000, "total_delivery": 5000},
                {"product_id": pB.id, "initial_inventory": 500, "total_delivery": 3600},
            ],
            start_date=base,
            end_date=base + timedelta(days=19),
            config=config,
        )

        # ── 场景3: 多产线交叉覆盖 ──
        print("\n" + "=" * 60)
        print("📋 场景3: 多产线交叉 — 无单线覆盖A+B+C")
        print("=" * 60)
        create_delivery_plan(db, "测试-多产线交叉",
            materials_data=[
                {"product_id": pA.id, "initial_inventory": 500, "total_delivery": 3000},
                {"product_id": pB.id, "initial_inventory": 300, "total_delivery": 2000},
                {"product_id": pC.id, "initial_inventory": 200, "total_delivery": 1500},
            ],
            start_date=base,
            end_date=base + timedelta(days=29),
            config=config,
        )

        # ── 场景4: 过载拆分 — 强制触发 _resolve_overload ──
        print("\n" + "=" * 60)
        print("📋 场景4: 过载拆分 — 产线1超负荷，触发_resolve_overload")
        print("      A净需求=(2800-300+100)=2600, B净需求=(1800-400+200)=1600")
        print("      产线1(7天): A班产200+B班产180 → 需21.89班次 > 可用21")
        print("      首日init覆盖安全库存门槛，触发_resolve_overload拆分")
        print("=" * 60)
        create_delivery_plan(db, "测试-过载拆分",
            materials_data=[
                {"product_id": pA.id, "initial_inventory": 300, "total_delivery": 2800},
                {"product_id": pB.id, "initial_inventory": 400, "total_delivery": 1800},
            ],
            start_date=base,
            end_date=base + timedelta(days=6),
            config=config,
        )

        # ── 场景5: 安全库存拆分 — 验证库存和安全库存按比例分配 ──
        print("\n" + "=" * 60)
        print("📋 场景5: 安全库存拆分 — 过载拆分 + 验证安全库存按比例分配")
        print("      A净需求=(3200-500+100)=2800, B净需求=(2000-400+200)=1800")
        print("      产线1(7天): A班产200+B班产180 → 需24.0班次 > 可用21")
        print("      拆分后每条产线承担比例的初期库存和安全库存")
        print("=" * 60)
        create_delivery_plan(db, "测试-安全库存拆分",
            materials_data=[
                {"product_id": pA.id, "initial_inventory": 500, "total_delivery": 3200},
                {"product_id": pB.id, "initial_inventory": 400, "total_delivery": 2000},
            ],
            start_date=base,
            end_date=base + timedelta(days=6),
            config=config,
        )

        print("\n" + "=" * 60)
        print("✅ 全部 5 个测试场景创建并完成排产计算！")
        print("=" * 60)
        print("\n可用 API 查看:")
        print("  GET http://localhost:8000/api/delivery-plans")
        print("  GET http://localhost:8000/api/delivery-plans/{id}")
        print("\n或在 Swagger UI 中查看:")
        print("  http://localhost:8000/docs")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 错误: {e}")
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
