from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import DiffChunk

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class DiffError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedFile:
    path: str
    changed_lines: set[int]
    text: str


def read_git_diff(repo: Path, *, staged: bool, base: str | None) -> str:
    args = ["git", "diff", "--no-ext-diff", "--unified=3", "--no-color"]
    if staged:
        args.append("--cached")
    elif base:
        args.append(f"{base}...HEAD")
    try:
        result = subprocess.run(args, cwd=repo, text=True, capture_output=True, timeout=30, check=False)
    except FileNotFoundError as exc:
        raise DiffError("Git is not installed or is not available on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise DiffError("Timed out while reading the Git diff.") from exc
    if result.returncode:
        if "not a git repository" in result.stderr.lower():
            raise DiffError(
                "This folder is not a Git repository. Run `git init`, make an initial commit, "
                "then change a file before running Reviewmate."
            )
        raise DiffError(result.stderr.strip() or "Could not read Git diff. Are you in a repository?")
    return result.stdout


def parse_diff(diff: str, *, max_chunk_chars: int = 12000) -> list[DiffChunk]:
    files: list[ParsedFile] = []
    current_path: str | None = None
    lines: set[int] = set()
    buffer: list[str] = []
    new_line = 0

    def flush() -> None:
        nonlocal current_path, lines, buffer
        if current_path and buffer and not any("Binary files" in line for line in buffer):
            files.append(ParsedFile(current_path, lines, "\n".join(buffer)))
        current_path, lines, buffer = None, set(), []

    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            flush()
            buffer.append(raw)
        elif raw.startswith("+++ b/"):
            current_path = raw[6:]
            buffer.append(raw)
        elif raw.startswith("+++ /dev/null"):
            current_path = None
            buffer.append(raw)
        else:
            match = HUNK.match(raw)
            if match:
                new_line = int(match.group(1))
                buffer.append(raw)
            elif raw.startswith("+") and not raw.startswith("+++"):
                if current_path:
                    lines.add(new_line)
                new_line += 1
                buffer.append(raw)
            elif raw.startswith("-") and not raw.startswith("---"):
                buffer.append(raw)
            else:
                if raw and not raw.startswith("\\") and new_line:
                    new_line += 1
                buffer.append(raw)
    flush()

    chunks: list[DiffChunk] = []
    for item in files:
        text = item.text
        if len(text) <= max_chunk_chars:
            chunks.append(DiffChunk(file_path=item.path, changed_lines=item.changed_lines, content=text))
        else:
            for start in range(0, len(text), max_chunk_chars):
                part = text[start : start + max_chunk_chars]
                chunks.append(DiffChunk(file_path=item.path, changed_lines=item.changed_lines, content=part))
    return chunks
