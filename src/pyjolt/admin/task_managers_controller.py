"""
Schedulers related admin dashboard controller
"""
from ..request import Request
from ..response import Response
from ..http_statuses import HttpStatus
from ..controller import get
from .common_controller import CommonAdminController

class AdminTaskManagersController(CommonAdminController):

    @get("/task-managers")
    async def task_managers(self, req: Request) -> Response:
        """List of all schedulers"""
        return await req.res.html(
            "/__admin_templates/task_managers.html", {
                "task_managers": self.dashboard.get_task_managers(),
                **self.get_common_variables()
            }
        )
    
    @get("/task-managers/<string:manager_name>")
    async def task_manager(self, req: Request, manager_name: str) -> Response:
        """Selected task manager"""
        return await req.res.html(
            "/__admin_templates/task_manager.html", {
                "task_managers": self.dashboard.get_task_managers(),
                "manager_name": manager_name,
                **self.get_common_variables()
            }
        )

    #API calls for task management
    @get("/task-managers/<string:manager_name>/run/<string:task_id>")
    async def run_task(self, req: Request, manager_name: str, task_id: str) -> Response:
        """Runs task with provided ID"""
        return req.res.json({
            "message": "Task started",
            "status": "success"
        }).status(HttpStatus.OK)

    @get("/task-managers/<string:manager_name>/pause/<string:task_id>")
    async def pause_task(self, req: Request, manager_name: str, task_id: str) -> Response:
        """Pauses task with provided ID"""
        return req.res.json({
            "message": "Task paused",
            "status": "success"
        }).status(HttpStatus.OK)
    
    @get("/task-managers/<string:manager_name>/resume/<string:task_id>")
    async def resume_task(self, req: Request, manager_name: str, task_id: str) -> Response:
        """Resumes task with provided ID"""
        return req.res.json({
            "message": "Task resumed",
            "status": "success"
        }).status(HttpStatus.OK)
    
    @get("/task-managers/<string:manager_name>/remove/<string:task_id>")
    async def remove_task(self, req: Request, manager_name: str, task_id: str) -> Response:
        """removes task with provided ID"""
        return req.res.json({
            "message": "Task removed",
            "status": "success"
        }).status(HttpStatus.OK)
