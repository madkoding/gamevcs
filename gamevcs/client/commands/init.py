import click
import getpass
from rich.console import Console
from rich.prompt import Prompt
from gamevcs.client.api import GameVCSClient, WorkspaceConfig

console = Console()


def init_command(
    email: str, host: str, workspace_path: str = None, password: str = None
):
    workspace_path = workspace_path or "."
    workspace = WorkspaceConfig(workspace_path)

    if workspace.exists():
        console.print(
            "[yellow]Workspace already initialized. Re-initializing...[/yellow]"
        )

    if ":" in host:
        server_url = f"http://{host}"
    else:
        server_url = f"http://{host}:9000"

    if not email:
        email = Prompt.ask("Email")

    if not password:
        password = getpass.getpass("Password: ")

    client = GameVCSClient(server_url)

    try:
        console.print("[cyan]Registering user...[/cyan]")
        result = client.register(email, email.split("@")[0], password)
        token = result["access_token"]
        user = result["user"]
    except Exception as e:
        if "already registered" in str(e).lower():
            console.print("[cyan]User exists, logging in...[/cyan]")
            result = client.login(email, password)
            token = result["access_token"]
            user = result["user"]
        else:
            console.print(f"[red]Error: {e}[/red]")
            return

    client = GameVCSClient(server_url, token)

    try:
        projects = client.list_projects()
    except Exception as e:
        console.print(f"[red]Error connecting to server: {e}[/red]")
        return

    if not projects:
        console.print("[cyan]No projects found. Creating default project...[/cyan]")
        project = client.create_project("Default", "Default project")
    else:
        project = projects[0]

    branches = client.list_branches(project["id"])
    if not branches:
        console.print("[yellow]No branches found, creating 'main' branch...[/yellow]")
        branch = client.create_branch(project["id"], "main", "Default branch")
    else:
        branch = branches[0]

    changelists = client.list_changelists(
        project_id=project["id"], branch_id=branch["id"], status="committed"
    )
    if changelists:
        parent_cl = changelists[0]
    else:
        parent_cl = None

    ws_changelist = client.create_changelist(
        project_id=project["id"], branch_id=branch["id"], message="Workspace changelist"
    )

    config = {
        "version": "1.0",
        "project": {"id": project["id"], "name": project["name"]},
        "branch": {"id": branch["id"], "name": branch["name"]},
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
        },
        "server": {"url": server_url, "token": token},
        "workspace_changelist": ws_changelist["id"],
    }

    workspace.save(config)

    console.print(f"[green]Workspace initialized successfully![/green]")
    console.print(f"Project: {project['name']}")
    console.print(f"Branch: {branch['name']}")
    console.print(f"Server: {server_url}")


@click.command(name="init")
@click.option("-email", "-e", help="Email for login")
@click.option("-host", "-h", help="Server host (host:port)")
@click.option("-path", "-p", default=".", help="Workspace path")
@click.option("-password", "-pw", help="Password (will prompt if not provided)")
def init_cmd(email, host, path, password):
    init_command(email, host, path, password)
