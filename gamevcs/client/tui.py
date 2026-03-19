from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.style import Style
from rich import box
from gamevcs.client.api import WorkspaceConfig

console = Console()


def render_status(workspace: WorkspaceConfig, client) -> Panel:
    config = workspace.load()
    project = config["project"]
    branch = config["branch"]
    ws_cl_id = config["workspace_changelist"]

    try:
        committed = client.list_changelists(
            project_id=project["id"], branch_id=branch["id"], status="committed"
        )
        latest = committed[0] if committed else None
    except:
        latest = None

    content = f"[bold]Project:[/bold] {project['name']}\n"
    content += f"[bold]Branch:[/bold] {branch['name']}\n"
    content += f"[bold]Workspace CL:[/bold] #{ws_cl_id}\n"
    if latest:
        content += f"[bold]Latest:[/bold] #{latest['id']} - {latest['message'][:30]}..."

    return Panel(
        content, title="[cyan]Status[/cyan]", border_style="cyan", box=box.ROUNDED
    )


def render_workspace_changes(workspace: WorkspaceConfig, client) -> Panel:
    config = workspace.load()
    ws_cl_id = config["workspace_changelist"]

    try:
        files = client.get_changelist_files(ws_cl_id)
    except:
        files = []

    if not files:
        content = "[dim]No pending changes[/dim]"
    else:
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Status", width=8, style="bold")
        table.add_column("Path")
        table.add_column("Size", justify="right")

        for f in files:
            status = {"add": "+", "modify": "M", "delete": "D"}.get(f["operation"], "?")
            color = {"add": "green", "modify": "yellow", "delete": "red"}.get(
                f["operation"], "white"
            )
            status_text = Text(status, style=color)
            table.add_row(status_text, f["path"], f"{f['size']:,}")

        return Panel(
            table,
            title="[yellow]Workspace Changes[/yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        )

    return Panel(
        content,
        title="[yellow]Workspace Changes[/yellow]",
        border_style="yellow",
        box=box.ROUNDED,
    )


def render_history(workspace: WorkspaceConfig, client) -> Panel:
    config = workspace.load()
    project = config["project"]
    branch = config["branch"]

    try:
        changelists = client.list_changelists(
            project_id=project["id"], branch_id=branch["id"], status="committed"
        )[:10]
    except:
        changelists = []

    if not changelists:
        content = "[dim]No committed changelists[/dim]"
    else:
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("ID", width=6, justify="right")
        table.add_column("Message")

        for cl in changelists:
            table.add_row(f"#{cl['id']}", cl["message"][:40] if cl["message"] else "")

        return Panel(
            table, title="[green]History[/green]", border_style="green", box=box.ROUNDED
        )

    return Panel(
        content, title="[green]History[/green]", border_style="green", box=box.ROUNDED
    )


def render_branches(workspace: WorkspaceConfig, client) -> Panel:
    config = workspace.load()
    project = config["project"]
    current_branch = config["branch"]["name"]

    try:
        branches = client.list_branches(project["id"])
    except:
        branches = []

    if not branches:
        content = "[dim]No branches[/dim]"
    else:
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Name")
        table.add_column("Current", width=8)

        for b in branches:
            marker = "←" if b["name"] == current_branch else ""
            table.add_row(b["name"], marker)

        return Panel(
            table, title="[blue]Branches[/blue]", border_style="blue", box=box.ROUNDED
        )

    return Panel(
        content, title="[blue]Branches[/blue]", border_style="blue", box=box.ROUNDED
    )


def render_tags(workspace: WorkspaceConfig, client) -> Panel:
    config = workspace.load()
    project = config["project"]

    try:
        tags = client.list_tags(project_id=project["id"])
    except:
        tags = []

    if not tags:
        content = "[dim]No tags[/dim]"
    else:
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Name")
        table.add_column("Changelist", justify="right")

        for t in tags:
            table.add_row(t["name"], f"#{t['changelist_id']}")

        return Panel(
            table,
            title="[magenta]Tags[/magenta]",
            border_style="magenta",
            box=box.ROUNDED,
        )

    return Panel(
        content,
        title="[magenta]Tags[/magenta]",
        border_style="magenta",
        box=box.ROUNDED,
    )


def render_main_menu() -> Panel:
    table = Table(box=None, show_header=False)
    table.add_column("Key", width=6, style="bold")
    table.add_column("Action")

    table.add_row("s", "Status")
    table.add_row("a", "Add files")
    table.add_row("c", "Commit")
    table.add_row("h", "History")
    table.add_row("b", "Branches")
    table.add_row("t", "Tags")
    table.add_row("l", "Locks")
    table.add_row("g", "Get latest")
    table.add_row("q", "Quit")

    return Panel(
        table, title="[white]Commands[/white]", border_style="white", box=box.ROUNDED
    )


def run_tui():
    try:
        workspace = WorkspaceConfig(".")
        config = workspace.load()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print(
            "[yellow]Run 'gamevcs init' first to initialize a workspace[/yellow]"
        )
        return

    client = workspace.get_client()

    while True:
        console.clear()

        console.print(
            Panel.fit(
                "[bold cyan]GameVCS - Version Control for Game Development[/bold cyan]",
                border_style="cyan",
                box=box.DOUBLE,
            )
        )
        console.print()

        try:
            console.print(render_status(workspace, client))
            console.print()

            console.print(render_workspace_changes(workspace, client))
            console.print()
            console.print(render_history(workspace, client), justify="left")

            console.print()
            console.print(render_branches(workspace, client), justify="left")
            console.print(render_tags(workspace, client), justify="left")

            console.print()
            console.print(render_main_menu())

            choice = Prompt.ask(
                "[bold]Choose action[/bold] (s/a/c/h/b/t/l/g/q)",
                default="q",
                show_default=False,
            ).lower()

            if choice == "q":
                break
            elif choice == "s":
                from gamevcs.client.commands.status import status_command

                status_command()
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
            elif choice == "a":
                files = Prompt.ask("[bold]Files to add[/bold] (space separated)")
                if files:
                    from gamevcs.client.commands.add import add_command

                    add_command(files.split())
            elif choice == "c":
                msg = Prompt.ask("[bold]Commit message[/bold]")
                if msg:
                    from gamevcs.client.commands.commit import commit_command

                    commit_command(msg)
            elif choice == "h":
                from gamevcs.client.commands.status import status_command

                status_command()
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
            elif choice == "b":
                name = Prompt.ask(
                    "[bold]Branch name to switch[/bold] (leave empty to list)"
                )
                if name:
                    from gamevcs.client.commands.branches import branch_switch_command

                    branch_switch_command(name)
                else:
                    from gamevcs.client.commands.branches import branch_list_command

                    branch_list_command()
                    console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()
            elif choice == "t":
                from gamevcs.client.commands.tags import tag_list_command

                tag_list_command()
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
            elif choice == "l":
                from gamevcs.client.commands.locks import locks_list_command

                locks_list_command()
                console.print("\n[dim]Press Enter to continue...[/dim]")
                input()
            elif choice == "g":
                from gamevcs.client.commands.get import get_command

                get_command("latest")
            else:
                pass

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback

            traceback.print_exc()
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

    console.print("[cyan]Goodbye![/cyan]")


if __name__ == "__main__":
    run_tui()
