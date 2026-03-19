import click
from rich.console import Console
from rich.table import Table
from gamevcs.client.api import WorkspaceConfig

console = Console()


def tag_list_command():
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]

    try:
        tags = client.list_tags(project_id=project_id)

        table = Table(show_header=True)
        table.add_column("Name")
        table.add_column("Changelist ID", justify="right")

        for tag in tags:
            table.add_row(tag["name"], str(tag["changelist_id"]))

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def tag_add_command(name: str, changelist_id: int = None, allow_move: bool = False):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]

    if not changelist_id:
        committed = client.list_changelists(
            project_id=project_id, branch_id=config["branch"]["id"], status="committed"
        )
        if committed:
            changelist_id = committed[0]["id"]
        else:
            console.print("[red]No committed changelists found[/red]")
            return

    try:
        tag = client.create_tag(project_id, name, changelist_id, allow_move)
        console.print(
            f"[green]Created tag '{tag['name']}' at changelist #{changelist_id}[/green]"
        )
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def tag_remove_command(name: str):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]

    try:
        tags = client.list_tags(project_id=project_id)
        tag = next((t for t in tags if t["name"] == name), None)

        if not tag:
            console.print(f"[red]Tag '{name}' not found[/red]")
            return

        client.delete_tag(tag["id"])
        console.print(f"[green]Deleted tag '{name}'[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@click.command(name="tag")
@click.argument("action", type=click.Choice(["list", "add", "remove"]))
@click.argument("name", required=False)
@click.option("-cl", "--changelist", type=int, help="Changelist ID")
@click.option("--allow-move", is_flag=True, help="Allow moving existing tag")
def tag_cmd(action, name, changelist, allow_move):
    if action == "list":
        tag_list_command()
    elif action == "add":
        if not name:
            console.print("[red]Tag name required[/red]")
            return
        tag_add_command(name, changelist, allow_move)
    elif action == "remove":
        if not name:
            console.print("[red]Tag name required[/red]")
            return
        tag_remove_command(name)
