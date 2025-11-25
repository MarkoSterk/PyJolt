"""
Schedulers related admin dashboard controller
"""
from ..request import Request
from ..response import Response
from ..controller import get
from .common_controller import CommonAdminController
from .templates.task_managers import TASK_MANAGERS

class AdminTaskManagersController(CommonAdminController):

    @get("/schedulers")
    async def task_managers(self, req: Request) -> Response:
        """List of all schedulers"""

        return await req.res.html_from_string(
            TASK_MANAGERS, {
                "schedulers": None,
                **self.get_common_variables()
            }
        )

