from datetime import datetime
from typing import Dict


class ProgressTracker:
    _progress_data: Dict[str, dict] = {}

    @classmethod
    def create(cls, task_id: str):
        cls._progress_data[task_id] = {
            "status": "RUNNING",
            "progress": 0,
            "step": "",
            "steps_total": 5,
            "start_time": datetime.now().isoformat(),
            "last_heartbeat": datetime.now().isoformat(),
            "logs": [],
        }

    @classmethod
    def update(cls, task_id: str, progress: float = None, step: str = None, log: str = None):
        if task_id not in cls._progress_data:
            return
        data = cls._progress_data[task_id]
        if progress is not None:
            data["progress"] = progress
        if step is not None:
            data["step"] = step
        data["last_heartbeat"] = datetime.now().isoformat()
        if log is not None:
            data["logs"].append(log)

    @classmethod
    def complete(cls, task_id: str):
        if task_id not in cls._progress_data:
            return
        cls._progress_data[task_id]["status"] = "SUCCESS"
        cls._progress_data[task_id]["progress"] = 100
        cls._progress_data[task_id]["last_heartbeat"] = datetime.now().isoformat()

    @classmethod
    def fail(cls, task_id: str, error: str):
        if task_id not in cls._progress_data:
            return
        cls._progress_data[task_id]["status"] = "FAILED"
        cls._progress_data[task_id]["last_heartbeat"] = datetime.now().isoformat()
        cls._progress_data[task_id]["logs"].append(f"ERROR: {error}")

    @classmethod
    def get(cls, task_id: str) -> dict:
        return cls._progress_data.get(task_id, {"status": "NOT_FOUND"})

    @classmethod
    def check_timeout(cls, timeout_seconds: int = 120):
        now = datetime.now()
        timed_out = []
        for task_id, data in cls._progress_data.items():
            if data["status"] != "RUNNING":
                continue
            last_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
            if (now - last_heartbeat).total_seconds() > timeout_seconds:
                timed_out.append(task_id)
        for task_id in timed_out:
            cls.fail(task_id, "任务超时")
