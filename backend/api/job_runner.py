import logging
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from ..progress_handler import CancellationSource, ProgressEvent

logger = logging.getLogger(__name__)


class JobRunner:
    """Manages background tasks for media compression."""

    def __init__(self, max_workers: int = 1) -> None:
        """Initialize JobRunner."""
        self.tasks: dict[str, Any] = {}
        self.tasks_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._cleanup_thread_started = False

    def start_cleanup_thread(self) -> None:
        """Start the background cleanup thread if not already started."""
        if not self._cleanup_thread_started:
            cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            cleanup_thread.start()
            self._cleanup_thread_started = True

    def _cleanup_loop(self) -> None:
        """Background thread to clean up old tasks every 10 minutes."""
        cleanup_interval = 600  # 10 minutes
        retention_period = 3600  # 1 hour
        while True:
            # Check every 10 minutes
            time.sleep(cleanup_interval)
            now = time.time()
            with self.tasks_lock:
                to_delete: list[str] = []
                for tid, t in self.tasks.items():
                    # Remove tasks that finished more than 1 hour ago
                    if t.get("status") in ["success", "failed", "cancelled"]:
                        finished_at = t.get("finished_at")
                        if finished_at and (now - finished_at) > retention_period:
                            to_delete.append(tid)

                for tid in to_delete:
                    del self.tasks[tid]

    def start_task(
        self, task_type: str, compression_func: Callable[..., Any], **kwargs: Any
    ) -> str:
        """Start a new compression task."""
        self.start_cleanup_thread()
        task_id = str(uuid.uuid4())
        cancel_source = CancellationSource()
        input_path = kwargs.get("input_path", "")
        filename = Path(input_path).name if input_path else ""

        max_tasks_limit = 100
        cleanup_batch_size = 20

        with self.tasks_lock:
            # Basic cleanup if too many tasks (safety limit)
            if len(self.tasks) > max_tasks_limit:
                finished_ids = [
                    tid
                    for tid, t in self.tasks.items()
                    if t["status"] in ["success", "failed", "cancelled"]
                ]
                # Remove first few finished tasks
                for fid in finished_ids[:cleanup_batch_size]:
                    del self.tasks[fid]

            self.tasks[task_id] = {
                "id": task_id,
                "status": "pending",
                "progress": None,
                "result": None,
                "cancel_source": cancel_source,
                "type": task_type,
                "filename": filename,
                "created_at": time.time(),
            }

        def run_task() -> None:

            def on_progress(event: ProgressEvent) -> None:
                self._update_task_safe(
                    task_id,
                    {
                        "progress": {
                            "percent": event.percent,
                            "current_time": event.current_time,
                            "total_duration": event.total_duration,
                            "fps": event.fps,
                            "speed": event.speed,
                            "frame": event.frame,
                            "eta": event.eta,
                            "status": event.status,
                        },
                        "status": "running",
                    },
                )

            try:
                logger.info("Task %s (%s) started: %s", task_id[:8], task_type, filename)
                result = compression_func(
                    on_progress=on_progress, cancellation_source=cancel_source, **kwargs
                )

                self._update_task_safe(
                    task_id,
                    {
                        "status": result.status.value,
                        "result": {
                            "is_success": result.is_success,
                            "output_path": result.output_path,
                            "output_size": result.output_size,
                            "compression_ratio": result.compression_ratio,
                            "error_message": result.error_message,
                        },
                        "finished_at": time.time(),
                    },
                )
                logger.info(
                    "Task %s (%s) finished: status=%s",
                    task_id[:8],
                    task_type,
                    result.status.value,
                )
            except Exception as e:
                logger.exception("Task %s (%s) failed: %s", task_id[:8], task_type, e)
                self._update_task_safe(
                    task_id,
                    {
                        "status": "failed",
                        "result": {
                            "is_success": False,
                            "error_message": str(e),
                        },
                        "finished_at": time.time(),
                    },
                )

        self.executor.submit(run_task)

        return task_id

    def _update_task_safe(self, task_id: str, updates: dict[str, Any]) -> None:
        """Update a task's information in a thread-safe manner."""
        with self.tasks_lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(updates)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get a task by its ID."""
        with self.tasks_lock:
            return self.tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        with self.tasks_lock:
            task = self.tasks.get(task_id)
            if task:
                task["cancel_source"].cancel()
                if task["status"] not in ["success", "failed", "cancelled"]:
                    task["status"] = "cancelling"
                return True
        return False

    def list_tasks(self) -> list[dict[str, Any]]:
        """List all tasks."""
        with self.tasks_lock:
            return [
                {
                    "id": t["id"],
                    "status": t["status"],
                    "type": t["type"],
                    "filename": t.get("filename", ""),
                    "progress": t.get("progress"),
                    "result": t.get("result"),
                    "created_at": t.get("created_at"),
                    "finished_at": t.get("finished_at"),
                }
                for t in self.tasks.values()
            ]


# Singleton instance
job_runner = JobRunner()
