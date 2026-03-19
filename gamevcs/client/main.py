import click
from gamevcs.client.commands.init import init_cmd
from gamevcs.client.commands.status import status_cmd
from gamevcs.client.commands.add import add_cmd
from gamevcs.client.commands.commit import commit_cmd
from gamevcs.client.commands.shelve import shelve_cmd, unshelve_cmd
from gamevcs.client.commands.branches import branch_cmd
from gamevcs.client.commands.tags import tag_cmd
from gamevcs.client.commands.locks import lock_cmd, unlock_cmd, locks_cmd
from gamevcs.client.commands.get import get_cmd


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GameVCS - Version Control for Game Development"""
    pass


cli.add_command(init_cmd)
cli.add_command(status_cmd)
cli.add_command(add_cmd)
cli.add_command(commit_cmd)
cli.add_command(shelve_cmd)
cli.add_command(unshelve_cmd)
cli.add_command(branch_cmd)
cli.add_command(tag_cmd)
cli.add_command(lock_cmd)
cli.add_command(unlock_cmd)
cli.add_command(locks_cmd)
cli.add_command(get_cmd)


@click.command(name="tui")
def tui_cmd():
    """Launch the terminal user interface"""
    from gamevcs.client.tui import run_tui

    run_tui()


cli.add_command(tui_cmd)


if __name__ == "__main__":
    cli()
