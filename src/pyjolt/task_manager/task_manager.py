"""
Task manager class
"""
from typing import Callable, Tuple, Optional, cast, TYPE_CHECKING
from functools import wraps

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from ..utilities import run_sync_or_async, run_in_background
from ..base_extension import BaseExtension

if TYPE_CHECKING:
    from ..pyjolt import PyJolt

class TaskManager(BaseExtension):
    """
    Task manager class for scheduling and managing backgroudn tasks.
    """
    _DEFAULT_CONFIGS = {
        "default_scheduler": AsyncIOScheduler,
        "default_jobstores": {
            'default': MemoryJobStore()
        },
        "default_executors": {
            'default': AsyncIOExecutor(),
        },
        "default_job_defaults": {
            'coalesce': False,
            'max_instances': 3
        },
        "default_daemon": True
    }

    

    def __init__(self, variable_prefix: str = "") -> None:
        self._variable_prefix: str = variable_prefix
        self._app: "Optional[PyJolt]" = None
        self._job_stores: Optional[dict] = self._DEFAULT_CONFIGS["default_jobstores"]
        self._executors: Optional[dict] = self._DEFAULT_CONFIGS["default_executors"]
        self._job_defaults: Optional[dict] = self._DEFAULT_CONFIGS["default_job_defaults"]
        self._daemon: bool = self._DEFAULT_CONFIGS["default_daemon"]
        self._scheduler: Optional[AsyncIOScheduler] = self._DEFAULT_CONFIGS["default_scheduler"]
        self._initial_jobs_methods_list: Optional[list[Tuple]] = []
        self._active_jobs: dict[str, Job] = {}
        self._get_defined_jobs()

    def init_app(self, app: "PyJolt"):
        """
        Initlizer for TaskManager with PyJolt app
        """
        self._app = app
        self._job_stores = self._app.get_conf(f"{self._variable_prefix}TASK_MANAGER_JOB_STORES",
                                              self._DEFAULT_CONFIGS["default_jobstores"])
        self._executors = self._app.get_conf(f"{self._variable_prefix}TASK_MANAGER_EXECUTORS",
                                             self._DEFAULT_CONFIGS["default_executors"])
        self._job_defaults = self._app.get_conf(f"{self._variable_prefix}TASK_MANAGER_JOB_DEFAULTS",
                                                self._DEFAULT_CONFIGS["default_job_defaults"])
        self._daemon = self._app.get_conf(f"{self._variable_prefix}TASK_MANAGER_DAEMON",
                                          self._DEFAULT_CONFIGS["default_daemon"])
        self._scheduler = self._app.get_conf(f"{self._variable_prefix}TASK_MANAGER_SCHEDULER",
                                             self._DEFAULT_CONFIGS["default_scheduler"])
        self._scheduler = self._scheduler(jobstores=self._job_stores,
                                            executors=self._executors,
                                            job_defaults=self._job_defaults,
                                            daemon=self._daemon
                                            )
        self._app.add_extension(self)
        self._app.add_on_startup_method(self._start_scheduler)
        self._app.add_on_shutdown_method(self._stop_scheduler)

    def start_scheduler(self):
        """
        Starts the scheduler
        """
        self._start_scheduler(None)

    def stop_scheduler(self):
        """
        Stop the scheduler
        """
        self._stop_scheduler(None)
        self._active_jobs = None

    def pause_scheduler(self):
        """
        Pauses scheduler execution
        """
        self.scheduler.pause()

    def resume_scheduler(self):
        """
        Resumes paused scheduler execution
        """
        self.scheduler.resume()

    async def _start_scheduler(self):
        """
        On startup hook for starting the scheduler
        """
        self.scheduler.start()
        self._start_initial_jobs()

    async def _stop_scheduler(self):
        """
        On shutdown hook for shuting the scheduler down
        """
        self.scheduler.shutdown()
    
    def _get_defined_jobs(self):
        for name in dir(self):
            method = getattr(self, name)
            if not callable(method):
                continue
            scheduler_method = getattr(method, "_scheduler_job", None)
            if scheduler_method:
                self._initial_jobs_methods_list.append((method,
                                                        scheduler_method["args"],
                                                        scheduler_method["kwargs"]))

    def _start_initial_jobs(self) -> None:
        """
        Starts all initial jobs (decorated functions)
        """
        if self._initial_jobs_methods_list is None:
            return
        for func, args, kwargs in self._initial_jobs_methods_list:
            job: Job = self.scheduler.add_job(func, *args, **kwargs)
            self._active_jobs[job.id] = job
        self._initial_jobs_methods_list = None

    def run_background_task(self, func: Callable, *args, **kwargs):
        """
        Runs a method in the background (fire and forget).
        Used for running function whose execution doesn't have to be awaited.
        Example: a route handler can return a response immediately, and the
        task is executed in a seperate thread (sending an email for example).

        Uses the pyjolt.utilities.run_in_background method
        """
        run_in_background(func, *args, **kwargs)

    def add_job(self, func: Callable, *args, **kwargs) -> Job:
        """
        Adds job
        """
        job: Job = self.scheduler.add_job(func, *args, **kwargs)
        self._active_jobs[job.id] = job
        return job

    def remove_job(self, job: str|Job, job_store: Optional[str] = None):
        """
        Removes a job.
        :param job: job id (str) or the Job instance returned by the scheduler.add_job method
        """
        if isinstance(job, Job):
            job = job.id
        return self._remove_job(job, job_store)

    def pause_job(self, job: str|Job):
        """
        Pauses the job
        """
        if isinstance(job, Job):
            return job.pause()
        active_job: Job = self._active_jobs.get(job, None)
        if job is None:
            raise JobLookupError(job)
        return active_job.pause()

    def resume_job(self, job: str|Job):
        """
        Resumes job
        :param paused_job: id or Job instance
        """
        if isinstance(job, Job):
            return job.resume()
        paused_job: Job = self._active_jobs.get(job, None)
        if paused_job is None:
            raise JobLookupError(paused_job)
        return paused_job.resume()
    
    def get_job(self, job_id: str) -> Job|None:
        return self._active_jobs.get(job_id, None)

    def _remove_job(self, job_id: str, job_store = None):
        """
        Removes job from job list
        """
        self.scheduler.remove_job(job_id, job_store)
        del self._active_jobs[job_id]

    @property
    def jobs(self) -> dict[str, Job]:
        """
        Returns list of running jobs
        """
        return self._active_jobs

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """
        Returns the background scheduler instance
        """
        return self._scheduler
    
    @property
    def app(self) -> "PyJolt":
        """
        Application instance
        """
        return cast("PyJolt", self._app)


def schedule_job(*args, **kwargs):
    """
    ```
    A decorator to add a function as a scheduled job in the given APScheduler instance.
    The decorated function is added to a list of tuples (func, args, kwargs) and the job
    is started when the scheduler instance is started (on_startup event of PyJolt)
    IMPORTANT: The decorator should be the top-most decorator of the function to make sure
    any other decorator is applied before the job is added to the job list
    :param args: Positional arguments to pass to scheduler.add_job().
                Typically, the first of these args is the trigger (e.g. 'interval', 'cron', etc.).
    :param kwargs: Keyword arguments to pass to scheduler.add_job().
    Example:
    Runs a job with id 'my_job_id' every 5 minutes

    @schedule_job('interval', minutes=5, id='my_job_id')
    async def my_job(self):
        #some task
    ```
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *f_args, **f_kwargs):
            return await run_sync_or_async(func, self, *f_args, **f_kwargs)
        setattr(wrapper, "_scheduler_job", {"args": args, "kwargs": kwargs})
        return wrapper
    return decorator
