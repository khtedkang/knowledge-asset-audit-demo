"""Portable, standard-library tools for a synthetic knowledge-asset audit."""

from .core import AssetRecord, AuditResult, audit_directory, write_audit_outputs
from .generator import generate_synthetic_dataset

__all__ = [
    "AssetRecord",
    "AuditResult",
    "audit_directory",
    "generate_synthetic_dataset",
    "write_audit_outputs",
]

__version__ = "1.0.0"

