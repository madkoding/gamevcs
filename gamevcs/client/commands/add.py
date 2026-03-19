import click
import os
import xxhash
from pathlib import Path
from rich.console import Console
from gamevcs.client.api import WorkspaceConfig

console = Console()


def add_command(paths: list[str]):
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return

    client = workspace.get_client()
    ws_cl_id = config["workspace_changelist"]

    if not paths:
        console.print("[red]No files specified[/red]")
        return

    project_config = config["project"]
    branch_config = config["branch"]

    try:
        existing_files = {f["path"]: f for f in client.get_changelist_files(ws_cl_id)}
    except:
        existing_files = {}

    for path_str in paths:
        path = Path(path_str).resolve()

        if not path.exists():
            console.print(
                f"[yellow]Warning: {path_str} does not exist, skipping[/yellow]"
            )
            continue

        if path.is_dir():
            continue

        relative_path = path.name

        with open(path, "rb") as f:
            content = f.read()

        file_hash = xxhash.xxh64(content).hexdigest()
        size = len(content)

        existing = existing_files.get(relative_path)

        if existing:
            if existing["hash"] == file_hash:
                console.print(f"[dim]Unchanged: {relative_path}[/dim]")
                continue
            operation = "modify"
        else:
            operation = "add"

        try:
            result = client.upload_file(ws_cl_id, relative_path, content, operation)
            console.print(f"[green]{operation.title()}: {relative_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error uploading {relative_path}: {e}[/red]")


@click.command(name="add")
@click.argument("paths", nargs=-1, required=False)
def add_cmd(paths):
    add_command(list(paths))
