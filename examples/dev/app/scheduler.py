"""
Scheduler extension
"""
from pyjolt.task_manager import TaskManager, schedule_job

class Scheduler(TaskManager):

    @schedule_job("interval", minutes=1, id="my_job")
    async def some_task(self):
        print("Performing task")

scheduler: Scheduler = Scheduler()

