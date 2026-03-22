"""Ensure core sanitization modules never import logging (no raw payload logs)."""

from pathlib import Path


def test_core_sanitization_modules_avoid_logging() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "pii_gateway" / "core"
    for name in ("sanitize_text.py", "sanitize_structured.py", "sanitize_pipeline.py"):
        text = (root / name).read_text(encoding="utf-8")
        assert "import logging" not in text
        assert "getLogger" not in text
