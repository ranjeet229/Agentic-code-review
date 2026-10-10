from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv

from .diff import DiffError, parse_diff, read_git_diff
from .models import Finding
from .provider import ProviderError, provider_from_env
from .review import review_chunks

app = typer.Typer(help="AI-assisted review of Git diffs.")


def markdown(findings: list[Finding]) -> str:
    if not findings:
        return "# Reviewmate report\n\nNo actionable findings.\n"
    rows = ["# Reviewmate report", ""]
    for item in findings:
        rows += [f"## {item.severity.value.upper()}: {item.title}", f"**{item.file_path}:{item.line_number}** · {item.category} · confidence {item.confidence:.0%}", "", item.explanation, "", f"Suggested fix: {item.suggested_fix}", ""]
    return "\n".join(rows)


@app.command()
def review(
    staged: Annotated[bool, typer.Option("--staged", help="Review staged changes.")] = False,
    base: Annotated[str | None, typer.Option("--base", help="Review changes from BASE...HEAD.")] = None,
    format: Annotated[str, typer.Option("--format", help="terminal or json")] = "terminal",
    output: Annotated[Path | None, typer.Option("--output", help="Write a Markdown report.")] = None,
) -> None:
    if staged and base:
        raise typer.BadParameter("Use either --staged or --base, not both.")
    if format not in {"terminal", "json"}:
        raise typer.BadParameter("--format must be terminal or json.")
    load_dotenv()
    try:
        chunks = parse_diff(read_git_diff(Path.cwd(), staged=staged, base=base))
        if not chunks:
            typer.echo("No reviewable text changes found.")
            raise typer.Exit(0)
        findings = review_chunks(chunks, provider_from_env())
    except (DiffError, ProviderError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(2) from exc
    if output:
        output.write_text(markdown(findings), encoding="utf-8")
    if format == "json":
        typer.echo(json.dumps([f.model_dump(mode="json") for f in findings], indent=2))
    else:
        typer.echo(markdown(findings))


@app.command()
def config() -> None:
    load_dotenv()
    from os import getenv
    typer.echo("Configuration status:")
    typer.echo(f"  GEMINI_API_KEY: {'set' if getenv('GEMINI_API_KEY') else 'missing'}")
    typer.echo(f"  GEMINI_MODEL: {getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}")


if __name__ == "__main__":
    app()
