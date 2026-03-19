import os
import json
from pathlib import Path
from typing import Optional
import requests


class GameVCSClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            error_msg = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get("detail", error_msg)
            except:
                pass
            raise Exception(f"HTTP {e.response.status_code}: {error_msg}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {str(e)}")

    def register(self, email: str, username: str, password: str):
        return self._request(
            "POST",
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "role": "normal",
            },
        )

    def login(self, email: str, password: str):
        return self._request(
            "POST", "/auth/login", json={"email": email, "password": password}
        )

    def get_me(self):
        return self._request("GET", "/auth/me")

    def list_users(self):
        return self._request("GET", "/users")

    def create_user(
        self, email: str, username: str, password: str, role: str = "normal"
    ):
        return self._request(
            "POST",
            "/users",
            json={
                "email": email,
                "username": username,
                "password": password,
                "role": role,
            },
        )

    def list_projects(self):
        return self._request("GET", "/projects")

    def create_project(self, name: str, description: Optional[str] = None):
        return self._request(
            "POST", "/projects", json={"name": name, "description": description}
        )

    def get_project(self, project_id: int):
        return self._request("GET", f"/projects/{project_id}")

    def list_branches(self, project_id: int):
        return self._request("GET", f"/projects/{project_id}/branches")

    def create_branch(
        self,
        project_id: int,
        name: str,
        description: Optional[str] = None,
        root_cl_id: Optional[int] = None,
    ):
        return self._request(
            "POST",
            f"/projects/{project_id}/branches",
            json={
                "project_id": project_id,
                "name": name,
                "description": description,
                "root_cl_id": root_cl_id,
            },
        )

    def list_changelists(
        self,
        project_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        status: Optional[str] = None,
        is_shelf: Optional[bool] = None,
    ):
        params = {}
        if project_id:
            params["project_id"] = project_id
        if branch_id:
            params["branch_id"] = branch_id
        if status:
            params["status"] = status
        if is_shelf is not None:
            params["is_shelf"] = is_shelf
        return self._request("GET", "/changelists", params=params)

    def create_changelist(
        self,
        project_id: int,
        branch_id: int,
        message: str = "",
        parent_cl_id: Optional[int] = None,
    ):
        return self._request(
            "POST",
            "/changelists",
            json={
                "project_id": project_id,
                "branch_id": branch_id,
                "message": message,
                "parent_cl_id": parent_cl_id,
            },
        )

    def get_changelist(self, changelist_id: int):
        return self._request("GET", f"/changelists/{changelist_id}")

    def update_changelist(self, changelist_id: int, message: str):
        return self._request(
            "PUT", f"/changelists/{changelist_id}", params={"message": message}
        )

    def commit_changelist(
        self, changelist_id: int, message: str, keep_locks: bool = False
    ):
        return self._request(
            "POST",
            f"/changelists/{changelist_id}/commit",
            json={"message": message, "keep_locks": keep_locks},
        )

    def shelve_changelist(self, changelist_id: int, message: str):
        return self._request(
            "POST", f"/changelists/{changelist_id}/shelve", json={"message": message}
        )

    def delete_changelist(self, changelist_id: int):
        return self._request("DELETE", f"/changelists/{changelist_id}")

    def get_changelist_files(self, changelist_id: int):
        return self._request("GET", f"/changelists/{changelist_id}/files")

    def upload_file(
        self, changelist_id: int, path: str, content: bytes, operation: str = "add"
    ):
        files = {"file": (Path(path).name, content)}
        data = {"path": path, "operation": operation}
        return self._request(
            "POST", f"/changelists/{changelist_id}/files", files=files, data=data
        )

    def download_file(self, changelist_id: int, file_id: int):
        return self._request(
            "GET", f"/changelists/{changelist_id}/files/{file_id}/download"
        )

    def list_locks(
        self, file_id: Optional[int] = None, changelist_id: Optional[int] = None
    ):
        params = {}
        if file_id:
            params["file_id"] = file_id
        if changelist_id:
            params["changelist_id"] = changelist_id
        return self._request("GET", "/locks", params=params)

    def request_lock(self, file_id: int):
        return self._request("POST", "/locks", json={"file_id": file_id})

    def release_lock(self, lock_id: int):
        return self._request("DELETE", f"/locks/{lock_id}")

    def list_tags(
        self, project_id: Optional[int] = None, changelist_id: Optional[int] = None
    ):
        params = {}
        if project_id:
            params["project_id"] = project_id
        if changelist_id:
            params["changelist_id"] = changelist_id
        return self._request("GET", "/tags", params=params)

    def create_tag(
        self, project_id: int, name: str, changelist_id: int, allow_move: bool = False
    ):
        return self._request(
            "POST",
            "/tags",
            json={
                "project_id": project_id,
                "name": name,
                "changelist_id": changelist_id,
                "allow_move": allow_move,
            },
        )

    def delete_tag(self, tag_id: int):
        return self._request("DELETE", f"/tags/{tag_id}")

    def get_tag_changelist(self, tag_name: str, project_id: int):
        return self._request(
            "GET", f"/tags/{tag_name}/changelist", params={"project_id": project_id}
        )


class WorkspaceConfig:
    DEFAULT_CONFIG_DIR = ".gamevcs"

    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.config_dir = self.workspace_path / self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / "config.json"

    def exists(self) -> bool:
        return self.config_file.exists()

    def load(self) -> dict:
        if not self.exists():
            raise Exception("Workspace not initialized. Run 'gamevc init' first.")
        with open(self.config_file, "r") as f:
            return json.load(f)

    def save(self, config: dict):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_project_config(self) -> dict:
        config = self.load()
        return config.get("project", {})

    def get_current_user(self) -> dict:
        config = self.load()
        return config.get("user", {})

    def get_server(self) -> str:
        config = self.load()
        return config.get("server", {}).get("url", "")

    def get_token(self) -> str:
        config = self.load()
        return config.get("server", {}).get("token", "")

    def get_client(self) -> GameVCSClient:
        config = self.load()
        server_config = config.get("server", {})
        url = server_config.get("url", "")
        token = server_config.get("token", "")
        return GameVCSClient(url, token)


def find_workspace(start_path: Optional[str] = None) -> Optional[Path]:
    if start_path is None:
        start_path = os.getcwd()

    current = Path(start_path).resolve()
    while True:
        config_file = current / ".gamevcs" / "config.json"
        if config_file.exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def get_workspace() -> WorkspaceConfig:
    workspace_path = find_workspace()
    if workspace_path is None:
        raise Exception("Not in a GameVCS workspace. Run 'gamevcs init' first.")
    return WorkspaceConfig(str(workspace_path))
