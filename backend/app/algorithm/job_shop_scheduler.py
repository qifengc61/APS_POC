import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ortools.sat.python import cp_model
from app.utils.time_calculator import calculate_duration, parse_throughput, parse_duration

logger = logging.getLogger("aps.scheduler")


HORIZON = 43200

DEFAULT_WEIGHTS = {
    "minimize_tardiness": 20,
    "finish_early": 6,
    "minimize_gap": 1,
    "balance_task_count": 10,
    "balance_workload": 0,
    "prioritize_delivery_time": 1,
    "minimize_tardiness_task_number": 1,
    "minimize_makespan": 20,
    "scheduling_rules": 54,
}


class JobShopScheduler:

    def __init__(
        self,
        tasks: List[dict],
        resources: List[dict],
        strategy_config: dict,
        planning_start: datetime,
        calendar_calculator=None,
        delivery_times: Optional[Dict[str, datetime]] = None,
    ):
        self.tasks = tasks
        self.resources = resources
        self.strategy_config = strategy_config
        self.planning_start = planning_start
        self.calendar_calculator = calendar_calculator
        self.delivery_times = delivery_times or {}
        self._use_work_time = self.calendar_calculator is not None

        if self._use_work_time:
            self.calendar_calculator.set_planning_start(planning_start)
            self._delivery_work_offsets = {}
            for order_id, dt in self.delivery_times.items():
                self._delivery_work_offsets[order_id] = self.calendar_calculator.calendar_to_work_minutes(dt)
        else:
            self._delivery_work_offsets = {}
            for order_id, dt in self.delivery_times.items():
                self._delivery_work_offsets[order_id] = max(0, int(
                    (dt - self.planning_start).total_seconds() / 60
                ))

        self.resource_index = {r["id"]: idx for idx, r in enumerate(self.resources)}
        self.task_index = {t["code"]: idx for idx, t in enumerate(self.tasks)}

        self.task_candidate_resources = []
        self.task_durations = []
        self.skipped_tasks = set()

        non_normal_resources = [
            r for r in self.resources
            if r.get("resource_status", "NORMAL") != "NORMAL"
        ]
        if non_normal_resources:
            logger.info("非正常状态资源: %s",
                        [(r['code'], r.get('resource_status')) for r in non_normal_resources])

        for idx, task in enumerate(self.tasks):
            process_info = task.get("process_info") or {}
            use_main_resources = process_info.get("use_main_resources", [])

            candidate_ids = []
            if isinstance(use_main_resources, list):
                for item in use_main_resources:
                    if isinstance(item, str):
                        candidate_ids.append(item)
                    elif isinstance(item, dict):
                        rid = item.get("resource_id") or item.get("id")
                        if rid:
                            candidate_ids.append(rid)

            valid_candidates = [
                rid for rid in candidate_ids
                if rid in self.resource_index
                and self.resources[self.resource_index[rid]].get("resource_status", "NORMAL") == "NORMAL"
            ]

            if not valid_candidates:
                existing_resource_ids = list(self.resource_index.keys())
                logger.warning(
                    "任务 %s(%s) 跳过 - 无可用资源。候选资源=%s, 系统资源IDs=%s, 匹配=%s",
                    task.get("code"), task.get("process_code"),
                    candidate_ids,
                    existing_resource_ids,
                    [rid for rid in candidate_ids if rid in self.resource_index]
                )
                self.skipped_tasks.add(idx)
                self.task_candidate_resources.append([])
                self.task_durations.append([])
                continue

            self.task_candidate_resources.append(valid_candidates)

            quantity = float(task.get("scheduled_quantity", 0))
            durations = []
            for rid in valid_candidates:
                res = self.resources[self.resource_index[rid]]
                throughput = res.get("throughput") or ""
                try:
                    dur = calculate_duration(throughput, quantity)
                except (ValueError, ZeroDivisionError):
                    dur = 60.0
                durations.append(max(1, int(round(dur))))

            self.task_durations.append(durations)
            logger.info("  任务 %s(%s): qty=%.0f, 资源=%d个, 工期=%s分",
                         task.get("code"), task.get("process_code"),
                         quantity, len(durations),
                         [f"{d}" for d in durations])

        self.weights = dict(DEFAULT_WEIGHTS)
        optimize_rules = strategy_config.get("optimize_rules") or []
        for rule in optimize_rules:
            key = rule.get("constraintKey")
            weight = rule.get("weight")
            if key and weight is not None:
                self.weights[key] = weight

        if self._use_work_time:
            logger.info("工作日历已激活，求解器将基于工作分钟空间建模")

    def build_model(self):
        active_tasks = [idx for idx in range(len(self.tasks)) if idx not in self.skipped_tasks]
        logger.info("构建CP模型: 总任务=%d, 跳过=%d, 有效=%d, 资源=%d",
                     len(self.tasks), len(self.skipped_tasks), len(active_tasks), len(self.resources))
        if not active_tasks:
            logger.error("所有任务均被跳过，无法构建模型!")

        total_work_minutes = sum(
            min(self.task_durations[idx]) for idx in active_tasks
        )
        horizon = max(HORIZON, int(total_work_minutes * 1.5) + 1440)
        self._horizon = horizon

        if self._use_work_time:
            logger.info("工作分钟空间: horizon=%d分(%.1f工时), 总工时=%d分",
                         horizon, horizon / 60, total_work_minutes)
        else:
            logger.info("日历分钟空间: horizon=%d分(%.1f天), 总工时=%d分",
                         horizon, horizon / 1440, total_work_minutes)
        if total_work_minutes > HORIZON:
            logger.warning("总工时超过默认时间窗, 已自动扩展至%d分", horizon)

        model = cp_model.CpModel()

        task_resource = {}
        task_start = {}
        task_end = {}
        task_duration = {}
        task_present = {}
        task_intervals = {}

        for idx in range(len(self.tasks)):
            if idx in self.skipped_tasks:
                continue

            candidates = self.task_candidate_resources[idx]
            num_candidates = len(candidates)
            durations = self.task_durations[idx]
            task = self.tasks[idx]

            task_resource[idx] = model.NewIntVar(
                0, num_candidates - 1, f"task_resource_{idx}"
            )
            task_start[idx] = model.NewIntVar(0, horizon, f"task_start_{idx}")
            task_end[idx] = model.NewIntVar(0, horizon, f"task_end_{idx}")

            min_dur = min(durations)
            max_dur = max(durations)
            task_duration[idx] = model.NewIntVar(
                min_dur, max_dur, f"task_duration_{idx}"
            )

            model.AddElement(task_resource[idx], durations, task_duration[idx])
            model.Add(task_end[idx] == task_start[idx] + task_duration[idx])

            task_present[idx] = {}
            task_intervals[idx] = {}
            for c_idx in range(num_candidates):
                present = model.NewBoolVar(f"task_{idx}_on_res_{c_idx}")
                task_present[idx][c_idx] = present

                interval = model.NewOptionalIntervalVar(
                    task_start[idx],
                    task_duration[idx],
                    task_end[idx],
                    present,
                    f"task_{idx}_interval_res_{c_idx}",
                )
                task_intervals[idx][c_idx] = interval

            for c_idx in range(num_candidates):
                model.Add(
                    task_resource[idx] == c_idx
                ).OnlyEnforceIf(task_present[idx][c_idx])
                model.Add(
                    task_resource[idx] != c_idx
                ).OnlyEnforceIf(task_present[idx][c_idx].Not())

            model.AddExactlyOne(task_present[idx].values())

            if task.get("pinned"):
                pinned_resource_id = task.get("main_resource_id")
                if pinned_resource_id and pinned_resource_id in candidates:
                    pinned_c_idx = candidates.index(pinned_resource_id)
                    model.Add(task_resource[idx] == pinned_c_idx)
                    model.Add(task_present[idx][pinned_c_idx] == 1)
                    for c_idx in range(num_candidates):
                        if c_idx != pinned_c_idx:
                            model.Add(task_present[idx][c_idx] == 0)

                pinned_start = task.get("start_time")
                if pinned_start:
                    if self._use_work_time:
                        offset = self.calendar_calculator.calendar_to_work_minutes(pinned_start)
                    else:
                        offset = int(
                            (pinned_start - self.planning_start).total_seconds() / 60
                        )
                    offset = max(0, min(offset, horizon))
                    model.Add(task_start[idx] == offset)

        resource_intervals = {rid: [] for rid in self.resource_index}
        for idx in range(len(self.tasks)):
            if idx in self.skipped_tasks:
                continue
            candidates = self.task_candidate_resources[idx]
            for c_idx, rid in enumerate(candidates):
                resource_intervals[rid].append(task_intervals[idx][c_idx])

        for rid, intervals in resource_intervals.items():
            if intervals:
                model.AddNoOverlap(intervals)

        for idx in range(len(self.tasks)):
            if idx in self.skipped_tasks:
                continue
            task = self.tasks[idx]
            front_codes = task.get("front_task_codes") or []
            process_info = task.get("process_info") or {}

            for front_code in front_codes:
                front_idx = self.task_index.get(front_code)
                if front_idx is None or front_idx in self.skipped_tasks:
                    continue

                front_task = self.tasks[front_idx]
                front_process_info = front_task.get("process_info") or {}

                post_interval_str = front_process_info.get(
                    "post_interval_duration", "0M"
                )
                try:
                    post_interval = int(parse_duration(post_interval_str))
                except (ValueError, TypeError):
                    post_interval = 0

                pre_interval_str = process_info.get("pre_interval_duration", "0M")
                try:
                    pre_interval = int(parse_duration(pre_interval_str))
                except (ValueError, TypeError):
                    pre_interval = 0

                total_interval = post_interval + pre_interval

                relationship = front_process_info.get("process_relationship", "ES")
                if relationship == "EE":
                    buffer_str = front_process_info.get("buffer_time", "0M")
                    try:
                        buffer = int(parse_duration(buffer_str))
                    except (ValueError, TypeError):
                        buffer = 0
                    model.Add(
                        task_start[idx]
                        >= task_start[front_idx] + buffer + pre_interval
                    )
                else:
                    model.Add(
                        task_start[idx] >= task_end[front_idx] + total_interval
                    )

        return model, task_start, task_end, task_duration, task_resource, task_present

    def _add_soft_constraints(
        self, model, task_start, task_end, task_duration, task_resource, task_present
    ):
        objective_terms = []

        w_tardiness = self.weights.get("minimize_tardiness", 0)
        w_early = self.weights.get("finish_early", 0)
        w_gap = self.weights.get("minimize_gap", 0)
        w_balance_count = self.weights.get("balance_task_count", 0)
        w_balance_load = self.weights.get("balance_workload", 0)
        w_delivery = self.weights.get("prioritize_delivery_time", 0)
        w_tardiness_count = self.weights.get("minimize_tardiness_task_number", 0)
        w_makespan = self.weights.get("minimize_makespan", 0)

        order_delivery_offset = {}
        if w_tardiness > 0 or w_tardiness_count > 0 or w_delivery > 0:
            for idx in range(len(self.tasks)):
                if idx in self.skipped_tasks:
                    continue
                task = self.tasks[idx]
                order_id = task.get("production_order_id")
                offset = self._delivery_work_offsets.get(order_id)
                if offset is not None:
                    order_delivery_offset[idx] = max(0, offset)

        if w_tardiness > 0:
            for idx in order_delivery_offset:
                if idx in self.skipped_tasks:
                    continue
                deadline = order_delivery_offset[idx]
                tardiness = model.NewIntVar(0, self._horizon, f"tardiness_{idx}")
                model.Add(tardiness >= task_end[idx] - deadline)
                model.Add(tardiness >= 0)
                objective_terms.append(w_tardiness * tardiness)

        if w_early > 0:
            for idx in range(len(self.tasks)):
                if idx in self.skipped_tasks:
                    continue
                objective_terms.append(w_early * task_end[idx])

        if w_makespan > 0:
            makespan = model.NewIntVar(0, self._horizon, "makespan")
            for idx in range(len(self.tasks)):
                if idx in self.skipped_tasks:
                    continue
                model.Add(makespan >= task_end[idx])
            objective_terms.append(w_makespan * makespan)

        if w_gap > 0:
            for idx in range(len(self.tasks)):
                if idx in self.skipped_tasks:
                    continue
                task = self.tasks[idx]
                front_codes = task.get("front_task_codes") or []
                for front_code in front_codes:
                    front_idx = self.task_index.get(front_code)
                    if front_idx is None or front_idx in self.skipped_tasks:
                        continue
                    gap = model.NewIntVar(
                        0, self._horizon, f"gap_{front_idx}_{idx}"
                    )
                    model.Add(gap >= task_start[idx] - task_end[front_idx])
                    objective_terms.append(w_gap * gap)

        if w_balance_count > 0:
            resource_task_counts = {}
            active_rids = []
            for rid in self.resource_index:
                presence_list = []
                for idx in range(len(self.tasks)):
                    if idx in self.skipped_tasks:
                        continue
                    candidates = self.task_candidate_resources[idx]
                    for c_idx, c_rid in enumerate(candidates):
                        if c_rid == rid:
                            presence_list.append(task_present[idx][c_idx])
                if presence_list:
                    count = model.NewIntVar(
                        0, len(self.tasks), f"res_task_count_{rid}"
                    )
                    model.Add(count == sum(presence_list))
                    resource_task_counts[rid] = count
                    active_rids.append(rid)

            if len(active_rids) >= 2:
                max_count = model.NewIntVar(
                    0, len(self.tasks), "max_task_count"
                )
                min_count = model.NewIntVar(
                    0, len(self.tasks), "min_task_count"
                )
                for rid in active_rids:
                    model.Add(max_count >= resource_task_counts[rid])
                    model.Add(min_count <= resource_task_counts[rid])
                count_spread = model.NewIntVar(
                    0, len(self.tasks), "task_count_spread"
                )
                model.Add(count_spread == max_count - min_count)
                objective_terms.append(w_balance_count * count_spread)

        if w_balance_load > 0:
            resource_workloads = {}
            active_rids_load = []
            for rid in self.resource_index:
                load_terms = []
                for idx in range(len(self.tasks)):
                    if idx in self.skipped_tasks:
                        continue
                    candidates = self.task_candidate_resources[idx]
                    for c_idx, c_rid in enumerate(candidates):
                        if c_rid == rid:
                            dur = self.task_durations[idx][c_idx]
                            load_var = model.NewIntVar(
                                0, self._horizon, f"load_{idx}_res_{c_idx}"
                            )
                            model.Add(
                                load_var == dur
                            ).OnlyEnforceIf(task_present[idx][c_idx])
                            model.Add(
                                load_var == 0
                            ).OnlyEnforceIf(task_present[idx][c_idx].Not())
                            load_terms.append(load_var)

                if not load_terms:
                    continue
                workload = model.NewIntVar(
                    0, self._horizon * len(self.tasks), f"res_workload_{rid}"
                )
                model.Add(workload == sum(load_terms))
                resource_workloads[rid] = workload
                active_rids_load.append(rid)

            if len(active_rids_load) >= 2:
                max_workload = model.NewIntVar(
                    0, self._horizon * len(self.tasks), "max_workload"
                )
                min_workload = model.NewIntVar(
                    0, self._horizon * len(self.tasks), "min_workload"
                )
                for rid in active_rids_load:
                    model.Add(max_workload >= resource_workloads[rid])
                    model.Add(min_workload <= resource_workloads[rid])
                workload_spread = model.NewIntVar(
                    0, self._horizon * len(self.tasks), "workload_spread"
                )
                model.Add(workload_spread == max_workload - min_workload)
                objective_terms.append(w_balance_load * workload_spread)

        if w_delivery > 0:
            active_offsets = {
                idx: order_delivery_offset[idx]
                for idx in order_delivery_offset
                if idx not in self.skipped_tasks
            }
            if active_offsets:
                offsets = list(active_offsets.values())
                max_off = max(offsets)
                min_off = min(offsets)
                off_range = max_off - min_off if max_off > min_off else 1
                for idx, offset in active_offsets.items():
                    norm_priority = 1 + int(
                        9 * (max_off - offset) / off_range
                    )
                    objective_terms.append(
                        w_delivery * norm_priority * task_start[idx]
                    )

        if w_tardiness_count > 0:
            for idx in order_delivery_offset:
                if idx in self.skipped_tasks:
                    continue
                deadline = order_delivery_offset[idx]
                is_late = model.NewBoolVar(f"is_late_{idx}")
                model.Add(
                    task_end[idx] > deadline
                ).OnlyEnforceIf(is_late)
                model.Add(
                    task_end[idx] <= deadline
                ).OnlyEnforceIf(is_late.Not())
                objective_terms.append(w_tardiness_count * is_late)

        return objective_terms

    def solve(self):
        (
            model,
            task_start,
            task_end,
            task_duration,
            task_resource,
            task_present,
        ) = self.build_model()

        objective_terms = self._add_soft_constraints(
            model, task_start, task_end, task_duration, task_resource, task_present
        )

        if objective_terms:
            model.Minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        max_time = self.strategy_config.get("maxNoImprovementTime", 300)
        solver.parameters.max_time_in_seconds = max_time
        solver.parameters.num_workers = min(8, os.cpu_count() or 4)

        t0 = time.perf_counter()
        status = solver.Solve(model)
        solve_time = round(time.perf_counter() - t0, 4)

        if status == cp_model.OPTIMAL:
            status_name = "OPTIMAL"
        elif status == cp_model.FEASIBLE:
            status_name = "FEASIBLE"
        else:
            status_name = "INFEASIBLE"

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.error(
                "求解器返回 %s。总任务=%d, 跳过=%d, 有效=%d, 资源=%d",
                status_name,
                len(self.tasks),
                len(self.skipped_tasks),
                len(self.tasks) - len(self.skipped_tasks),
                len(self.resources),
            )
            return {
                "success": False,
                "status": status_name,
                "tasks": [],
                "solve_time": solve_time,
                "objective_value": 0,
            }

        result_tasks = []
        for idx in range(len(self.tasks)):
            task = self.tasks[idx]
            if idx in self.skipped_tasks:
                result_tasks.append(
                    {
                        "task_id": task.get("id"),
                        "task_code": task.get("code"),
                        "resource_id": None,
                        "start_time": None,
                        "end_time": None,
                        "duration_minutes": 0,
                        "pinned": task.get("pinned", False),
                    }
                )
                continue

            c_idx = solver.Value(task_resource[idx])
            candidates = self.task_candidate_resources[idx]
            resource_id = candidates[c_idx]

            start_offset = solver.Value(task_start[idx])
            dur = solver.Value(task_duration[idx])
            end_offset = start_offset + dur

            res_info = self.resources[self.resource_index[resource_id]]
            logger.info("  求解结果 - %s -> %s(%s) offset=%d dur=%d",
                         task["code"], res_info["name"], res_info["code"],
                         start_offset, dur)

            if self._use_work_time:
                start_dt = self.calendar_calculator.work_minutes_to_calendar(start_offset)
                end_dt = self.calendar_calculator.work_minutes_to_calendar(end_offset)
            else:
                start_dt = self.planning_start + timedelta(minutes=start_offset)
                end_dt = self.planning_start + timedelta(minutes=end_offset)

            result_tasks.append(
                {
                    "task_id": task.get("id"),
                    "task_code": task.get("code"),
                    "resource_id": resource_id,
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "duration_minutes": dur,
                    "pinned": task.get("pinned", False),
                }
            )

        obj_val = solver.ObjectiveValue() if objective_terms else 0

        return {
            "success": True,
            "status": status_name,
            "tasks": result_tasks,
            "solve_time": solve_time,
            "objective_value": obj_val,
        }
