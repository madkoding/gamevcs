import click
from rich.console import Console
from rich.table import Table
from gamevcs.client.api import WorkspaceConfig

console = Console()


def branch_list_command():
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]

    try:
        branches = client.list_branches(project_id)

        table = Table(show_header=True)
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Description")

        for branch in branches:
            table.add_row(
                str(branch["id"]), branch["name"], branch.get("description", "") or ""
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def branch_add_command(name: str, description: str = None):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]

    try:
        branch = client.create_branch(project_id, name, description)
        console.print(
            f"[green]Created branch '{branch['name']}' (ID: {branch['id']})[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def branch_switch_command(branch_name: str):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]

    try:
        branches = client.list_branches(project_id)
        branch = next((b for b in branches if b["name"] == branch_name), None)

        if not branch:
            console.print(f"[red]Branch '{branch_name}' not found[/red]")
            return

        changelists = client.list_changelists(
            project_id=project_id, branch_id=branch["id"], status="committed"
        )

        if changelists:
            parent_cl = changelists[0]["id"]
        else:
            parent_cl = None

        new_cl = client.create_changelist(
            project_id=project_id,
            branch_id=branch["id"],
            message="Workspace changelist",
            parent_cl_id=parent_cl,
        )

        config["branch"] = {"id": branch["id"], "name": branch["name"]}
        config["workspace_changelist"] = new_cl["id"]
        workspace.save(config)

        console.print(f"[green]Switched to branch '{branch['name']}'[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def branch_merge_command(branch_name: str):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]
    current_branch_id = config["branch"]["id"]

    try:
        branches = client.list_branches(project_id)
        source_branch = next((b for b in branches if b["name"] == branch_name), None)

        if not source_branch:
            console.print(f"[red]Branch '{branch_name}' not found[/red]")
            return

        result = client._request(
            "POST",
            f"/branches/{current_branch_id}/merge",
            json={"source_branch_id": source_branch["id"], "target_cl_id": None},
        )

        console.print(
            f"[green]Merged branch '{branch_name}' into current branch[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@click.command(name="branch")
@click.argument("action", type=click.Choice(["list", "add", "switch", "merge"]))
@click.argument("name", required=False)
@click.option("-desc", "--description", help="Branch description")
def branch_cmd(action, name, description):
    if action == "list":
        branch_list_command()
    elif action == "add":
        if not name:
            console.print("[red]Branch name required[/red]")
            return
        branch_add_command(name, description)
    elif action == "switch":
        if not name:
            console.print("[red]Branch name required[/red]")
            return
        branch_switch_command(name)
    elif action == "merge":
        if not name:
            console.print("[red]Branch name required[/red]")
            return
        branch_merge_command(name)
