import click
import os
import xxhash
from pathlib import Path
from rich.console import Console
from rich.table import Table
from gamevcs.client.api import WorkspaceConfig

console = Console()


def status_command():
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project = config["project"]
    branch = config["branch"]
    ws_cl_id = config["workspace_changelist"]

    console.print(f"[bold]Project:[/bold] {project['name']}")
    console.print(f"[bold]Branch:[/bold] {branch['name']}")
    console.print(f"[bold]Workspace Changelist:[/bold] #{ws_cl_id}")
    console.print()

    try:
        committed_cls = client.list_changelists(
            project_id=project["id"], branch_id=branch["id"], status="committed"
        )
        if committed_cls:
            latest_cl = committed_cls[0]
            console.print(
                f"[bold]Latest Committed:[/bold] #{latest_cl['id']} - {latest_cl['message'][:50]}"
            )
        else:
            console.print("[bold]Latest Committed:[/bold] (none)")
    except Exception as e:
        console.print(f"[yellow]Could not fetch latest: {e}[/yellow]")

    console.print()
    console.print("[bold]Workspace Changes:[/bold]")

    ws_files = client.get_changelist_files(ws_cl_id)

    if not ws_files:
        console.print("[dim]No pending changes[/dim]")
    else:
        table = Table(show_header=True)
        table.add_column("Status", style="cyan")
        table.add_column("Path", style="white")
        table.add_column("Size", justify="right")

        for f in ws_files:
            status_icon = {
                "add": "[green]+[/green]",
                "modify": "[yellow]M[/yellow]",
                "delete": "[red]D[/red]",
            }.get(f["operation"], "?")

            size_str = f"{f['size']:,} bytes"
            if f["lock"]:
                status_icon += f" [🔒]({f['lock'].get('username', 'user')})"

            table.add_row(status_icon, f["path"], size_str)

        console.print(table)

    try:
        shelved = client.list_changelists(project_id=project["id"], is_shelf=True)
        if shelved:
            console.print()
            console.print("[bold]Shelved Changes:[/bold]")
            for shelf in shelved[:5]:
                console.print(f"  #{shelf['id']} - {shelf['message'][:40]}")
    except:
        pass


@click.command(name="status")
@click.option("-ws_cl", is_flag=True, help="Show workspace changelist ID only")
def status_cmd(ws_cl):
    status_command()
