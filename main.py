"""
main.py — CLI entry point for the Millenia Ventures Capital Formation System.

Usage:
  python main.py run    --deal data/mock_deals/deal_acme_corp.json
  python main.py step   --deal data/mock_deals/deal_acme_corp.json --step 7a
  python main.py resume --deal data/mock_deals/deal_acme_corp.json --from-step 3
  python main.py status --deal data/mock_deals/deal_acme_corp.json
  python main.py report --deal data/mock_deals/deal_acme_corp.json --week 3
"""
import sys
import json
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from core.deal import Deal
from core.checkpoint import CheckpointManager
from core.workflow_engine import WorkflowEngine
from core.logger import get_logger
from config import OUTPUT_DIR

console = Console()
logger = get_logger("millenia.cli")


def _load_deal(deal_path: str) -> Deal:
    """Load and validate a Deal from a JSON file."""
    path = Path(deal_path)
    if not path.exists():
        console.print(f"[bold red]Error:[/bold red] Deal file not found: {deal_path}")
        sys.exit(1)
    try:
        deal = Deal.from_json_file(str(path))
        console.print(f"[green]✓[/green] Loaded deal: [bold]{deal.company_name}[/bold] ({deal.deal_id})")
        return deal
    except ValueError as e:
        console.print(f"[bold red]Invalid deal JSON:[/bold red] {e}")
        sys.exit(1)


def _print_status(status: dict) -> None:
    """Pretty-print a deal status report."""
    console.print(Panel(
        f"[bold]{status['company_name']}[/bold] | "
        f"${status['raise_amount']:,.0f} raise | "
        f"Stage: {status['stage']}",
        title=f"Deal Status — {status['deal_id']}",
        border_style="blue",
    ))

    # Pipeline table
    table = Table(title="Pipeline Steps", show_header=True, header_style="bold magenta")
    table.add_column("Step", width=8)
    table.add_column("Name", width=35)
    table.add_column("Status", width=12)

    STATUS_ICONS = {
        "completed": "[green]✅ Done[/green]",
        "pending": "[dim]⏳ Pending[/dim]",
        "blocked": "[red]⛔ Blocked[/red]",
        "skipped": "[yellow]⏭ Skipped[/yellow]",
        "failed": "[red]❌ Failed[/red]",
    }

    for step_id, step_info in status["pipeline"].items():
        table.add_row(
            step_id,
            step_info["name"],
            STATUS_ICONS.get(step_info["status"], step_info["status"]),
        )
    console.print(table)

    # Metrics
    m = status["metrics"]
    console.print(Panel(
        f"Contacted: {m['investors_contacted']} | "
        f"Responded: {m['investors_responded']} ({m['response_rate_percent']:.1f}%) | "
        f"Committed: {m['investors_committed']}\n"
        f"Raised: ${m['total_committed_usd']:,.0f} / ${m['raise_target_usd']:,.0f} "
        f"({m['percent_raised']:.1f}%) | "
        f"Week: {m['outreach_week']} | "
        f"Campaign: {'🟢 Active' if m['campaign_active'] else '⚫ Inactive'}",
        title="Key Metrics",
        border_style="green",
    ))

    if status["errors"]:
        console.print(Panel(
            "\n".join(f"• {e}" for e in status["errors"]),
            title=f"[red]Errors ({len(status['errors'])})[/red]",
            border_style="red",
        ))


# ── CLI Commands ───────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Millenia Ventures — Capital Formation Automation System"""
    pass


@cli.command()
@click.option("--deal", required=True, help="Path to deal JSON file")
def run(deal):
    """Run the full 14-step pipeline for a deal."""
    console.print(Panel(
        "[bold blue]Millenia Ventures — Capital Formation System[/bold blue]\n"
        "Running full pipeline…",
        border_style="blue",
    ))

    deal_obj = _load_deal(deal)

    # Check for existing checkpoint
    checkpoint_mgr = CheckpointManager(str(OUTPUT_DIR))
    if checkpoint_mgr.exists(deal_obj.deal_id):
        last_step = checkpoint_mgr.get_last_completed_step(deal_obj.deal_id)
        console.print(
            f"\n[yellow]Checkpoint found[/yellow] — last completed step: {last_step}\n"
            f"Use [bold]python main.py resume[/bold] to continue from checkpoint, "
            f"or [bold]--restart[/bold] to start fresh."
        )
        if not click.confirm("Start fresh (ignore checkpoint)?", default=False):
            console.print("Use: python main.py resume --deal <file> --from-step <step>")
            sys.exit(0)

    engine = WorkflowEngine()
    deal_obj = engine.run_full_pipeline(deal_obj)

    # Print final status
    status = engine.get_status_report(deal_obj)
    _print_status(status)

    console.print(f"\n[bold green]Pipeline complete.[/bold green] Outputs in: outputs/{deal_obj.deal_id}/")


@cli.command()
@click.option("--deal", required=True, help="Path to deal JSON file")
@click.option("--step", required=True, help="Step to run (e.g., 2, 7a, 14)")
def step(deal, step):
    """Run a single step for a deal."""
    deal_obj = _load_deal(deal)
    engine = WorkflowEngine()

    # Normalize step ID
    step_id = step.lower().lstrip("0") or "0"
    if len(step_id) == 1 and step_id.isdigit():
        step_id = f"0{step_id}"

    console.print(f"Running step [bold]{step_id}[/bold] for [bold]{deal_obj.company_name}[/bold]…\n")

    try:
        deal_obj, result = engine.run_step(deal_obj, step_id)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Print result
    success = result.get("success", False)
    icon = "[green]✅[/green]" if success else "[red]❌[/red]"
    console.print(f"\n{icon} Step {step_id} {'succeeded' if success else 'failed'}")

    if result.get("errors"):
        console.print("[yellow]Errors:[/yellow]")
        for err in result["errors"]:
            console.print(f"  • {err}")

    if result.get("human_actions_required"):
        console.print("[cyan]Human Actions Required:[/cyan]")
        for action in result["human_actions_required"]:
            console.print(f"  ⚡ {action}")

    output_files = result.get("output", {})
    if output_files:
        console.print(f"\n[dim]Outputs saved to: outputs/{deal_obj.deal_id}/[/dim]")


@cli.command()
@click.option("--deal", required=True, help="Path to deal JSON file")
@click.option("--from-step", "from_step", required=True, help="Step to resume from (e.g., 3, 07a)")
def resume(deal, from_step):
    """Resume pipeline from a specific step (or pick up from checkpoint)."""
    checkpoint_mgr = CheckpointManager(str(OUTPUT_DIR))

    deal_obj = _load_deal(deal)

    # Try to load checkpoint for this deal
    checkpointed = checkpoint_mgr.load(deal_obj.deal_id)
    if checkpointed:
        console.print(
            f"[green]Checkpoint loaded[/green] — restoring deal state from checkpoint."
        )
        deal_obj = checkpointed

    # Normalize step
    step_id = from_step.lower().lstrip("0") or "0"
    if len(step_id) == 1 and step_id.isdigit():
        step_id = f"0{step_id}"

    console.print(f"Resuming from step [bold]{step_id}[/bold]…\n")
    engine = WorkflowEngine()
    deal_obj = engine.run_from_step(deal_obj, step_id)

    status = engine.get_status_report(deal_obj)
    _print_status(status)


@cli.command()
@click.option("--deal", required=True, help="Path to deal JSON file")
def status(deal):
    """Check the pipeline status for a deal."""
    deal_obj = _load_deal(deal)

    # Try to load checkpoint
    checkpoint_mgr = CheckpointManager(str(OUTPUT_DIR))
    checkpointed = checkpoint_mgr.load(deal_obj.deal_id)
    if checkpointed:
        deal_obj = checkpointed
        console.print("[dim]State loaded from checkpoint.[/dim]\n")

    engine = WorkflowEngine()
    status_data = engine.get_status_report(deal_obj)
    _print_status(status_data)


@cli.command()
@click.option("--deal", required=True, help="Path to deal JSON file")
@click.option("--week", default=None, type=int, help="Specific week number to report on")
def report(deal, week):
    """Generate a weekly report for a deal."""
    deal_obj = _load_deal(deal)

    # Try to load checkpoint
    checkpoint_mgr = CheckpointManager(str(OUTPUT_DIR))
    checkpointed = checkpoint_mgr.load(deal_obj.deal_id)
    if checkpointed:
        deal_obj = checkpointed

    if week is not None:
        deal_obj.outreach_week = week

    console.print(
        f"Generating week {deal_obj.outreach_week or 1} report for [bold]{deal_obj.company_name}[/bold]…\n"
    )

    engine = WorkflowEngine()
    deal_obj, result = engine.run_step(deal_obj, "14")

    if result.get("success"):
        report_file = result.get("output", {}).get("weekly_report", "")
        console.print(f"[green]✅ Report generated:[/green] {report_file}")
    else:
        console.print("[red]Report generation failed:[/red]")
        for err in result.get("errors", []):
            console.print(f"  • {err}")

    if result.get("human_actions_required"):
        console.print("\n[yellow]⚡ Actions Required:[/yellow]")
        for action in result["human_actions_required"]:
            console.print(f"  • {action}")


if __name__ == "__main__":
    cli()
