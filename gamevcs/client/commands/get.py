import click
from rich.console import Console
from gamevcs.client.api import WorkspaceConfig

console = Console()


def get_command(changelist_id: str = None):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    project_id = config["project"]["id"]
    branch_id = config["branch"]["id"]

    target_cl_id = None

    if changelist_id is None or changelist_id == "latest":
        committed = client.list_changelists(
            project_id=project_id, branch_id=branch_id, status="committed"
        )
        if committed:
            target_cl_id = committed[0]["id"]
        else:
            console.print("[yellow]No committed changelists yet[/yellow]")
            return
    elif changelist_id == "head":
        committed = client.list_changelists(
            project_id=project_id, branch_id=branch_id, status="committed"
        )
        if committed:
            target_cl_id = committed[0]["id"]
    else:
        try:
            target_cl_id = int(changelist_id)
        except ValueError:
            try:
                result = client.get_tag_changelist(changelist_id, project_id)
                target_cl_id = result["changelist"]["id"]
            except:
                console.print(f"[red]Invalid changelist or tag: {changelist_id}[/red]")
                return

    if not target_cl_id:
        console.print("[yellow]No target changelist found[/yellow]")
        return

    try:
        target_cl = client.get_changelist(target_cl_id)
        files = client.get_changelist_files(target_cl_id)

        console.print(
            f"[bold]Getting changelist #{target_cl_id}:[/bold] {target_cl.get('message', '')[:50]}"
        )

        if not files:
            console.print("[dim]No files in this changelist[/dim]")
            return

        console.print(f"[green]Retrieved {len(files)} files[/green]")

        config["workspace_changelist"] = target_cl_id
        workspace.save(config)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@click.command(name="get")
@click.argument("changelist", required=False, default="latest")
def get_cmd(changelist):
    get_command(changelist)
