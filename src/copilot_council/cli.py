"""Command-line interface for Copilot Council."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from copilot_council import __version__
from copilot_council.config.loader import create_template, load_config
from copilot_council.council import Council
from copilot_council.logging import setup_logging
from copilot_council.roles.predefined import PREDEFINED_ROLES

# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="copilot-council")
def main() -> None:
    """Copilot LLM Council - Orchestrate multiple AI agents."""
    pass


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to council YAML config file.",
)
@click.option(
    "--task",
    "-t",
    type=str,
    required=True,
    help="Task/prompt for the council.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for results (markdown).",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.option(
    "--log-file",
    "-l",
    type=click.Path(path_type=Path),
    envvar="COUNCIL_LOG_FILE",
    help="Path to log file. Also reads from COUNCIL_LOG_FILE env var.",
)
def run(
    config: Path,
    task: str,
    output: Path | None,
    verbose: bool,
    log_file: Path | None,
) -> None:
    """Run a council deliberation."""
    # Set up logging - use env var as fallback
    log_level = logging.DEBUG if verbose else logging.INFO
    log_path = log_file or (Path(lf) if (lf := os.getenv("COUNCIL_LOG_FILE")) else None)
    setup_logging(level=log_level, log_file=log_path)

    console.print(f"[bold blue]Loading council from {config}...[/]")

    try:
        council_config = load_config(config)
    except Exception as e:
        console.print(f"[bold red]Error loading config:[/] {e}")
        raise SystemExit(1) from e

    council = Council.from_config(council_config.to_dict())

    console.print(
        Panel(
            f"[bold]{council.name}[/]\n"
            f"Strategy: {council.strategy} | "
            f"Members: {len(council.members)} | "
            f"Max Rounds: {council.max_rounds}",
            title="Council Configuration",
        )
    )

    console.print(f"\n[bold]Task:[/] {task}\n")

    with console.status("[bold green]Council deliberating..."):
        result = asyncio.run(council.deliberate(task))

    # Display results
    console.print("\n[bold green]Session completed![/]")
    console.print(f"Session ID: [cyan]{result.session.session_id}[/]")
    console.print(f"Status: {result.session.status}")
    if result.session.duration_seconds:
        console.print(f"Duration: {result.session.duration_seconds:.1f}s")
    console.print(
        f"Tokens: {result.session.total_input_tokens} input, "
        f"{result.session.total_output_tokens} output"
    )

    console.print("\n" + "=" * 60 + "\n")

    for response in result.responses:
        title = f"[bold]{response.member_name}[/] ({response.role}) - Round {response.round_number}"
        console.print(
            Panel(
                response.response.content,
                title=title,
                subtitle=f"Model: {response.response.model}",
            )
        )
        console.print()

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(result.to_markdown())
        console.print(f"[green]Results saved to {output}[/]")


@main.command()
def roles() -> None:
    """List available predefined roles."""
    table = Table(title="Available Roles")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")

    for role in PREDEFINED_ROLES.values():
        table.add_row(role.name, role.description)

    console.print(table)


@main.command()
@click.argument("name")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("."),
    help="Output directory for config file.",
)
def init(name: str, output: Path) -> None:
    """Initialize a new council configuration."""
    config_path = output / f"{name}.yaml"

    if config_path.exists():
        console.print(f"[yellow]Config already exists: {config_path}[/]")
        if not click.confirm("Overwrite?"):
            raise SystemExit(0)

    create_template(config_path, name)
    console.print(f"[green]Created council config: {config_path}[/]")
    console.print("\nEdit the config file, then run:")
    console.print(f"  [cyan]council run -c {config_path} -t 'Your task here'[/]")


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to council YAML config file.",
)
def validate(config: Path) -> None:
    """Validate a council configuration file."""
    try:
        council_config = load_config(config)
        console.print("[green]✓ Configuration is valid![/]")
        console.print(f"  Name: {council_config.name}")
        console.print(f"  Strategy: {council_config.strategy}")
        console.print(f"  Members: {len(council_config.members)}")
        for m in council_config.members:
            console.print(f"    - {m.name} ({m.role}, {m.model})")
    except Exception as e:
        console.print(f"[red]✗ Configuration invalid:[/] {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
