"""
File controller for pyjolt admin dashboard
"""
import os
from typing import Any, Optional
import mimetypes
from pathlib import Path
import shutil
from ..http_statuses import HttpStatus
from ..controller import get, post, delete
from .common_controller import CommonAdminController
from ..auth import login_required
from ..request import Request
from ..response import Response
from ..utilities import get_file

class AdminFileController(CommonAdminController):

    @get("/files")
    @login_required
    async def file_explorer(self, req: Request) -> Response:
        """
        File explorer page
        """
        return await req.res.html("/__admin_templates/file_explorer.html", {
            "folder": self.app.get_conf("STATIC_DIR"),
            "files_and_folders": await self.get_files_and_folder(None),
            **self.get_common_variables()
        })
    
    @get("/files/fetch")
    @login_required
    async def get_all(self, req: Request) -> Response:
        """
        Returns all files
        """
        folder_path: Optional[str] = req.query_params.get("path", None)
        return req.res.json({
            "message": "Files fetched successfully",
            "status": "success",
            "data": await self.get_files_and_folder(folder_path)
        }).status(HttpStatus.OK)
    
    @get("/files/fetch/one")
    @login_required
    async def get_file(self, req: Request) -> Response:
        """
        Returns selected file
        """
        file_path: Optional[str] = req.query_params.get("path", None)
        if file_path is None:
            return req.res.json({
                "message": "Please provide a valid file path",
                "status": "warning"
            }).status(HttpStatus.BAD_REQUEST)
        full_path = os.path.join(self.app.root_path, file_path.lstrip("/\\"))
        if not os.path.isfile(full_path):
            return req.res.json({
                "message": "File does not exist",
                "status": "danger"
            }).status(HttpStatus.BAD_REQUEST)
        guessed, _ = mimetypes.guess_type(full_path)
        content_type = guessed or "application/octet-stream"
        status, headers, body = await get_file(full_path, content_type=content_type)
        headers["Accept-Ranges"] = "bytes"
        return req.res.send_file(body, headers).status(status)
    
    @get("/files/rename")
    @login_required
    async def rename(self, req: Request) -> Response:
        """
        Renames file or folder
        """
        data: dict[str, str] = {}
        for param in ["path", "oldName", "newName"]:
            param_data: Optional[str] = req.query_params.get(param, None)
            if param_data is None:
                return req.res.json({
                    "message": f"Missing parameter '{param}'",
                    "status": "warning"
                }).status(HttpStatus.BAD_REQUEST)
            data[param] = param_data
        
        data["path"] = os.path.join(self.app.root_path, data["path"].lstrip("/\\"))
        old_path = os.path.join(data["path"], data["oldName"])
        new_path = os.path.join(data["path"], data["newName"])
        print(data["path"], old_path, new_path)
        try:
            os.rename(old_path, new_path)
        except Exception:
            return req.res.json({
                "message": f"Failed to change file name {data['oldName']}",
                "status": "danger"
            }).status(HttpStatus.BAD_REQUEST)

        return req.res.json({
            "message": "File or folder renamed successfully",
            "status": "success",
            "data": {
                "old_path": old_path,
                "new_path": new_path,
                "new_name": data["newName"],
                "old_name": data["oldName"]
            }
        }).status(HttpStatus.OK)
    
    @post("/files/upload")
    @login_required
    async def upload(self, req: Request) -> Response:
        """
        Uploads single file
        """
        data: dict[str, Any] = await req.form_and_files()
        full_path = os.path.join(self.app.root_path, data["path"].lstrip("/\\"))
        file_path = Path(full_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data["file"].read())
        return req.res.json({
            "message": "File uploaded successfully",
            "status": "success",
            "data": {
                "path": data["path"],
                "name": data["file"].filename,
                "is_folder": False
            }
        }).status(HttpStatus.CREATED)
    
    @delete("/files")
    @login_required
    async def delete(self, req: Request) -> Response:
        """
        Delete a file or folder
        """
        path: Optional[str] = req.query_params.get("path", None)
        full_path = os.path.join(self.app.root_path, path.lstrip("/\\") if path is not None else "")
        if path is None or (not os.path.isfile(full_path) and not os.path.isdir(full_path)):
            return req.res.json({
                "message": "Please provide a valid file or folder path",
                "status": "danger"
            }).status(HttpStatus.BAD_REQUEST)

        
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)

        return req.res.no_content()

    async def get_files_and_folder(self, path: Optional[str]) -> list[dict[str, str|bool]]:
        """Returns all files and folders at the provided path"""
        if path is None:
            path = self.app.static_files_path
        else:
            if path.startswith("/static"):
                path = path.replace("/static", "")
            elif path.startswith("static"):
                path = path.replace("static", "")
            path = os.path.join(self.app.static_files_path, *path.split("/"))
        items = os.listdir(path)
        files_and_folders = []
        for name in items:
            full = os.path.join(path, name)
            files_and_folders.append({
                "path": path.replace(self.app.root_path, ""),
                "name": name,
                "is_folder": True if os.path.isdir(full) else False
            })
        
        return files_and_folders
