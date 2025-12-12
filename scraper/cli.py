"""
Mortgage Rate Scraper CLI

A command-line tool for scraping current mortgage rates from multiple
financial sources. Uses async Playwright for browser automation and
implements various anti-detection measures.

Usage:
    python -m scraper.cli scrape                    # Scrape all sources
    python -m scraper.cli scrape --source bankrate  # Scrape specific source
    python -m scraper.cli scrape --zip 10001        # Use specific zip code
    python -m scraper.cli scrape --no-headless      # Show browser window
    python -m scraper.cli list-sources              # List available sources
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import typer
from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.table import Table
from rich.text import Text
from dotenv import load_dotenv

from scrapers import (
    MortgageScraper,
    MortgageRates,
    BankrateScraper,
    NerdWalletScraper,
    WellsFargoScraper,
    ChaseScraper,
    ZillowScraper,
    SCRAPER_REGISTRY,
)
from utils.helpers import generate_timestamp_filename, ScraperMetrics

# Load environment variables from .env file if present
load_dotenv()

# Initialize CLI app and console
app = typer.Typer(
    name="mortgage-scraper",
    help="Scrape current mortgage rates from multiple financial sources.",
    add_completion=False,
)
console = Console()

# Default zip code (can be overridden via env var or CLI arg)
DEFAULT_ZIP_CODE = os.getenv("MORTGAGE_SCRAPER_ZIP", "90210")


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging with rich formatting.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_time=False,
                show_path=False,
            )
        ],
    )


def create_results_table(results: List[MortgageRates]) -> Table:
    """
    Create a rich Table displaying scraped mortgage rates.

    Args:
        results: List of MortgageRates from all scrapers

    Returns:
        Formatted rich Table object
    """
    table = Table(
        title="Current Mortgage Rates",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold white",
        border_style="blue",
        show_lines=True,
    )

    # Add columns
    table.add_column("Source", style="bold white", min_width=12)
    table.add_column("30-Year Fixed", justify="right", style="green")
    table.add_column("15-Year Fixed", justify="right", style="green")
    table.add_column("5/1 ARM", justify="right", style="green")
    table.add_column("Status", justify="center", min_width=10)
    table.add_column("Time (ms)", justify="right", style="dim")

    for rate in results:
        # Format rate values or show N/A
        thirty_yr = f"{rate.thirty_year_fixed:.3f}%" if rate.thirty_year_fixed else "[dim]N/A[/dim]"
        fifteen_yr = f"{rate.fifteen_year_fixed:.3f}%" if rate.fifteen_year_fixed else "[dim]N/A[/dim]"
        arm = f"{rate.arm_5_1:.3f}%" if rate.arm_5_1 else "[dim]N/A[/dim]"

        # Status indicator
        if rate.error:
            status = Text("FAILED", style="bold red")
        elif rate.is_valid:
            status = Text("OK", style="bold green")
        else:
            status = Text("PARTIAL", style="bold yellow")

        # Duration
        duration = f"{rate.duration_ms:.0f}"

        table.add_row(
            rate.source,
            thirty_yr,
            fifteen_yr,
            arm,
            status,
            duration,
        )

    return table


def create_summary_panel(results: List[MortgageRates], metrics: ScraperMetrics) -> Panel:
    """
    Create a summary panel with aggregate statistics.

    Args:
        results: List of MortgageRates from all scrapers
        metrics: ScraperMetrics with timing data

    Returns:
        Rich Panel with summary statistics
    """
    # Calculate averages (excluding None values)
    thirty_yr_rates = [r.thirty_year_fixed for r in results if r.thirty_year_fixed]
    fifteen_yr_rates = [r.fifteen_year_fixed for r in results if r.fifteen_year_fixed]
    arm_rates = [r.arm_5_1 for r in results if r.arm_5_1]

    avg_30 = sum(thirty_yr_rates) / len(thirty_yr_rates) if thirty_yr_rates else None
    avg_15 = sum(fifteen_yr_rates) / len(fifteen_yr_rates) if fifteen_yr_rates else None
    avg_arm = sum(arm_rates) / len(arm_rates) if arm_rates else None

    # Build summary text
    lines = [
        f"[bold]Scrape Summary[/bold]",
        f"",
        f"[cyan]Total Sources:[/cyan] {len(results)}",
        f"[green]Successful:[/green] {metrics.success_count}",
        f"[red]Failed:[/red] {metrics.failure_count}",
        f"[dim]Duration:[/dim] {metrics.total_duration_seconds:.1f}s",
        f"",
        f"[bold]Average Rates[/bold]",
        f"[cyan]30-Year Fixed:[/cyan] {f'{avg_30:.3f}%' if avg_30 else 'N/A'}",
        f"[cyan]15-Year Fixed:[/cyan] {f'{avg_15:.3f}%' if avg_15 else 'N/A'}",
        f"[cyan]5/1 ARM:[/cyan] {f'{avg_arm:.3f}%' if avg_arm else 'N/A'}",
    ]

    return Panel(
        "\n".join(lines),
        title="Summary",
        border_style="green",
        padding=(1, 2),
    )


def save_to_csv(results: List[MortgageRates], output_path: Optional[str] = None) -> str:
    """
    Save results to a timestamped CSV file.

    Args:
        results: List of MortgageRates to save
        output_path: Optional custom path; if None, generates timestamped filename

    Returns:
        Path to the saved file
    """
    if output_path is None:
        output_path = generate_timestamp_filename("mortgage_rates", "csv")

    # Convert to DataFrame
    data = [rate.to_dict() for rate in results]
    df = pd.DataFrame(data)

    # Reorder columns for readability
    column_order = [
        "source",
        "30_year_fixed",
        "15_year_fixed",
        "5_1_arm",
        "scraped_at",
        "duration_ms",
        "error",
    ]
    df = df[[col for col in column_order if col in df.columns]]

    # Save to CSV
    df.to_csv(output_path, index=False)

    return output_path


async def run_scrapers_parallel(
    scrapers: List[MortgageScraper],
    progress: Progress,
    task_ids: dict[str, TaskID],
) -> List[MortgageRates]:
    """
    Run multiple scrapers concurrently using asyncio.gather.

    Why parallel execution?
    - Each scraper is I/O bound (waiting for network, page loads)
    - Running in parallel reduces total time from sum to max
    - Example: 5 scrapers × 30s = 150s serial, ~30s parallel

    Args:
        scrapers: List of scraper instances to run
        progress: Rich Progress for updates
        task_ids: Map of source name to Progress task ID

    Returns:
        List of MortgageRates from all scrapers
    """

    async def scrape_with_progress(scraper: MortgageScraper) -> MortgageRates:
        """Wrapper to update progress bar during scraping."""
        task_id = task_ids[scraper.source_name]
        progress.update(task_id, description=f"[cyan]{scraper.source_name}[/cyan] - Scraping...")

        try:
            result = await scraper.scrape()

            if result.error:
                progress.update(task_id, description=f"[red]{scraper.source_name}[/red] - Failed")
            elif result.is_valid:
                progress.update(task_id, description=f"[green]{scraper.source_name}[/green] - Done")
            else:
                progress.update(task_id, description=f"[yellow]{scraper.source_name}[/yellow] - Partial")

            progress.update(task_id, completed=1)
            return result

        except Exception as e:
            progress.update(task_id, description=f"[red]{scraper.source_name}[/red] - Error")
            progress.update(task_id, completed=1)
            return MortgageRates(source=scraper.source_name, error=str(e))

    # Run all scrapers concurrently
    # asyncio.gather runs all coroutines in parallel and waits for all to complete
    results = await asyncio.gather(
        *[scrape_with_progress(scraper) for scraper in scrapers],
        return_exceptions=False,  # Exceptions are handled inside scrape_with_progress
    )

    return list(results)


@app.command()
def scrape(
    sources: Optional[List[str]] = typer.Option(
        None,
        "--source",
        "-s",
        help="Specific source(s) to scrape. Can be repeated. If not specified, scrapes all.",
    ),
    zip_code: str = typer.Option(
        DEFAULT_ZIP_CODE,
        "--zip",
        "-z",
        help="ZIP code for location-specific rates.",
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output CSV file path. Default: mortgage_rates_[timestamp].csv",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--no-headless",
        help="Run browsers in headless mode (no visible window).",
    ),
    timeout: int = typer.Option(
        30000,
        "--timeout",
        "-t",
        help="Timeout in milliseconds for page loads.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging output.",
    ),
) -> None:
    """
    Scrape mortgage rates from financial websites.

    Runs scrapers concurrently for speed. Results are displayed in a
    formatted table and saved to CSV.

    Examples:

        # Scrape all sources
        python -m scraper.cli scrape

        # Scrape specific sources
        python -m scraper.cli scrape -s bankrate -s chase

        # Use custom zip code
        python -m scraper.cli scrape --zip 10001

        # Show browser windows for debugging
        python -m scraper.cli scrape --no-headless -v
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    # Validate and select sources
    if sources:
        # Validate source names
        invalid = [s for s in sources if s.lower() not in SCRAPER_REGISTRY]
        if invalid:
            console.print(f"[red]Unknown sources: {', '.join(invalid)}[/red]")
            console.print(f"Available: {', '.join(SCRAPER_REGISTRY.keys())}")
            raise typer.Exit(1)

        scraper_classes = [SCRAPER_REGISTRY[s.lower()] for s in sources]
    else:
        scraper_classes = list(SCRAPER_REGISTRY.values())

    # Create scraper instances
    scrapers = [
        cls(zip_code=zip_code, headless=headless, timeout_ms=timeout)
        for cls in scraper_classes
    ]

    # Display startup banner
    console.print()
    console.print(
        Panel(
            f"[bold]Mortgage Rate Scraper[/bold]\n\n"
            f"Sources: {len(scrapers)}\n"
            f"ZIP Code: {zip_code}\n"
            f"Headless: {headless}\n"
            f"Timeout: {timeout}ms",
            border_style="blue",
        )
    )
    console.print()

    # Track metrics
    metrics = ScraperMetrics()
    metrics.start()

    # Run scrapers with progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=False,
    ) as progress:
        # Create progress tasks for each scraper
        task_ids = {
            scraper.source_name: progress.add_task(
                f"[dim]{scraper.source_name}[/dim] - Waiting...",
                total=1,
            )
            for scraper in scrapers
        }

        # Run all scrapers concurrently
        results = asyncio.run(run_scrapers_parallel(scrapers, progress, task_ids))

    metrics.end()

    # Update metrics with results
    for rate in results:
        if rate.error:
            metrics.record_failure(rate.source, rate.error, rate.duration_ms)
        else:
            metrics.record_success(rate.source, rate.duration_ms)

    # Display results
    console.print()
    console.print(create_results_table(results))
    console.print()
    console.print(create_summary_panel(results, metrics))

    # Save to CSV
    csv_path = save_to_csv(results, output)
    console.print(f"\n[dim]Results saved to:[/dim] [bold]{csv_path}[/bold]\n")


@app.command("list-sources")
def list_sources() -> None:
    """
    List all available scraper sources.

    Shows the name and target URL for each scraper.
    """
    console.print()
    table = Table(
        title="Available Sources",
        box=box.ROUNDED,
        header_style="bold cyan",
    )

    table.add_column("Name", style="bold white")
    table.add_column("URL", style="dim")

    for name, cls in SCRAPER_REGISTRY.items():
        # Create a temporary instance to get the URL
        instance = cls()
        table.add_row(name, instance.base_url)

    console.print(table)
    console.print()


@app.command()
def version() -> None:
    """Display version information."""
    console.print("[bold]Mortgage Rate Scraper[/bold] v1.0.0")
    console.print("Built with Playwright, Typer, and Rich")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
