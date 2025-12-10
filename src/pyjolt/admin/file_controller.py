"""
File controller for pyjolt admin dashboard
"""
import os
from typing import Optional
from ..controller import get
from .common_controller import CommonAdminController
from ..auth import login_required
from ..request import Request
from ..response import Response

class AdminFileController(CommonAdminController):

    @get("/files")
    @login_required
    async def all_files(self, req: Request) -> Response:
        """
        Gets all files in folder
        """
        folder: Optional[str] = req.query_params.get("folder", None)
        return await req.res.html("/__admin_templates/file_explorer.html", {
            "folder": folder if folder is not None else self.app.get_conf("STATIC_DIR"),
            "files_and_folders": await self.get_files_and_folder(folder),
            **self.get_common_variables()
        })
    

    async def get_files_and_folder(self, path: Optional[str]) -> list[dict[str, str|bool]]:
        """Returns all files and folders at the provided path"""
        if path is None:
            path = self.app.static_files_path
        items = os.listdir(path)
        files_and_folders = []
        for name in items:
            full = os.path.join(path, name)
            files_and_folders.append({
                "path": full,
                "name": name,
                "is_folder": True if os.path.isdir(full) else False
            })
        
        return files_and_folders




