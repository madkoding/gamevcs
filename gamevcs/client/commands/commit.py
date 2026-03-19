import click
from rich.console import Console
from gamevcs.client.api import WorkspaceConfig

console = Console()


def commit_command(message: str, keep_locks: bool = False):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    ws_cl_id = config["workspace_changelist"]

    if not message:
        console.print("[red]Commit message is required[/red]")
        return

    try:
        ws_files = client.get_changelist_files(ws_cl_id)
        if not ws_files:
            console.print("[yellow]No changes to commit[/yellow]")
            return

        result = client.commit_changelist(ws_cl_id, message, keep_locks)
        console.print(f"[green]Committed as changelist #{result['id']}[/green]")

        new_cl = client.create_changelist(
            project_id=config["project"]["id"],
            branch_id=config["branch"]["id"],
            message="Workspace changelist",
        )

        config["workspace_changelist"] = new_cl["id"]
        workspace.save(config)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@click.command(name="commit")
@click.option("-m", "--message", required=True, help="Commit message")
@click.option("--keep-locks", is_flag=True, help="Keep locks after commit")
def commit_cmd(message, keep_locks):
    commit_command(message, keep_locks)
