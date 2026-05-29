import time
import os
from datetime import date, timedelta
from typing import List, Optional
from ortools.sat.python import cp_model
import chinese_calendar
from ..models.schemas import ProductParams


class MultiProductScheduler:
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
        products: List[ProductParams],
        start_date: date,
        end_date: date,
        holidays: List[date],
        max_time_seconds: int = 10,
        rest_day_weight: float = 50.0,
        max_consecutive_work_days: int = 7,
        **kwargs,
    ):
        self.num_products = len(products)
        self.products_data = []
        for idx, p in enumerate(products):
            self.products_data.append({
                "initial_inventory": p.initial_inventory,
                "safety_stock": p.safety_stock,
                "rated_output": p.rated_output,
                "total_delivery": p.total_delivery,
                "daily_deliveries": p.daily_deliveries or [],
            })

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

        self._daily_delivery_lists = []
        for pidx in range(self.num_products):
            delivery_map = {}
            for dd in self.products_data[pidx]["daily_deliveries"]:
                d = dd["date"] if isinstance(dd["date"], date) else date.fromisoformat(str(dd["date"]))
                delivery_map[d] = int(dd["quantity"])
            self._daily_delivery_lists.append(
                self._compute_daily_deliveries(self.products_data[pidx]["total_delivery"], delivery_map)
            )

        self._validate_feasibility()

    def _validate_feasibility(self):
        n = self.max_consecutive_work_days
        max_work_days = self.days // (n + 1) * n + min(self.days % (n + 1), n)

        for pidx, pd in enumerate(self.products_data):
            label = f"物品{pidx + 1}"
            rated = pd["rated_output"]
            init = pd["initial_inventory"]
            saf = pd["safety_stock"]
            total = pd["total_delivery"]
            max_possible = max_work_days * self.MAX_DAILY_SHIFTS * rated
            net_demand = total - init + saf
            if net_demand > 0 and max_possible < net_demand:
                raise ValueError(
                    f"{label}：即使在最大连续工作{n}天的约束下，产能极限仍无法满足净需求。"
                    f"最大可排产天数{max_work_days}天（共{self.days}天），"
                    f"最大产能{max_possible:.0f}，净需求{net_demand}"
                )

        total_max = max_work_days * self.MAX_DAILY_SHIFTS * sum(pd["rated_output"] for pd in self.products_data)
        total_net = sum(
            max(0, pd["total_delivery"] - pd["initial_inventory"] + pd["safety_stock"])
            for pd in self.products_data
        )
        if total_net > total_max:
            raise ValueError(
                f"所有物品合计净需求{total_net}超过总产能极限{total_max:.0f}"
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
            num = len(uniform_indices)
            base = remaining // num
            extra = remaining % num
            for idx, ui in enumerate(uniform_indices):
                result[ui] = base + (1 if idx < extra else 0)

        return result

    def _get_daily_delivery(self, day_idx: int, product_idx: int) -> int:
        return self._daily_delivery_lists[product_idx][day_idx]

    def _build_model(self):
        model = cp_model.CpModel()
        S = self.scale

        shift_table = [int(st * S) for st in self.SHIFT_TOTALS]
        max_shift_scaled = int(self.MAX_DAILY_SHIFTS * S)

        all_combo_vars = []
        all_production_vars = []
        all_shift_vars = []
        is_work_day = []

        for pidx in range(self.num_products):
            pd = self.products_data[pidx]
            max_prod = int(self.MAX_DAILY_SHIFTS * pd["rated_output"] * S)
            prod_table = [
                int((self.COMBOS[cv][0] + self.COMBOS[cv][1]) * pd["rated_output"] * S)
                for cv in self.COMBO_DOMAIN
            ]

            combo_vars = []
            production_vars = []
            shift_vars = []

            for i in range(self.days):
                c = model.NewIntVarFromDomain(
                    cp_model.Domain.FromValues(self.COMBO_DOMAIN), f"combo_{pidx}_{i}"
                )
                combo_vars.append(c)

                p = model.NewIntVar(0, max_prod, f"prod_{pidx}_{i}")
                model.AddElement(c, prod_table, p)
                production_vars.append(p)

                s = model.NewIntVar(0, max_shift_scaled, f"shift_{pidx}_{i}")
                model.AddElement(c, shift_table, s)
                shift_vars.append(s)

            all_combo_vars.append(combo_vars)
            all_production_vars.append(production_vars)
            all_shift_vars.append(shift_vars)

        for i in range(self.days):
            model.Add(sum(all_shift_vars[pidx][i] for pidx in range(self.num_products)) <= max_shift_scaled)

            w = model.NewBoolVar(f"is_work_{i}")
            product_working = []
            for pidx in range(self.num_products):
                pw = model.NewBoolVar(f"pw_{pidx}_{i}")
                model.Add(all_combo_vars[pidx][i] > 0).OnlyEnforceIf(pw)
                model.Add(all_combo_vars[pidx][i] == 0).OnlyEnforceIf(pw.Not())
                product_working.append(pw)
            model.AddBoolOr(product_working).OnlyEnforceIf(w)
            model.AddBoolAnd([pw.Not() for pw in product_working]).OnlyEnforceIf(w.Not())
            is_work_day.append(w)

        all_inventory_vars = []
        for pidx in range(self.num_products):
            pd = self.products_data[pidx]
            inv_vars = self._build_inventory(
                model, all_production_vars[pidx], pidx,
                pd["initial_inventory"], pd["safety_stock"],
                int(self.MAX_DAILY_SHIFTS * pd["rated_output"] * S),
            )
            all_inventory_vars.append(inv_vars)

        total_final_excess = 0
        for pidx in range(self.num_products):
            pd = self.products_data[pidx]
            cumulative_delivery = sum(self._get_daily_delivery(i, pidx) for i in range(self.days))
            max_prod = int(self.MAX_DAILY_SHIFTS * pd["rated_output"] * S)
            final_inv_ub = int(pd["initial_inventory"] * S) + self.days * max_prod - int(cumulative_delivery * S)

            final_excess = model.NewIntVar(0, max(0, final_inv_ub - int(pd["safety_stock"] * S)), f"final_excess_{pidx}")
            model.Add(final_excess == all_inventory_vars[pidx][-1] - int(pd["safety_stock"] * S))
            total_final_excess += final_excess

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

        total_smoothness = 0
        for pidx in range(self.num_products):
            total_smoothness += self._build_smoothness(model, all_combo_vars[pidx], pidx)

        overproduction_weight = 1
        smoothness_weight = 5
        consecutive_weight = 60
        primary_obj = (
            overproduction_weight * total_final_excess
            + self.rest_day_weight * total_rest_occupied
            + smoothness_weight * total_smoothness
            + consecutive_weight * total_consecutive_penalty
        )

        return model, all_combo_vars, primary_obj

    def _build_inventory(self, model, prod_vars, pidx, initial_inv, safety_stock, max_prod):
        S = self.scale
        inv_vars = []
        cumulative_delivery = 0
        for i in range(self.days):
            cumulative_delivery += self._get_daily_delivery(i, pidx)
            inv_ub = int(initial_inv * S) + (i + 1) * max_prod - int(cumulative_delivery * S)
            inv_lb = int(safety_stock * S)
            inv = model.NewIntVar(inv_lb, inv_ub, f"inv_{pidx}_{i}")
            inv_vars.append(inv)

        for i in range(self.days):
            dd_scaled = int(self._get_daily_delivery(i, pidx) * S)
            if i == 0:
                model.Add(inv_vars[i] == int(initial_inv * S) + prod_vars[i] - dd_scaled)
            else:
                model.Add(inv_vars[i] == inv_vars[i - 1] + prod_vars[i] - dd_scaled)

        for i in range(self.days):
            model.Add(inv_vars[i] >= int(safety_stock * S))

        return inv_vars

    def _build_smoothness(self, model, combo_vars, pidx):
        smooth_vars = []
        for i in range(self.days - 1):
            diff = model.NewIntVar(-5, 5, f"combo_diff_{pidx}_{i}")
            model.Add(diff == combo_vars[i + 1] - combo_vars[i])
            abs_diff = model.NewIntVar(0, 5, f"combo_abs_diff_{pidx}_{i}")
            model.AddAbsEquality(abs_diff, diff)
            smooth_vars.append(abs_diff)
        return sum(smooth_vars)

    def run(self) -> dict:
        model, all_combo_vars, primary_obj = self._build_model()

        model.Minimize(primary_obj)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_time_seconds
        solver.parameters.num_workers = min(8, os.cpu_count() or 4)

        t0 = time.perf_counter()
        status = solver.Solve(model)
        solve_time = round(time.perf_counter() - t0, 4)
        status_name = solver.StatusName(status)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            all_combos = []
            for pidx in range(self.num_products):
                all_combos.append([solver.Value(all_combo_vars[pidx][i]) for i in range(self.days)])
            result = self._build_result(all_combos)
            result["solver_status"] = status_name
            result["solve_time"] = solve_time
            return result

        no_result = {
            "success": False,
            "message": "无可行排产方案：在给定约束条件下无法满足库存安全与交货需求，请调整参数或延长排产周期",
            "daily_results": [],
            "total_production_days": 0,
            "rest_days_occupied": 0,
            "num_products": self.num_products,
            "solver_status": status_name,
            "solve_time": solve_time,
        }
        for pidx in range(self.num_products):
            no_result[f"total_production_days_{pidx + 1}"] = 0
            no_result[f"min_inventory_{pidx + 1}"] = 0
            no_result[f"final_inventory_{pidx + 1}"] = 0
            no_result[f"delivery_fulfilled_{pidx + 1}"] = False
            no_result[f"holiday_production_days_{pidx + 1}"] = 0
        return no_result

    def _build_result(self, all_combos: list) -> dict:
        inventories = [int(pd["initial_inventory"]) for pd in self.products_data]
        total_produced = [0] * self.num_products
        holiday_prod = [0] * self.num_products
        min_inv = [float("inf")] * self.num_products
        production_days = 0
        rest_days_occupied = 0
        daily_results = []

        for i in range(self.days):
            day_combos = [all_combos[pidx][i] for pidx in range(self.num_products)]
            day_data = {
                "date": self.dates[i].isoformat(),
                "is_holiday": self.calendar_holiday_flags[i] or self.user_holiday_flags[i],
                "is_rest": self.rest_flags[i],
                "is_adjusted_workday": self.calendar_adjusted_workday_flags[i],
                "total_work_hours": 0,
            }

            for pidx in range(self.num_products):
                c = day_combos[pidx]
                s1, s2 = self.COMBOS[c]
                d = int((s1 + s2) * self.products_data[pidx]["rated_output"])
                dd = self._get_daily_delivery(i, pidx)
                inventories[pidx] = inventories[pidx] + d - dd
                total_produced[pidx] += d
                inv_violation = inventories[pidx] < self.products_data[pidx]["safety_stock"]
                min_inv[pidx] = min(min_inv[pidx], inventories[pidx])

                shift_label = self.COMBO_LABELS[c]
                prod1 = int(s1 * self.products_data[pidx]["rated_output"])
                prod2 = int(s2 * self.products_data[pidx]["rated_output"])
                prod_label = self._fmt_prod(prod1, prod2, s1, s2)
                work_hours = (s1 + s2) * 8

                day_data[f"combo_{pidx + 1}"] = c
                day_data[f"shift1_{pidx + 1}"] = s1
                day_data[f"shift2_{pidx + 1}"] = s2
                day_data[f"shift_label_{pidx + 1}"] = shift_label
                day_data[f"prod1_{pidx + 1}"] = prod1
                day_data[f"prod2_{pidx + 1}"] = prod2
                day_data[f"prod_label_{pidx + 1}"] = prod_label
                day_data[f"work_hours_{pidx + 1}"] = work_hours
                day_data[f"daily_output_{pidx + 1}"] = d
                day_data[f"daily_delivery_{pidx + 1}"] = dd
                day_data[f"closing_inventory_{pidx + 1}"] = inventories[pidx]
                day_data[f"inventory_violation_{pidx + 1}"] = inv_violation
                day_data["total_work_hours"] += work_hours

            line_working = any(c > 0 for c in day_combos)
            if line_working:
                production_days += 1
                if self.rest_flags[i]:
                    rest_days_occupied += 1

            for pidx in range(self.num_products):
                if day_combos[pidx] > 0 and self.rest_flags[i]:
                    holiday_prod[pidx] += 1

            daily_results.append(day_data)

        result = {
            "success": True,
            "message": f"排产计算完成（OR-Tools CP-SAT {self.num_products}物料求解器）",
            "daily_results": daily_results,
            "total_production_days": production_days,
            "rest_days_occupied": rest_days_occupied,
            "num_products": self.num_products,
        }

        for pidx in range(self.num_products):
            result[f"total_production_days_{pidx + 1}"] = sum(1 for cv in all_combos[pidx] if cv > 0)
            result[f"min_inventory_{pidx + 1}"] = int(min_inv[pidx])
            result[f"final_inventory_{pidx + 1}"] = int(inventories[pidx])
            result[f"delivery_fulfilled_{pidx + 1}"] = (
                total_produced[pidx] + self.products_data[pidx]["initial_inventory"]
                >= self.products_data[pidx]["total_delivery"]
            )
            result[f"holiday_production_days_{pidx + 1}"] = holiday_prod[pidx]

        return result

    @staticmethod
    def _fmt_prod(p1: int, p2: int, s1: float, s2: float) -> str:
        if s2 > 0:
            return f"{p1}+{p2}"
        if s1 > 0:
            return str(p1)
        return "0"
