import time
import os
from datetime import date, timedelta
from typing import List, Optional
from ortools.sat.python import cp_model
import chinese_calendar


class ORToolsScheduler:
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
    WORKDAY_OT = {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 2}
    RESTDAY_OT = {0: 0, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
    WORKDAY_HAS_OT = {0: False, 1: False, 2: False, 3: False, 4: True, 5: True}
    RESTDAY_HAS_OT = {0: False, 1: True, 2: True, 3: True, 4: True, 5: True}
    MAX_DAILY_TOTAL = 3.0

    def __init__(
        self,
        initial_inventory: float,
        safety_stock: float,
        rated_output: float,
        total_delivery: float,
        start_date: date,
        end_date: date,
        holidays: List[date],
        daily_deliveries: Optional[List[dict]] = None,
        max_time_seconds: int = 10,
        overtime_shift_weight: float = 10.0,
        overtime_day_weight: float = 5.0,
        rest_day_weight: float = 20.0,
        max_consecutive_work_days: int = 7,
        **kwargs,
    ):
        self.initial_inventory = initial_inventory
        self.safety_stock = safety_stock
        self.rated_output = rated_output
        self.total_delivery = total_delivery
        self.start_date = start_date
        self.end_date = end_date
        self.holidays = set(holidays)
        self.daily_deliveries = daily_deliveries or []
        self.max_time_seconds = max_time_seconds
        self.scale = 2
        OT_NORMALIZE = 6
        self.overtime_shift_weight = int(overtime_shift_weight * self.scale / OT_NORMALIZE)
        self.overtime_day_weight = int(overtime_day_weight * self.scale / OT_NORMALIZE)
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

        self.delivery_map = {}
        for dd in self.daily_deliveries:
            d = dd["date"] if isinstance(dd["date"], date) else date.fromisoformat(str(dd["date"]))
            self.delivery_map[d] = int(dd["quantity"])

        self._daily_delivery_list = self._compute_daily_deliveries()

        self._validate_feasibility()

    def _validate_feasibility(self):
        n = self.max_consecutive_work_days
        max_work_days = self.days // (n + 1) * n + min(self.days % (n + 1), n)
        max_possible = max_work_days * self.MAX_DAILY_TOTAL * self.rated_output
        net_demand = self.total_delivery - self.initial_inventory + self.safety_stock
        if net_demand > 0 and max_possible < net_demand:
            raise ValueError(
                f"即使在最大连续工作{n}天的约束下，产能极限仍无法满足净需求。"
                f"最大可排产天数{max_work_days}天（共{self.days}天），"
                f"最大产能{max_possible:.0f}，净需求{net_demand}"
            )

    def _compute_daily_deliveries(self) -> list:
        result = []
        for i in range(self.days):
            d = self.dates[i]
            if d in self.delivery_map:
                result.append(self.delivery_map[d])
            else:
                result.append(None)

        uniform_indices = [i for i, v in enumerate(result) if v is None]
        if uniform_indices:
            total_assigned = sum(v for v in result if v is not None)
            remaining = int(self.total_delivery) - total_assigned
            n = len(uniform_indices)
            base = remaining // n
            extra = remaining % n
            for idx, ui in enumerate(uniform_indices):
                result[ui] = base + (1 if idx < extra else 0)

        return result

    def _get_daily_delivery(self, day_idx: int) -> int:
        return self._daily_delivery_list[day_idx]

    def _build_model(self):
        model = cp_model.CpModel()
        S = self.scale
        max_prod = int(self.MAX_DAILY_TOTAL * self.rated_output * S)

        prod_table = [int((self.COMBOS[cv][0] + self.COMBOS[cv][1]) * self.rated_output * S) for cv in self.COMBO_DOMAIN]

        combo_vars = []
        for i in range(self.days):
            var = model.NewIntVarFromDomain(
                cp_model.Domain.FromValues(self.COMBO_DOMAIN), f"combo_{i}"
            )
            combo_vars.append(var)

        production_vars = []
        overtime_count_vars = []
        overtime_day_vars = []
        rest_occupied_vars = []
        for i in range(self.days):
            prod = model.NewIntVar(0, max_prod, f"prod_{i}")
            model.AddElement(combo_vars[i], prod_table, prod)
            production_vars.append(prod)

            if self.rest_flags[i]:
                ot_table = [self.RESTDAY_OT[cv] for cv in self.COMBO_DOMAIN]
                has_ot_table = [1 if self.RESTDAY_HAS_OT[cv] else 0 for cv in self.COMBO_DOMAIN]
                rest_occ_table = [0 if cv == 0 else 1 for cv in self.COMBO_DOMAIN]
            else:
                ot_table = [self.WORKDAY_OT[cv] for cv in self.COMBO_DOMAIN]
                has_ot_table = [1 if self.WORKDAY_HAS_OT[cv] else 0 for cv in self.COMBO_DOMAIN]
                rest_occ_table = [0 for _ in self.COMBO_DOMAIN]

            ot_count = model.NewIntVar(0, 6, f"ot_count_{i}")
            model.AddElement(combo_vars[i], ot_table, ot_count)
            overtime_count_vars.append(ot_count)

            ot_day = model.NewBoolVar(f"ot_day_{i}")
            model.AddElement(combo_vars[i], has_ot_table, ot_day)
            overtime_day_vars.append(ot_day)

            rest_occupied = model.NewBoolVar(f"rest_occupied_{i}")
            model.AddElement(combo_vars[i], rest_occ_table, rest_occupied)
            rest_occupied_vars.append(rest_occupied)

        cumulative_delivery = 0
        inventory_vars = []
        for i in range(self.days):
            cumulative_delivery += self._get_daily_delivery(i)
            inv_ub = int(self.initial_inventory * S) + (i + 1) * max_prod - int(cumulative_delivery * S)
            inv_lb = int(self.safety_stock * S)
            inv = model.NewIntVar(inv_lb, inv_ub, f"inv_{i}")
            inventory_vars.append(inv)

        for i in range(self.days):
            daily_delivery_scaled = int(self._get_daily_delivery(i) * S)
            if i == 0:
                model.Add(
                    inventory_vars[i]
                    == int(self.initial_inventory * S) + production_vars[i] - daily_delivery_scaled
                )
            else:
                model.Add(
                    inventory_vars[i]
                    == inventory_vars[i - 1] + production_vars[i] - daily_delivery_scaled
                )

        for i in range(self.days):
            model.Add(inventory_vars[i] >= int(self.safety_stock * S))

        final_inventory = inventory_vars[-1]
        final_inv_ub = int(self.initial_inventory * S) + self.days * max_prod - int(cumulative_delivery * S)
        final_excess_ub = final_inv_ub - int(self.safety_stock * S)
        final_excess = model.NewIntVar(0, final_excess_ub, "final_excess")
        model.Add(final_excess == final_inventory - int(self.safety_stock * S))

        total_overtime_shifts = sum(overtime_count_vars)
        total_overtime_days = sum(overtime_day_vars)
        total_rest_occupied = sum(rest_occupied_vars)

        is_work_day = []
        for i in range(self.days):
            w = model.NewBoolVar(f"is_work_{i}")
            model.Add(combo_vars[i] == 0).OnlyEnforceIf(w.Not())
            model.Add(combo_vars[i] > 0).OnlyEnforceIf(w)
            is_work_day.append(w)

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

        smoothness_vars = []
        for i in range(self.days - 1):
            diff = model.NewIntVar(-5, 5, f"combo_diff_{i}")
            model.Add(diff == combo_vars[i + 1] - combo_vars[i])
            abs_diff = model.NewIntVar(0, 5, f"combo_abs_diff_{i}")
            model.AddAbsEquality(abs_diff, diff)
            smoothness_vars.append(abs_diff)
        total_smoothness = sum(smoothness_vars)

        overproduction_weight = 1
        smoothness_weight = 5
        consecutive_weight = 60
        primary_obj = (
            overproduction_weight * final_excess
            + self.overtime_shift_weight * total_overtime_shifts
            + self.overtime_day_weight * total_overtime_days
            + self.rest_day_weight * total_rest_occupied
            + smoothness_weight * total_smoothness
            + consecutive_weight * total_consecutive_penalty
        )

        return model, combo_vars, primary_obj

    def run(self) -> dict:
        model, combo_vars, primary_obj = self._build_model()

        model.Minimize(primary_obj)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_time_seconds
        solver.parameters.num_workers = min(8, os.cpu_count() or 4)

        t0 = time.perf_counter()
        status = solver.Solve(model)
        solve_time = round(time.perf_counter() - t0, 4)
        status_name = solver.StatusName(status)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            combos = [solver.Value(combo_vars[i]) for i in range(self.days)]
            result = self._build_result(combos)
            result["solver_status"] = status_name
            result["solve_time"] = solve_time
            return result

        return {
            "success": False,
            "message": "无可行排产方案：在给定约束条件下无法满足库存安全与交货需求，请调整参数或延长排产周期",
            "daily_results": [],
            "total_production_days": 0,
            "overtime_days": 0,
            "overtime_shifts": 0,
            "holiday_production_days": 0,
            "min_inventory": 0,
            "final_inventory": 0,
            "delivery_fulfilled": False,
            "solver_status": status_name,
            "solve_time": solve_time,
        }

    def _build_result(self, combos: list) -> dict:
        inventory = int(self.initial_inventory)
        total_produced = 0
        daily_results = []
        holiday_prod_days = 0
        total_overtime_shifts = 0
        total_overtime_days = 0
        min_inventory = float("inf")

        for i, cv in enumerate(combos):
            s1, s2 = self.COMBOS[cv]
            daily_output = int((s1 + s2) * self.rated_output)
            daily_delivery = self._get_daily_delivery(i)
            inventory = inventory + daily_output - daily_delivery
            total_produced += daily_output

            is_rest = self.rest_flags[i]
            is_holiday = self.calendar_holiday_flags[i] or self.user_holiday_flags[i]
            is_adjusted_workday = self.calendar_adjusted_workday_flags[i]
            inv_violation = inventory < self.safety_stock
            min_inventory = min(min_inventory, inventory)

            if cv > 0 and is_rest:
                holiday_prod_days += 1

            if is_rest:
                total_overtime_shifts += self.RESTDAY_OT[cv]
                if self.RESTDAY_HAS_OT[cv]:
                    total_overtime_days += 1
            else:
                total_overtime_shifts += self.WORKDAY_OT[cv]
                if self.WORKDAY_HAS_OT[cv]:
                    total_overtime_days += 1

            shift_label = self.COMBO_LABELS[cv]
            prod1 = int(s1 * self.rated_output)
            prod2 = int(s2 * self.rated_output)

            if s2 > 0:
                prod_label = f"{self._fmt_num(prod1)}+{self._fmt_num(prod2)}"
            elif s1 > 0:
                prod_label = self._fmt_num(prod1)
            else:
                prod_label = "0"

            daily_results.append(
                {
                    "date": self.dates[i].isoformat(),
                    "is_holiday": is_holiday,
                    "is_rest": is_rest,
                    "is_adjusted_workday": is_adjusted_workday,
                    "combo": cv,
                    "shift1": s1,
                    "shift2": s2,
                    "shift_label": shift_label,
                    "prod1": int(prod1),
                    "prod2": int(prod2),
                    "prod_label": prod_label,
                    "work_hours": (s1 + s2) * 8,
                    "daily_output": daily_output,
                    "daily_delivery": daily_delivery,
                    "closing_inventory": inventory,
                    "inventory_violation": inv_violation,
                }
            )

        production_days = sum(1 for cv in combos if cv > 0)
        final_inv = daily_results[-1]["closing_inventory"] if daily_results else 0

        return {
            "success": True,
            "message": "排产计算完成（OR-Tools CP-SAT求解器）",
            "daily_results": daily_results,
            "total_production_days": production_days,
            "overtime_days": total_overtime_days,
            "overtime_shifts": total_overtime_shifts,
            "holiday_production_days": holiday_prod_days,
            "min_inventory": min_inventory,
            "final_inventory": final_inv,
            "delivery_fulfilled": total_produced + self.initial_inventory >= self.total_delivery,
        }

    @staticmethod
    def _fmt_num(val: float) -> str:
        if val == int(val):
            return str(int(val))
        return str(round(val, 2))
