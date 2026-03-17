import click
from rich.console import Console
from rich.table import Table
from rich import box

from app.db import get_connection
from app.models import init_db
from app.task_manager import (
    add_task,
    get_task,
    list_tasks,
    update_task_status,
    add_log,
    get_logs,
    get_failed_tasks,
    increment_retries,
)
from app.executor import run_with_retry

console = Console()

STATUS_COLORS = {
    "PENDING": "yellow",
    "RUNNING": "blue",
    "SUCCESS": "green",
    "FAILED":  "red",
}


def _color(status: str) -> str:
    return STATUS_COLORS.get(status, "white")


# ─────────────────────────────────────────────────────────
# CLI Group
# ─────────────────────────────────────────────────────────

@click.group()
def cli():
    """🚀 Mini Task Automation & Job Tracking CLI

    \b
    Commands:
      add          Add a new task
      run          Execute a task by ID (with retry)
      status       Show status of a task
      logs         View execution logs for a task
      list         List all tasks
      retry-failed Retry all failed tasks
    """
    pass


# ─────────────────────────────────────────────────────────
# ADD
# ─────────────────────────────────────────────────────────

@cli.command()
@click.argument("command")
def add(command: str):
    """Add a new task (shell command) to the queue.

    \b
    Example:
      python cli.py add "echo hello world"
      python cli.py add "ls -la /tmp"
    """
    conn = get_connection()
    init_db(conn)
    task_id = add_task(command, conn)
    conn.close()
    console.print(
        f"[bold green]✓ Task #{task_id} added:[/bold green] [cyan]{command}[/cyan]"
    )


# ─────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────

@cli.command()
@click.argument("task_id", type=int)
@click.option(
    "--retries",
    default=3,
    show_default=True,
    help="Max retry attempts on failure.",
)
def run(task_id: int, retries: int):
    """Execute a task by its ID with automatic retry on failure.

    \b
    Example:
      python cli.py run 1
      python cli.py run 2 --retries 5
    """
    conn = get_connection()
    task = get_task(task_id, conn)
    if not task:
        console.print(f"[red]✗ Task #{task_id} not found.[/red]")
        conn.close()
        return

    console.print(
        f"[bold yellow]▶ Running Task #{task_id}:[/bold yellow] [cyan]{task['command']}[/cyan]"
    )
    update_task_status(task_id, "RUNNING", conn)

    output, status, attempts = run_with_retry(task["command"], max_retries=retries)

    update_task_status(task_id, status, conn)
    add_log(task_id, output, status, conn)
    conn.close()

    color = _color(status)
    if status == "SUCCESS":
        console.print(
            f"[bold green]✓ SUCCESS[/bold green] (completed in {attempts} attempt(s))"
        )
    else:
        console.print(
            f"[bold red]✗ FAILED[/bold red] after {attempts} attempt(s)"
        )
    console.rule("[dim]Output[/dim]")
    console.print(output or "[dim](no output)[/dim]")


# ─────────────────────────────────────────────────────────
# STATUS
# ─────────────────────────────────────────────────────────

@cli.command()
@click.argument("task_id", type=int)
def status(task_id: int):
    """Check the current status of a task.

    \b
    Example:
      python cli.py status 1
    """
    conn = get_connection()
    task = get_task(task_id, conn)
    conn.close()

    if not task:
        console.print(f"[red]✗ Task #{task_id} not found.[/red]")
        return

    c = _color(task["status"])
    console.print(
        f"  Task [bold]#{task['id']}[/bold]  "
        f"Status: [{c}]{task['status']}[/{c}]  "
        f"Retries: [bold]{task['retries']}[/bold]  "
        f"Created: [dim]{task['created_at']}[/dim]\n"
        f"  Command: [cyan]{task['command']}[/cyan]"
    )


# ─────────────────────────────────────────────────────────
# LOGS
# ─────────────────────────────────────────────────────────

@cli.command()
@click.argument("task_id", type=int)
def logs(task_id: int):
    """View execution logs for a specific task.

    \b
    Example:
      python cli.py logs 1
    """
    conn = get_connection()
    task_logs = get_logs(task_id, conn)
    conn.close()

    if not task_logs:
        console.print(f"[yellow]No logs found for Task #{task_id}[/yellow]")
        return

    table = Table(title=f"Execution Logs — Task #{task_id}", box=box.ROUNDED)
    table.add_column("#",          style="dim",  width=5)
    table.add_column("Status",     style="bold", width=10)
    table.add_column("Output",                   no_wrap=False)
    table.add_column("Executed At", style="dim", width=22)

    for log in task_logs:
        c = _color(log["status"])
        table.add_row(
            str(log["id"]),
            f"[{c}]{log['status']}[/{c}]",
            (log["output"] or "")[:120],
            str(log["executed_at"]),
        )
    console.print(table)


# ─────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────

@cli.command("list")
def list_all():
    """List all tasks in the system.

    \b
    Example:
      python cli.py list
    """
    conn = get_connection()
    tasks = list_tasks(conn)
    conn.close()

    if not tasks:
        console.print("[yellow]No tasks found. Use [bold]add[/bold] to create one.[/yellow]")
        return

    table = Table(title="All Tasks", box=box.ROUNDED)
    table.add_column("ID",         style="dim",  width=5)
    table.add_column("Command",    style="cyan")
    table.add_column("Status",     style="bold", width=12)
    table.add_column("Retries",    width=8)
    table.add_column("Created At", style="dim",  width=22)

    for task in tasks:
        c = _color(task["status"])
        table.add_row(
            str(task["id"]),
            task["command"],
            f"[{c}]{task['status']}[/{c}]",
            str(task["retries"]),
            str(task["created_at"]),
        )
    console.print(table)


# ─────────────────────────────────────────────────────────
# RETRY-FAILED
# ─────────────────────────────────────────────────────────

@cli.command("retry-failed")
def retry_failed():
    """Retry all tasks currently in FAILED state.

    \b
    Example:
      python cli.py retry-failed
    """
    conn = get_connection()
    failed = get_failed_tasks(conn)

    if not failed:
        console.print("[bold green]✓ No failed tasks found.[/bold green]")
        conn.close()
        return

    console.print(f"[yellow]Found [bold]{len(failed)}[/bold] failed task(s). Retrying...[/yellow]\n")

    for task in failed:
        console.print(f"  [bold]→ Task #{task['id']}:[/bold] [cyan]{task['command']}[/cyan]")
        update_task_status(task["id"], "RUNNING", conn)
        increment_retries(task["id"], conn)

        output, status, attempts = run_with_retry(task["command"])
        update_task_status(task["id"], status, conn)
        add_log(task["id"], output, status, conn)

        c = _color(status)
        console.print(f"    [{c}]{status}[/{c}] after {attempts} attempt(s)\n")

    conn.close()


# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
