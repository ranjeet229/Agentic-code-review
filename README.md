# Reviewmate

`reviewmate` is a Python 3.11+ command-line tool that asks an LLM to review a Git diff for likely bugs, security problems, error-handling gaps, and missing tests. It only reads the diff: it does not modify Git state, commit, push, or create pull requests.

## Setup

### Install from PyPI

Install the published CLI into an existing Python environment:

```powershell
pip install reviewmate
$env:GEMINI_API_KEY = 'YOUR_GEMINI_KEY'
$env:GEMINI_MODEL = 'YOUR_GEMINI_MODEL'
reviewmate review
```

For an isolated installation (recommended), create a virtual environment and then run Reviewmate from the Git repository you want to inspect:

```powershell
python -m venv reviewmate-env
.\reviewmate-env\Scripts\Activate.ps1
pip install --upgrade reviewmate

$env:GEMINI_API_KEY = 'YOUR_GEMINI_KEY'
$env:GEMINI_MODEL = 'YOUR_GEMINI_MODEL'

cd C:\path\to\their-git-project
reviewmate review
```

Replace `YOUR_GEMINI_KEY` and `YOUR_GEMINI_MODEL` with your Gemini API key and selected model. Reviewmate reads the current repository's Git diff; it does not start a server or modify repository files.

### Local development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Set `GEMINI_API_KEY` in `.env`. `GEMINI_MODEL` defaults to `gemini-3.5-flash-lite` and can be changed there. Reviewmate uses Gemini's `generateContent` API. The provider is isolated behind `ModelProvider` so another provider can be added without changing review orchestration.

Never commit `.env` or API keys.

## Commands

```powershell
reviewmate config
reviewmate review                 # unstaged changes
reviewmate review --staged        # index / staged changes
reviewmate review --base main     # main...HEAD
reviewmate review --format json
reviewmate review --output report.md
```

`--staged` and `--base` are mutually exclusive. Findings are validated with Pydantic, filtered to changed added lines, and deduplicated by path, line, and title. Model failures, malformed output, timeouts, and rate limits exit with an error rather than claiming a review was performed. Binary diffs and empty diffs are skipped. Large text diffs are split into bounded chunks.

## Development

```powershell
pytest
ruff check .
mypy src
```

The tests mock the provider boundary and do not use credentials or network access. A representative input and expected-style report are in `examples/`.

## Limitations

LLM findings are advisory and may miss issues or contain false positives. Reviewmate deliberately accepts only findings anchored to added lines in the supplied diff, so it does not report pre-existing code outside the change. Context is limited to Git diff hunks and each request chunk.
