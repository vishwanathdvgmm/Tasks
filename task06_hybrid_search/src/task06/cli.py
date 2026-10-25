import json
import typer
from rich.console import Console
from rich.table import Table
from .db import connect, initialize_schema
from .seed import seed_documents
from .retrieval import vector_search, lexical_search, hybrid_search
from .benchmark import run_benchmark

app = typer.Typer(help="Task 06: hybrid search and precision retrieval")
console = Console()

@app.command()
def check():
    """Check database connectivity and initialize the schema."""
    initialize_schema()
    with connect() as conn:
        conn.execute("SELECT 1")
    console.print("[green]PostgreSQL + pgvector connection OK; schema initialized[/green]")

@app.command()
def seed(tenant: str = typer.Option("org_demo", "--tenant")):
    """Insert or update deterministic demo documents."""
    count = seed_documents(tenant)
    console.print(f"[green]Seeded {count} documents for tenant {tenant}[/green]")

@app.command()
def search(
    query: str = typer.Argument(...),
    tenant: str = typer.Option("org_demo", "--tenant"),
    mode: str = typer.Option("hybrid", "--mode", help="vector, lexical, hybrid"),
    top_k: int = typer.Option(5, "--top-k", min=1, max=50),
):
    """Search the corpus with one retrieval strategy."""
    if mode == "vector":
        results = vector_search(query, tenant, 50)[:top_k]
    elif mode == "lexical":
        results = lexical_search(query, tenant, 50)[:top_k]
    elif mode == "hybrid":
        results = hybrid_search(query, tenant, 50, top_k, True)
    else:
        raise typer.BadParameter("mode must be vector, lexical, or hybrid")
    table = Table("Rank", "ID", "Title", "Score", "Source")
    for index, result in enumerate(results, start=1):
        table.add_row(str(index), result.external_id, result.title, f"{result.score:.4f}", result.source)
    console.print(table)

@app.command()
def benchmark(tenant: str = typer.Option("org_demo", "--tenant")):
    """Compare vector-only, lexical-only, and hybrid+reranker metrics."""
    report = run_benchmark(tenant)
    console.print_json(json.dumps(report, indent=2))
