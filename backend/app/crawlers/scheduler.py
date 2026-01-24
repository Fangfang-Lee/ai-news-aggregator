from typing import Callable, Optional, Dict, Any
import schedule
import time
import threading
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Simple task scheduler for periodic tasks"""

    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.tasks: Dict[str, Any] = {}

    def add_task(self, name: str, func: Callable, interval_minutes: int = 60):
        """
        Add a scheduled task

        Args:
            name: Task name
            func: Function to execute
            interval_minutes: Interval in minutes
        """
        self.tasks[name] = {
            'func': func,
            'interval': interval_minutes,
            'schedule': schedule.every(interval_minutes).minutes
        }
        logger.info(f"Added scheduled task: {name} every {interval_minutes} minutes")

    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        schedule.clear()
        logger.info("Scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("Scheduler loop started")

        # Schedule all tasks
        for name, task in self.tasks.items():
            task['schedule'].do(task['func']).tag(name)

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def run_task_now(self, name: str):
        """
        Run a specific task immediately

        Args:
            name: Task name
        """
        if name in self.tasks:
            logger.info(f"Running task {name} immediately")
            try:
                self.tasks[name]['func']()
            except Exception as e:
                logger.error(f"Error running task {name}: {e}")
        else:
            logger.warning(f"Task {name} not found")