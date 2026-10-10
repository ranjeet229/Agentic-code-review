from __future__ import annotations

from .models import DiffChunk, Finding
from .provider import ModelProvider

SYSTEM = """You are a precise senior code reviewer. Review only the supplied Git diff. Return JSON exactly matching {\"findings\": [{severity, category, file_path, line_number, title, explanation, suggested_fix, confidence}]}. Report likely bugs, security issues, error-handling gaps, and missing tests. Be concise. Do not invent paths or lines."""


def prompt_for(chunk: DiffChunk) -> str:
    return f"{SYSTEM}\n\nChanged file: {chunk.file_path}\nChanged added lines: {sorted(chunk.changed_lines)}\n\nDiff:\n{chunk.content}"


def valid_findings(findings: list[Finding], chunks: list[DiffChunk]) -> list[Finding]:
    valid = {(chunk.file_path, line) for chunk in chunks for line in chunk.changed_lines}
    result: list[Finding] = []
    seen: set[tuple[str, int, str]] = set()
    for finding in findings:
        key = (finding.file_path, finding.line_number, finding.title.casefold())
        if (finding.file_path, finding.line_number) in valid and key not in seen:
            seen.add(key)
            result.append(finding)
    return result


def review_chunks(chunks: list[DiffChunk], provider: ModelProvider) -> list[Finding]:
    raw: list[Finding] = []
    for chunk in chunks:
        raw.extend(provider.review(prompt_for(chunk)).findings)
    return valid_findings(raw, chunks)
