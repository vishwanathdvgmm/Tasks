import asyncio
import json
import typer
from rich.console import Console
from rich.table import Table
from .benchmark import run_benchmark, save_report
from .client import OpenAICompatibleClient
from .config import settings
from .vram import estimate_vram

app = typer.Typer(help="Task 13: local LLM serving, VRAM estimation, and benchmarking.")
console = Console()

def make_client() -> OpenAICompatibleClient:
    return OpenAICompatibleClient(settings.base_url, settings.api_key, settings.timeout_seconds)

@app.command()
def doctor():
    """Check whether the configured OpenAI-compatible endpoint is reachable."""
    async def run():
        client = make_client()
        try:
            data = await client.models()
            console.print(f"[green]Endpoint reachable:[/green] {settings.base_url}")
            table = Table("Model ID")
            for item in data.get("data", []):
                table.add_row(str(item.get("id", "unknown")))
            console.print(table)
        except Exception as exc:
            console.print(f"[red]Connection failed:[/red] {exc}")
            raise typer.Exit(1)
    asyncio.run(run())

@app.command()
def chat(prompt: str = typer.Argument(..., help="Prompt to send to the local model."),
         model: str = typer.Option(settings.model, help="Model identifier."),
         max_tokens: int = typer.Option(128, min=1, max=8192)):
    """Send one prompt to an OpenAI-compatible local model endpoint."""
    async def run():
        try:
            data = await make_client().chat(model, prompt, max_tokens=max_tokens)
            choices = data.get("choices", [])
            if not choices:
                console.print_json(json.dumps(data))
                return
            console.print(choices[0].get("message", {}).get("content", ""))
            if data.get("usage"):
                console.print(f"\n[dim]Usage: {data['usage']}[/dim]")
        except Exception as exc:
            console.print(f"[red]Request failed:[/red] {exc}")
            raise typer.Exit(1)
    asyncio.run(run())

@app.command()
def vram(parameters: float = typer.Option(8.0, help="Parameter count in billions."),
         bits: int = typer.Option(4, help="Weight precision: 4, 8, or 16 bits."),
         context: int = typer.Option(4096, help="Context tokens per request."),
         concurrency: int = typer.Option(1, help="Concurrent active requests."),
         layers: int = typer.Option(32),
         kv_heads: int = typer.Option(8),
         head_dim: int = typer.Option(128),
         overhead: float = typer.Option(1.5, help="Runtime overhead in GB.")):
    """Estimate weight, KV-cache, and runtime VRAM requirements."""
    try:
        result = estimate_vram(parameters, bits, context, concurrency, layers, kv_heads, head_dim,
                               runtime_overhead_gb=overhead)
    except ValueError as exc:
        raise typer.BadParameter(str(exc))
    table = Table("Component", "Estimated GB")
    table.add_row("Weights (incl. quantization overhead)", f"{result.weight_gb:.2f}")
    table.add_row("KV cache", f"{result.kv_cache_gb:.2f}")
    table.add_row("Runtime overhead", f"{result.runtime_overhead_gb:.2f}")
    table.add_row("[bold]Total[/bold]", f"[bold]{result.total_gb:.2f}[/bold]")
    console.print(table)
    console.print("[dim]Estimate only. Actual use varies by architecture, quantization metadata, context, and runtime.[/dim]")

@app.command()
def benchmark(prompt: str = typer.Option("Explain quantization in two sentences."),
              model: str = typer.Option(settings.model),
              requests: int = typer.Option(10, min=1, max=1000),
              concurrency: int = typer.Option(2, min=1, max=256),
              max_tokens: int = typer.Option(128, min=1, max=8192),
              output: str = typer.Option("results/benchmark.json")):
    """Run concurrent requests and save a JSON benchmark report."""
    async def run():
        report = await run_benchmark(make_client(), model, prompt, requests, concurrency, max_tokens)
        save_report(report, output)
        console.print_json(json.dumps({k: v for k, v in report.items() if k != "results"}))
        console.print(f"\nSaved detailed report to [bold]{output}[/bold]")
        if report["failed_requests"]:
            raise typer.Exit(1)
    asyncio.run(run())

if __name__ == "__main__":
    app()
