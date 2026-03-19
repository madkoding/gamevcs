import click
from rich.console import Console
from rich.table import Table
from gamevcs.client.api import WorkspaceConfig

console = Console()


def lock_command(path: str):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    ws_cl_id = config["workspace_changelist"]

    try:
        files = client.get_changelist_files(ws_cl_id)
        file = next((f for f in files if f["path"] == path), None)

        if not file:
            console.print(
                f"[yellow]File '{path}' not in workspace changelist. Adding it first...[/yellow]"
            )
            return

        lock = client.request_lock(file["id"])

        if lock["status"] == "active":
            console.print(f"[green]Lock acquired on {path}[/green]")
        else:
            console.print(
                f"[yellow]Added to lock queue (position {lock['queue_position']}) for {path}[/yellow]"
            )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def unlock_command(path: str):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    ws_cl_id = config["workspace_changelist"]

    try:
        files = client.get_changelist_files(ws_cl_id)
        file = next((f for f in files if f["path"] == path), None)

        if not file:
            console.print(f"[red]File '{path}' not in workspace[/red]")
            return

        if not file.get("lock"):
            console.print(f"[yellow]File '{path}' is not locked[/yellow]")
            return

        locks = client.list_locks(file_id=file["id"])
        active_lock = next((l for l in locks if l["status"] == "active"), None)

        if active_lock:
            client.release_lock(active_lock["id"])
            console.print(f"[green]Released lock on {path}[/green]")
        else:
            console.print(f"[yellow]No active lock on {path}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def locks_list_command():
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    ws_cl_id = config["workspace_changelist"]

    try:
        files = client.get_changelist_files(ws_cl_id)

        table = Table(show_header=True)
        table.add_column("Path")
        table.add_column("Lock Status")
        table.add_column("User")

        for f in files:
            if f.get("lock"):
                status = f"Locked by {f['lock']['username']}"
            else:
                status = "Unlocked"

            table.add_row(
                f["path"],
                status,
                f["lock"].get("username", "-") if f.get("lock") else "-",
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@click.command(name="lock")
@click.argument("path")
def lock_cmd(path):
    lock_command(path)


@click.command(name="unlock")
@click.argument("path")
def unlock_cmd(path):
    unlock_command(path)


@click.command(name="locks")
def locks_cmd():
    locks_list_command()
