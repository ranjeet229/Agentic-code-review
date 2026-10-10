from reviewmate.models import DiffChunk, Finding, ReviewResponse, Severity
from reviewmate.provider import ModelProvider
from reviewmate.review import review_chunks, valid_findings


def finding(**overrides: object) -> Finding:
    data: dict[str, object] = {"severity": Severity.HIGH, "category": "security", "file_path": "app.py", "line_number": 3, "title": "Unsafe eval", "explanation": "Untrusted input is executed.", "suggested_fix": "Use a safe parser.", "confidence": 0.9}
    data.update(overrides)
    return Finding.model_validate(data)


def test_validate_model_output() -> None:
    response = ReviewResponse.model_validate({"findings": [finding().model_dump()]})
    assert response.findings[0].title == "Unsafe eval"


def test_discards_unmatched_lines_and_deduplicates() -> None:
    chunks = [DiffChunk(file_path="app.py", changed_lines={3}, content="+")]
    items = [finding(), finding(), finding(line_number=99), finding(file_path="other.py")]
    assert valid_findings(items, chunks) == [finding()]


def test_rejects_path_traversal() -> None:
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        finding(file_path="../secret.py")


class StubProvider(ModelProvider):
    def review(self, prompt: str) -> ReviewResponse:
        assert "Changed file: app.py" in prompt
        return ReviewResponse(findings=[finding()])


def test_review_uses_provider_response_and_validates_anchor() -> None:
    chunks = [DiffChunk(file_path="app.py", changed_lines={3}, content="+value")]
    assert review_chunks(chunks, StubProvider()) == [finding()]
