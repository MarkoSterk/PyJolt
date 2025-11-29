"""
Task manager
"""
import asyncio
from pyjolt.task_manager import TaskManager, schedule_job

class SchedulerManager(TaskManager):
    """
    Custom TaskManager implementation
    """
    @schedule_job("interval", minutes=1, id="some_task", name="A simple task")
    async def some_task(self):
        self.app.logger.info("Started job...")
        await asyncio.sleep(3)
        self.app.logger.info("Finished job...")

scheduler_manager: SchedulerManager = SchedulerManager()
