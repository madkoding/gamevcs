import click
from rich.console import Console
from gamevcs.client.api import WorkspaceConfig

console = Console()


def shelve_command(message: str):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    ws_cl_id = config["workspace_changelist"]

    if not message:
        message = "Shelved changes"

    try:
        ws_files = client.get_changelist_files(ws_cl_id)
        if not ws_files:
            console.print("[yellow]No changes to shelve[/yellow]")
            return

        result = client.shelve_changelist(ws_cl_id, message)
        console.print(f"[green]Shelved as changelist #{result['id']}[/green]")

        new_cl = client.create_changelist(
            project_id=config["project"]["id"],
            branch_id=config["branch"]["id"],
            message="Workspace changelist",
        )

        config["workspace_changelist"] = new_cl["id"]
        workspace.save(config)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def unshelve_command(shelf_id: int):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()

    try:
        shelf_cl = client.get_changelist(shelf_id)

        if not shelf_cl.get("is_shelf"):
            console.print(f"[red]Changelist #{shelf_id} is not a shelf[/red]")
            return

        ws_cl_id = config["workspace_changelist"]
        shelf_files = client.get_changelist_files(shelf_id)

        for shelf_file in shelf_files:
            path = shelf_file["path"]
            file_info = client.download_file(shelf_id, shelf_file["id"])
            console.print(f"[green]Unshelved: {path}[/green]")

        console.print(
            f"[green]Unshelved {len(shelf_files)} files from shelf #{shelf_id}[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@click.command(name="shelve")
@click.option("-m", "--message", required=True, help="Shelf message")
def shelve_cmd(message):
    shelve_command(message)


@click.command(name="unshelve")
@click.argument("shelf_id", type=int)
def unshelve_cmd(shelf_id):
    unshelve_command(shelf_id)
