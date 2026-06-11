"""Backward-compatible re-export of process_prompt."""
from src.process_prompt import process_prompt  # noqa: F401

__all__ = ["process_prompt"]
