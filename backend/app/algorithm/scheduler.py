import time
import os
from datetime import date, timedelta
from typing import List, Optional
from ortools.sat.python import cp_model
import chinese_calendar
from ..models.schemas import ProductParams


class TwoProductScheduler:
    COMBO_DOMAIN = [0, 1, 2, 3, 4, 5]
    COMBOS = {
        0: (0, 0),
        1: (1.0, 0),
        2: (1.0, 0.5),
        3: (1.0, 1.0),
        4: (1.5, 1.0),
        5: (1.5, 1.5),
    }
    COMBO_LABELS = {
        0: "休息",
        1: "1班",
        2: "1班+0.5班",
        3: "1班+1班",
        4: "1.5班+1班",
        5: "1.5班+1.5班",
    }
    SHIFT_TOTALS = [0, 1.0, 1.5, 2.0, 2.5, 3.0]
    MAX_DAILY_SHIFTS = 3.0

    def __init__(
        self,
        product_1: ProductParams,
        product_2: ProductParams,
        start_date: date,
        end_date: date,
        holidays: List[date],
        max_time_seconds: int = 10,
        rest_day_weight: float = 50.0,
        max_consecutive_work_days: int = 7,
        **kwargs,
    ):
        self.initial_inventory_1 = product_1.initial_inventory
        self.safety_stock_1 = product_1.safety_stock
        self.rated_output_1 = product_1.rated_output
        self.total_delivery_1 = product_1.total_delivery
        self.daily_deliveries_1 = product_1.daily_deliveries or []

        self.initial_inventory_2 = product_2.initial_inventory
        self.safety_stock_2 = product_2.safety_stock
        self.rated_output_2 = product_2.rated_output
        self.total_delivery_2 = product_2.total_delivery
        self.daily_deliveries_2 = product_2.daily_deliveries or []

        self.start_date = start_date
        self.end_date = end_date
        self.holidays = set(holidays)
        self.max_time_seconds = max_time_seconds
        self.scale = 2
        self.rest_day_weight = int(rest_day_weight * self.scale)
        self.max_consecutive_work_days = max_consecutive_work_days

        self.days = (end_date - start_date).days + 1
        self.dates = [start_date + timedelta(days=i) for i in range(self.days)]

        self.calendar_rest_flags = []
        self.calendar_holiday_flags = []
        self.calendar_adjusted_workday_flags = []
        for d in self.dates:
            is_cal_rest = not chinese_calendar.is_workday(d)
            is_cal_holiday = chinese_calendar.is_holiday(d)
            is_adjusted = d.weekday() >= 5 and chinese_calendar.is_workday(d)
            self.calendar_rest_flags.append(is_cal_rest)
            self.calendar_holiday_flags.append(is_cal_holiday)
            self.calendar_adjusted_workday_flags.append(is_adjusted)

        self.user_holiday_flags = [d in self.holidays for d in self.dates]
        self.rest_flags = [
            self.calendar_rest_flags[i] or self.user_holiday_flags[i]
            for i in range(self.days)
        ]

        self.delivery_map_1 = {}
        for dd in self.daily_deliveries_1:
            d = dd["date"] if isinstance(dd["date"], date) else date.fromisoformat(str(dd["date"]))
            self.delivery_map_1[d] = int(dd["quantity"])

        self.delivery_map_2 = {}
        for dd in self.daily_deliveries_2:
            d = dd["date"] if isinstance(dd["date"], date) else date.fromisoformat(str(dd["date"]))
            self.delivery_map_2[d] = int(dd["quantity"])

        self._daily_delivery_list_1 = self._compute_daily_deliveries(self.total_delivery_1, self.delivery_map_1)
        self._daily_delivery_list_2 = self._compute_daily_deliveries(self.total_delivery_2, self.delivery_map_2)

        self._validate_feasibility()

    def _validate_feasibility(self):
        n = self.max_consecutive_work_days
        max_work_days = self.days // (n + 1) * n + min(self.days % (n + 1), n)

        for label, rated, init, saf, total in [
            ("物品1", self.rated_output_1, self.initial_inventory_1, self.safety_stock_1, self.total_delivery_1),
            ("物品2", self.rated_output_2, self.initial_inventory_2, self.safety_stock_2, self.total_delivery_2),
        ]:
            max_possible = max_work_days * self.MAX_DAILY_SHIFTS * rated
            net_demand = total - init + saf
            if net_demand > 0 and max_possible < net_demand:
                raise ValueError(
                    f"{label}：即使在最大连续工作{n}天的约束下，产能极限仍无法满足净需求。"
                    f"最大可排产天数{max_work_days}天（共{self.days}天），"
                    f"最大产能{max_possible:.0f}，净需求{net_demand}"
                )

        total_max = max_work_days * self.MAX_DAILY_SHIFTS * (self.rated_output_1 + self.rated_output_2)
        total_net = (
            max(0, self.total_delivery_1 - self.initial_inventory_1 + self.safety_stock_1)
            + max(0, self.total_delivery_2 - self.initial_inventory_2 + self.safety_stock_2)
        )
        if total_net > total_max:
            raise ValueError(
                f"两个物品合计净需求{total_net}超过总产能极限{total_max:.0f}"
            )

    def _compute_daily_deliveries(self, total_delivery: float, delivery_map: dict) -> list:
        result = []
        for i in range(self.days):
            d = self.dates[i]
            if d in delivery_map:
                result.append(delivery_map[d])
            else:
                result.append(None)

        uniform_indices = [i for i, v in enumerate(result) if v is None]
        if uniform_indices:
            total_assigned = sum(v for v in result if v is not None)
            remaining = int(total_delivery) - total_assigned
            n = len(uniform_indices)
            base = remaining // n
            extra = remaining % n
            for idx, ui in enumerate(uniform_indices):
                result[ui] = base + (1 if idx < extra else 0)

        return result

    def _get_daily_delivery(self, day_idx: int, product: str) -> int:
        if product == "1":
            return self._daily_delivery_list_1[day_idx]
        return self._daily_delivery_list_2[day_idx]

    def _build_model(self):
        model = cp_model.CpModel()
        S = self.scale

        max_prod_1 = int(self.MAX_DAILY_SHIFTS * self.rated_output_1 * S)
        max_prod_2 = int(self.MAX_DAILY_SHIFTS * self.rated_output_2 * S)

        prod_table_1 = [
            int((self.COMBOS[cv][0] + self.COMBOS[cv][1]) * self.rated_output_1 * S)
            for cv in self.COMBO_DOMAIN
        ]
        prod_table_2 = [
            int((self.COMBOS[cv][0] + self.COMBOS[cv][1]) * self.rated_output_2 * S)
            for cv in self.COMBO_DOMAIN
        ]

        shift_table = [int(st * S) for st in self.SHIFT_TOTALS]
        max_shift_scaled = int(self.MAX_DAILY_SHIFTS * S)

        combo_1_vars = []
        combo_2_vars = []
        production_1_vars = []
        production_2_vars = []
        is_work_day = []

        for i in range(self.days):
            c1 = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(self.COMBO_DOMAIN), f"combo_1_{i}"
            )
            c2 = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(self.COMBO_DOMAIN), f"combo_2_{i}"
            )
            combo_1_vars.append(c1)
            combo_2_vars.append(c2)

            p1 = model.NewIntVar(0, max_prod_1, f"prod_1_{i}")
            p2 = model.NewIntVar(0, max_prod_2, f"prod_2_{i}")
            model.AddElement(c1, prod_table_1, p1)
            model.AddElement(c2, prod_table_2, p2)
            production_1_vars.append(p1)
            production_2_vars.append(p2)

            s1 = model.NewIntVar(0, max_shift_scaled, f"shift_1_{i}")
            s2 = model.NewIntVar(0, max_shift_scaled, f"shift_2_{i}")
            model.AddElement(c1, shift_table, s1)
            model.AddElement(c2, shift_table, s2)
            model.Add(s1 + s2 <= max_shift_scaled)

            w = model.NewBoolVar(f"is_work_{i}")
            model.Add(c1 + c2 == 0).OnlyEnforceIf(w.Not())
            model.Add(c1 + c2 > 0).OnlyEnforceIf(w)
            is_work_day.append(w)

        inventory_1_vars = self._build_inventory(
            model, production_1_vars, "1", self.initial_inventory_1, self.safety_stock_1, max_prod_1
        )
        inventory_2_vars = self._build_inventory(
            model, production_2_vars, "2", self.initial_inventory_2, self.safety_stock_2, max_prod_2
        )

        cumulative_delivery_1 = sum(self._get_daily_delivery(i, "1") for i in range(self.days))
        cumulative_delivery_2 = sum(self._get_daily_delivery(i, "2") for i in range(self.days))
        final_inv_ub_1 = int(self.initial_inventory_1 * S) + self.days * max_prod_1 - int(cumulative_delivery_1 * S)
        final_inv_ub_2 = int(self.initial_inventory_2 * S) + self.days * max_prod_2 - int(cumulative_delivery_2 * S)

        final_excess_1 = model.NewIntVar(0, final_inv_ub_1 - int(self.safety_stock_1 * S), "final_excess_1")
        model.Add(final_excess_1 == inventory_1_vars[-1] - int(self.safety_stock_1 * S))

        final_excess_2 = model.NewIntVar(0, final_inv_ub_2 - int(self.safety_stock_2 * S), "final_excess_2")
        model.Add(final_excess_2 == inventory_2_vars[-1] - int(self.safety_stock_2 * S))

        n = self.max_consecutive_work_days
        for i in range(self.days - n):
            model.Add(sum(is_work_day[i:i + n + 1]) <= n)

        consecutive_window_vars = []
        window_len = n - 1
        if window_len >= 2:
            for i in range(self.days - window_len + 1):
                window = is_work_day[i:i + window_len]
                all_work = model.NewBoolVar(f"consec_window_{i}")
                model.AddBoolAnd(window).OnlyEnforceIf(all_work)
                model.AddBoolOr([w.Not() for w in window]).OnlyEnforceIf(all_work.Not())
                consecutive_window_vars.append(all_work)
        total_consecutive_penalty = sum(consecutive_window_vars)

        fixed_rest_occupied = []
        for i in range(self.days):
            if self.rest_flags[i]:
                fixed_rest_occupied.append(is_work_day[i])
        total_rest_occupied = sum(fixed_rest_occupied)

        smoothness_1 = self._build_smoothness(model, combo_1_vars, "1")
        smoothness_2 = self._build_smoothness(model, combo_2_vars, "2")
        total_smoothness = smoothness_1 + smoothness_2

        overproduction_weight = 1
        smoothness_weight = 5
        consecutive_weight = 60
        primary_obj = (
            overproduction_weight * (final_excess_1 + final_excess_2)
            + self.rest_day_weight * total_rest_occupied
            + smoothness_weight * total_smoothness
            + consecutive_weight * total_consecutive_penalty
        )

        return model, combo_1_vars, combo_2_vars, primary_obj

    def _build_inventory(self, model, prod_vars, label, initial_inv, safety_stock, max_prod):
        S = self.scale
        inv_vars = []
        cumulative_delivery = 0
        for i in range(self.days):
            cumulative_delivery += self._get_daily_delivery(i, label)
            inv_ub = int(initial_inv * S) + (i + 1) * max_prod - int(cumulative_delivery * S)
            inv_lb = int(safety_stock * S)
            inv = model.NewIntVar(inv_lb, inv_ub, f"inv_{label}_{i}")
            inv_vars.append(inv)

        for i in range(self.days):
            dd_scaled = int(self._get_daily_delivery(i, label) * S)
            if i == 0:
                model.Add(inv_vars[i] == int(initial_inv * S) + prod_vars[i] - dd_scaled)
            else:
                model.Add(inv_vars[i] == inv_vars[i - 1] + prod_vars[i] - dd_scaled)

        for i in range(self.days):
            model.Add(inv_vars[i] >= int(safety_stock * S))

        return inv_vars

    def _build_smoothness(self, model, combo_vars, label):
        smooth_vars = []
        for i in range(self.days - 1):
            diff = model.NewIntVar(-5, 5, f"combo_diff_{label}_{i}")
            model.Add(diff == combo_vars[i + 1] - combo_vars[i])
            abs_diff = model.NewIntVar(0, 5, f"combo_abs_diff_{label}_{i}")
            model.AddAbsEquality(abs_diff, diff)
            smooth_vars.append(abs_diff)
        return sum(smooth_vars)

    def run(self) -> dict:
        model, combo_1_vars, combo_2_vars, primary_obj = self._build_model()

        model.Minimize(primary_obj)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_time_seconds
        solver.parameters.num_workers = min(8, os.cpu_count() or 4)

        t0 = time.perf_counter()
        status = solver.Solve(model)
        solve_time = round(time.perf_counter() - t0, 4)
        status_name = solver.StatusName(status)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            combos_1 = [solver.Value(combo_1_vars[i]) for i in range(self.days)]
            combos_2 = [solver.Value(combo_2_vars[i]) for i in range(self.days)]
            result = self._build_result(combos_1, combos_2)
            result["solver_status"] = status_name
            result["solve_time"] = solve_time
            return result

        return {
            "success": False,
            "message": "无可行排产方案：在给定约束条件下无法满足库存安全与交货需求，请调整参数或延长排产周期",
            "daily_results": [],
            "total_production_days": 0,
            "rest_days_occupied": 0,
            "total_production_days_1": 0,
            "min_inventory_1": 0,
            "final_inventory_1": 0,
            "delivery_fulfilled_1": False,
            "holiday_production_days_1": 0,
            "total_production_days_2": 0,
            "min_inventory_2": 0,
            "final_inventory_2": 0,
            "delivery_fulfilled_2": False,
            "holiday_production_days_2": 0,
            "solver_status": status_name,
            "solve_time": solve_time,
        }

    def _build_result(self, combos_1: list, combos_2: list) -> dict:
        inv_1 = int(self.initial_inventory_1)
        inv_2 = int(self.initial_inventory_2)
        total_produced_1 = 0
        total_produced_2 = 0
        daily_results = []
        holiday_prod_1 = 0
        holiday_prod_2 = 0
        min_inv_1 = float("inf")
        min_inv_2 = float("inf")
        production_days = 0
        rest_days_occupied = 0

        for i, (c1, c2) in enumerate(zip(combos_1, combos_2)):
            s1_1, s2_1 = self.COMBOS[c1]
            s1_2, s2_2 = self.COMBOS[c2]
            d1 = int((s1_1 + s2_1) * self.rated_output_1)
            d2 = int((s1_2 + s2_2) * self.rated_output_2)
            dd1 = self._get_daily_delivery(i, "1")
            dd2 = self._get_daily_delivery(i, "2")
            inv_1 = inv_1 + d1 - dd1
            inv_2 = inv_2 + d2 - dd2
            total_produced_1 += d1
            total_produced_2 += d2

            is_rest = self.rest_flags[i]
            is_holiday = self.calendar_holiday_flags[i] or self.user_holiday_flags[i]
            is_adjusted = self.calendar_adjusted_workday_flags[i]
            inv_violation_1 = inv_1 < self.safety_stock_1
            inv_violation_2 = inv_2 < self.safety_stock_2
            min_inv_1 = min(min_inv_1, inv_1)
            min_inv_2 = min(min_inv_2, inv_2)

            line_working = c1 > 0 or c2 > 0
            if line_working:
                production_days += 1
                if is_rest:
                    rest_days_occupied += 1

            if c1 > 0 and is_rest:
                holiday_prod_1 += 1
            if c2 > 0 and is_rest:
                holiday_prod_2 += 1

            total_hours = (s1_1 + s2_1 + s1_2 + s2_2) * 8

            shift_label_1 = self.COMBO_LABELS[c1]
            prod1_1 = int(s1_1 * self.rated_output_1)
            prod2_1 = int(s2_1 * self.rated_output_1)
            prod_label_1 = self._fmt_prod(prod1_1, prod2_1, s1_1, s2_1)

            shift_label_2 = self.COMBO_LABELS[c2]
            prod1_2 = int(s1_2 * self.rated_output_2)
            prod2_2 = int(s2_2 * self.rated_output_2)
            prod_label_2 = self._fmt_prod(prod1_2, prod2_2, s1_2, s2_2)

            daily_results.append({
                "date": self.dates[i].isoformat(),
                "is_holiday": is_holiday,
                "is_rest": is_rest,
                "is_adjusted_workday": is_adjusted,
                "combo_1": c1,
                "shift1_1": s1_1,
                "shift2_1": s2_1,
                "shift_label_1": shift_label_1,
                "prod1_1": prod1_1,
                "prod2_1": prod2_1,
                "prod_label_1": prod_label_1,
                "work_hours_1": (s1_1 + s2_1) * 8,
                "daily_output_1": d1,
                "daily_delivery_1": dd1,
                "closing_inventory_1": inv_1,
                "inventory_violation_1": inv_violation_1,
                "combo_2": c2,
                "shift1_2": s1_2,
                "shift2_2": s2_2,
                "shift_label_2": shift_label_2,
                "prod1_2": prod1_2,
                "prod2_2": prod2_2,
                "prod_label_2": prod_label_2,
                "work_hours_2": (s1_2 + s2_2) * 8,
                "daily_output_2": d2,
                "daily_delivery_2": dd2,
                "closing_inventory_2": inv_2,
                "inventory_violation_2": inv_violation_2,
                "total_work_hours": total_hours,
            })

        final_inv_1 = daily_results[-1]["closing_inventory_1"] if daily_results else 0
        final_inv_2 = daily_results[-1]["closing_inventory_2"] if daily_results else 0

        return {
            "success": True,
            "message": "排产计算完成（OR-Tools CP-SAT双物品求解器）",
            "daily_results": daily_results,
            "total_production_days": production_days,
            "rest_days_occupied": rest_days_occupied,
            "total_production_days_1": sum(1 for cv in combos_1 if cv > 0),
            "min_inventory_1": int(min_inv_1),
            "final_inventory_1": int(final_inv_1),
            "delivery_fulfilled_1": total_produced_1 + self.initial_inventory_1 >= self.total_delivery_1,
            "holiday_production_days_1": holiday_prod_1,
            "total_production_days_2": sum(1 for cv in combos_2 if cv > 0),
            "min_inventory_2": int(min_inv_2),
            "final_inventory_2": int(final_inv_2),
            "delivery_fulfilled_2": total_produced_2 + self.initial_inventory_2 >= self.total_delivery_2,
            "holiday_production_days_2": holiday_prod_2,
        }

    @staticmethod
    def _fmt_prod(p1: int, p2: int, s1: float, s2: float) -> str:
        if s2 > 0:
            return f"{p1}+{p2}"
        if s1 > 0:
            return str(p1)
        return "0"