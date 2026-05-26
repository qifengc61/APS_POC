import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

UNIT_MINUTES = {"D": 480, "H": 60, "M": 1, "S": 1 / 60}


def parse_throughput(throughput_str: str) -> dict:
    if not throughput_str:
        raise ValueError("产能字符串为空")
    throughput_str = throughput_str.strip()
    if throughput_str.endswith("/P"):
        rest = throughput_str[:-2]
        match = re.match(r'^(\d+(?:\.\d+)?)([DHMS])$', rest)
        if match:
            return {"type": "per_batch", "value": float(match.group(1)), "unit": match.group(2)}
    if "/" in throughput_str:
        match = re.match(r'^(\d+(?:\.\d+)?)/([DHMS])$', throughput_str)
        if match:
            return {"type": "per_time", "value": float(match.group(1)), "unit": match.group(2)}
    match = re.match(r'^(\d+(?:\.\d+)?)([DHMS])$', throughput_str)
    if match:
        return {"type": "per_unit", "value": float(match.group(1)), "unit": match.group(2)}
    raise ValueError(f"无法解析产能字符串: {throughput_str}")


def calculate_duration(throughput_str: str, quantity: float) -> float:
    parsed = parse_throughput(throughput_str)
    unit_minutes = UNIT_MINUTES[parsed["unit"]]
    if parsed["type"] == "per_unit":
        return parsed["value"] * quantity * unit_minutes
    elif parsed["type"] == "per_time":
        return (quantity / parsed["value"]) * unit_minutes
    elif parsed["type"] == "per_batch":
        return parsed["value"] * unit_minutes
    raise ValueError(f"未知的产能类型: {parsed['type']}")


def parse_duration(duration_str: str) -> float:
    if not duration_str:
        return 0
    duration_str = duration_str.strip()
    match = re.match(r'^(\d+(?:\.\d+)?)([DHMS])$', duration_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        return value * UNIT_MINUTES[unit]
    raise ValueError(f"无法解析时长字符串: {duration_str}")


class WorkCalendarCalculator:
    def __init__(self, calendars: List[dict], work_modes: List[dict]):
        self.work_modes = {wm["id"]: wm for wm in work_modes}
        self.calendars = sorted(
            calendars,
            key=lambda c: c.get("priority", 0),
            reverse=True,
        )
        self._planning_start = None

    def set_planning_start(self, dt: datetime):
        self._planning_start = dt

    def _get_calendar(self, dt: datetime) -> Optional[dict]:
        date = dt.date()
        for cal in self.calendars:
            if not cal.get("enabled", True):
                continue
            begin = cal.get("begin_time")
            end = cal.get("end_time")
            if begin is not None and date < begin:
                continue
            if end is not None and date > end:
                continue
            return cal
        return None

    def is_work_day(self, dt: datetime) -> bool:
        cal = self._get_calendar(dt)
        if cal is None:
            return False
        work_days = cal.get("work_days", "0000000")
        weekday = dt.weekday()
        index = (weekday + 1) % 7
        return index < len(work_days) and work_days[index] == "1"

    def get_daily_work_minutes(self, dt: datetime) -> int:
        if not self.is_work_day(dt):
            return 0
        periods = self.get_work_periods(dt)
        if not periods:
            return 0
        total = sum(
            int((end - start).total_seconds() / 60)
            for start, end in periods
        )
        return total

    def get_work_periods(self, dt: datetime) -> List[Tuple[datetime, datetime]]:
        cal = self._get_calendar(dt)
        if cal is None:
            return []
        work_mode = self.work_modes.get(cal.get("work_mode_id"))
        if work_mode is None:
            return []
        date = dt.date()
        periods = []
        for tp in work_mode.get("time_periods", []):
            start_parts = tp["start"].split(":")
            end_parts = tp["end"].split(":")
            start_dt = datetime(
                date.year, date.month, date.day,
                int(start_parts[0]), int(start_parts[1]),
            )
            end_dt = datetime(
                date.year, date.month, date.day,
                int(end_parts[0]), int(end_parts[1]),
            )
            periods.append((start_dt, end_dt))
        periods.sort(key=lambda p: p[0])
        return periods

    def calendar_to_work_minutes(self, dt: datetime) -> int:
        if self._planning_start is None:
            if dt <= self._planning_start:
                return 0
        total = 0
        current_date = self._planning_start.replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        while current_date < target_date:
            total += self.get_daily_work_minutes(current_date)
            current_date += timedelta(days=1)
        if self.is_work_day(dt):
            periods = self.get_work_periods(dt)
            for p_start, p_end in periods:
                if dt < p_start:
                    break
                if dt >= p_end:
                    total += int((p_end - p_start).total_seconds() / 60)
                else:
                    total += int((dt - p_start).total_seconds() / 60)
                    break
        return total

    def work_minutes_to_calendar(self, work_minutes: int) -> datetime:
        if work_minutes <= 0:
            return self._planning_start
        remaining = work_minutes
        current_date = self._planning_start.replace(hour=0, minute=0, second=0, microsecond=0)
        for _ in range(10000):
            if self.is_work_day(current_date):
                periods = self.get_work_periods(current_date)
                for p_start, p_end in periods:
                    period_mins = int((p_end - p_start).total_seconds() / 60)
                    if remaining <= period_mins:
                        return p_start + timedelta(minutes=remaining)
                    remaining -= period_mins
            current_date += timedelta(days=1)
        return self._planning_start

    def find_next_work_time(self, dt: datetime, resource_id: str = None) -> datetime:
        if self.is_work_day(dt):
            periods = self.get_work_periods(dt)
            for start, end in periods:
                if start <= dt < end:
                    return dt
                if dt < start:
                    return start
        current_date = datetime(dt.year, dt.month, dt.day) + timedelta(days=1)
        for _ in range(366):
            if self.is_work_day(current_date):
                periods = self.get_work_periods(current_date)
                if periods:
                    return periods[0][0]
            current_date += timedelta(days=1)
        return dt

    def find_work_period_end(self, dt: datetime, duration_minutes: float, resource_id: str = None) -> datetime:
        if duration_minutes <= 0:
            return dt
        remaining = duration_minutes
        current = self.find_next_work_time(dt, resource_id)
        safety = 0
        while remaining > 1e-9 and safety < 10000:
            safety += 1
            periods = self.get_work_periods(current)
            for start, end in periods:
                if current >= end:
                    continue
                if current < start:
                    current = start
                available = (end - current).total_seconds() / 60
                if available >= remaining:
                    return current + timedelta(minutes=remaining)
                remaining -= available
                current = end
            next_day = datetime(current.year, current.month, current.day) + timedelta(days=1)
            current = self.find_next_work_time(next_day, resource_id)
        return current


def calculate_task_times(front_task: dict, current_process: dict, direction: str = "FORWARD") -> dict:
    front_end = front_task["end_time"]
    process_info = front_task.get("process_info", {})
    relationship = process_info.get("process_relationship", "ES")
    post_interval = parse_duration(process_info.get("post_interval_duration", "0M"))
    buffer_time = parse_duration(process_info.get("buffer_time", "0M"))
    pre_interval = parse_duration(current_process.get("pre_interval_duration", "0M"))

    if relationship == "ES":
        earliest_start = front_end + timedelta(minutes=post_interval + pre_interval)
    elif relationship == "EE":
        front_start = front_task.get("start_time", front_end)
        earliest_start = front_start + timedelta(minutes=buffer_time + pre_interval)
    else:
        earliest_start = front_end + timedelta(minutes=pre_interval)

    return {"earliest_start": earliest_start}
