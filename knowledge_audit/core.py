"""Inventory, hashing, classification, duplicate detection, and reporting."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


HASH_CHUNK_SIZE = 1024 * 1024


@dataclass
class AssetRecord:
    relative_path: str
    extension: str
    size_bytes: int | None
    modified_utc: str
    sha256: str
    project: str
    asset_type: str
    lifecycle_hint: str
    duplicate_group: str = ""
    duplicate_of: str = ""
    read_error: str = ""


@dataclass
class AuditResult:
    root: str
    records: list[AssetRecord]
    summary: dict[str, object]


PROJECT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Self-injectable medicine return model",
        ("self injection", "self injectable", "medicine return", "collection scenario"),
    ),
    (
        "Medical-waste vehicle operations",
        ("medical waste", "vehicle", "route assumption", "handling checklist"),
    ),
    (
        "Drone systems",
        ("drone", "flight", "coverage model", "inspection use case"),
    ),
    (
        "Publishing workflow",
        ("publishing", "release checklist", "validation rule", "link check"),
    ),
)


TYPE_BY_EXTENSION = {
    ".csv": "Structured data",
    ".json": "Structured data",
    ".tsv": "Structured data",
    ".py": "Source code",
    ".js": "Source code",
    ".ts": "Source code",
    ".tsx": "Source code",
    ".html": "Source code",
    ".css": "Source code",
    ".md": "Document",
    ".txt": "Document",
    ".pdf": "Document",
    ".docx": "Document",
    ".pptx": "Presentation",
    ".key": "Presentation",
    ".png": "Image",
    ".jpg": "Image",
    ".jpeg": "Image",
    ".svg": "Image",
    ".zip": "Archive",
    ".tar": "Archive",
    ".gz": "Archive",
}


def _normalise_words(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def classify_project(relative_path: str) -> str:
    """Classify a path with transparent filename/path keyword rules."""

    words = _normalise_words(relative_path)
    for label, needles in PROJECT_RULES:
        if any(needle in words for needle in needles):
            return label
    return "Cross-project / General"


def classify_asset_type(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.casefold()
    return TYPE_BY_EXTENSION.get(suffix, "Other")


def classify_lifecycle(relative_path: str) -> str:
    """Return a filename-derived hint; never treat it as authoritative status."""

    words = set(_normalise_words(relative_path).split())
    if words.intersection({"archive", "archived", "backup", "old", "obsolete"}):
        return "Archive/backup hint"
    if words.intersection({"temp", "tmp", "draft", "wip", "review", "copy"}):
        return "Working-copy hint"
    if words.intersection({"final", "approved", "published", "release"}):
        return "Final/release hint"
    return "No status hint"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_for_path(root: Path, path: Path) -> AssetRecord:
    relative = path.relative_to(root).as_posix()
    try:
        stat = path.stat()
        size = stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    except OSError as exc:
        return AssetRecord(
            relative_path=relative,
            extension=path.suffix.casefold(),
            size_bytes=None,
            modified_utc="",
            sha256="",
            project=classify_project(relative),
            asset_type=classify_asset_type(relative),
            lifecycle_hint=classify_lifecycle(relative),
            read_error=f"metadata: {type(exc).__name__}: {exc}",
        )

    try:
        digest = sha256_file(path)
        error = ""
    except OSError as exc:
        digest = ""
        error = f"content: {type(exc).__name__}: {exc}"

    return AssetRecord(
        relative_path=relative,
        extension=path.suffix.casefold(),
        size_bytes=size,
        modified_utc=modified,
        sha256=digest,
        project=classify_project(relative),
        asset_type=classify_asset_type(relative),
        lifecycle_hint=classify_lifecycle(relative),
        read_error=error,
    )


def _canonical_rank(record: AssetRecord) -> tuple[int, int, str]:
    """Prefer paths without working/archive hints, then shorter paths."""

    penalty = {
        "No status hint": 0,
        "Final/release hint": 0,
        "Working-copy hint": 1,
        "Archive/backup hint": 2,
    }.get(record.lifecycle_hint, 3)
    return penalty, len(record.relative_path), record.relative_path.casefold()


def assign_duplicate_groups(records: list[AssetRecord]) -> None:
    """Annotate exact-content duplicate groups in place."""

    by_digest: dict[str, list[AssetRecord]] = defaultdict(list)
    for record in records:
        if record.sha256:
            by_digest[record.sha256].append(record)

    groups = [group for group in by_digest.values() if len(group) > 1]
    groups.sort(key=lambda group: min(item.relative_path.casefold() for item in group))
    for index, group in enumerate(groups, start=1):
        group_id = f"DUP-{index:03d}"
        canonical = min(group, key=_canonical_rank)
        for record in sorted(group, key=lambda item: item.relative_path.casefold()):
            record.duplicate_group = group_id
            if record is not canonical:
                record.duplicate_of = canonical.relative_path


def _counter_dict(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items(), key=lambda item: item[0].casefold()))


def build_summary(records: list[AssetRecord]) -> dict[str, object]:
    readable = [record for record in records if record.sha256 and not record.read_error]
    duplicate_groups = sorted(
        {record.duplicate_group for record in records if record.duplicate_group}
    )
    redundant = [record for record in records if record.duplicate_of]
    review_items = [
        record
        for record in records
        if record.read_error
        or record.duplicate_of
        or record.lifecycle_hint in {"Working-copy hint", "Archive/backup hint"}
    ]
    return {
        "files_discovered": len(records),
        "files_readable": len(readable),
        "files_with_errors": sum(bool(record.read_error) for record in records),
        "total_bytes": sum(record.size_bytes or 0 for record in records),
        "unique_content_hashes": len({record.sha256 for record in readable}),
        "exact_duplicate_groups": len(duplicate_groups),
        "redundant_exact_copies": len(redundant),
        "potential_duplicate_bytes": sum(record.size_bytes or 0 for record in redundant),
        "review_queue_items": len(review_items),
        "counts_by_project": _counter_dict(record.project for record in records),
        "counts_by_asset_type": _counter_dict(record.asset_type for record in records),
        "counts_by_lifecycle_hint": _counter_dict(
            record.lifecycle_hint for record in records
        ),
        "counts_by_extension": _counter_dict(
            record.extension or "[no extension]" for record in records
        ),
    }


def audit_directory(root: Path) -> AuditResult:
    supplied_root = Path(root)
    display_root = supplied_root.as_posix()
    root = supplied_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Audit root is not a directory: {display_root}")

    records: list[AssetRecord] = []
    paths = sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix().casefold(),
    )
    for path in paths:
        if path.is_symlink():
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                records.append(
                    AssetRecord(
                        relative_path=relative,
                        extension=path.suffix.casefold(),
                        size_bytes=None,
                        modified_utc="",
                        sha256="",
                        project=classify_project(relative),
                        asset_type=classify_asset_type(relative),
                        lifecycle_hint=classify_lifecycle(relative),
                        read_error="content: symlink skipped",
                    )
                )
            continue
        if path.is_file():
            records.append(_record_for_path(root, path))

    assign_duplicate_groups(records)
    # Preserve the caller-supplied label in outputs. This avoids needlessly
    # publishing workstation usernames when a relative audit root is used.
    return AuditResult(root=display_root, records=records, summary=build_summary(records))


def _format_bytes(value: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    amount = float(value)
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{value} B"


def _escape_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _markdown_counts(title: str, counts: dict[str, int]) -> list[str]:
    rows = [f"### {title}", "", "| Category | Files |", "|---|---:|"]
    rows.extend(f"| {_escape_cell(label)} | {count} |" for label, count in counts.items())
    return rows


def render_report(
    result: AuditResult,
    *,
    title: str,
    provenance: str,
    generated_at_utc: str,
) -> str:
    summary = result.summary
    lines = [
        f"# {title}",
        "",
        f"Generated: {generated_at_utc}",
        "",
        "## Scope and provenance",
        "",
        provenance,
        "",
        f"Audited root: `{result.root}`",
        "",
        "## Executive summary",
        "",
        "| Measure | Result |",
        "|---|---:|",
        f"| Files discovered | {summary['files_discovered']} |",
        f"| Readable files | {summary['files_readable']} |",
        f"| Files with read errors | {summary['files_with_errors']} |",
        f"| Total size | {_format_bytes(int(summary['total_bytes']))} |",
        f"| Unique content hashes | {summary['unique_content_hashes']} |",
        f"| Exact-duplicate groups | {summary['exact_duplicate_groups']} |",
        f"| Redundant exact copies | {summary['redundant_exact_copies']} |",
        f"| Potential duplicate bytes | {_format_bytes(int(summary['potential_duplicate_bytes']))} |",
        f"| Items in review queue | {summary['review_queue_items']} |",
        "",
    ]
    lines.extend(_markdown_counts("Project view", summary["counts_by_project"]))
    lines.append("")
    lines.extend(_markdown_counts("Asset-type view", summary["counts_by_asset_type"]))
    lines.extend(
        [
            "",
            "## Exact duplicates",
            "",
            "Exact duplicates share a SHA-256 hash. The suggested representative is",
            "selected by a transparent path heuristic; it is not an authorization to delete files.",
            "",
        ]
    )
    duplicates = [record for record in result.records if record.duplicate_of]
    if duplicates:
        lines.extend(
            [
                "| Group | Suggested representative | Redundant copy | Size |",
                "|---|---|---|---:|",
            ]
        )
        for record in duplicates:
            lines.append(
                "| {group} | `{canonical}` | `{duplicate}` | {size} |".format(
                    group=record.duplicate_group,
                    canonical=_escape_cell(record.duplicate_of),
                    duplicate=_escape_cell(record.relative_path),
                    size=_format_bytes(record.size_bytes or 0),
                )
            )
    else:
        lines.append("No exact duplicates were found.")

    review = [
        record
        for record in result.records
        if record.read_error
        or record.duplicate_of
        or record.lifecycle_hint in {"Working-copy hint", "Archive/backup hint"}
    ]
    lines.extend(
        [
            "",
            "## Human review queue",
            "",
            "| Path | Reason |",
            "|---|---|",
        ]
    )
    for record in review:
        reasons = []
        if record.read_error:
            reasons.append(record.read_error)
        if record.duplicate_of:
            reasons.append(f"exact duplicate of {record.duplicate_of}")
        if record.lifecycle_hint in {"Working-copy hint", "Archive/backup hint"}:
            reasons.append(record.lifecycle_hint)
        lines.append(
            f"| `{_escape_cell(record.relative_path)}` | {_escape_cell('; '.join(reasons))} |"
        )
    if not review:
        lines.append("| — | No heuristic review items |")

    lines.extend(
        [
            "",
            "## Interpretation boundaries",
            "",
            "- Duplicate detection is byte-for-byte only; similar or revised documents are not grouped.",
            "- Project, asset-type, and lifecycle labels are filename/path heuristics.",
            "- A hash match indicates identical bytes, not that a file is safe to remove.",
            "- File ownership, retention obligations, business value, and access rights require human review.",
            "- Unreadable files remain visible as exceptions rather than silently disappearing.",
            "",
            "## Output guide",
            "",
            "- `inventory.csv`: one row per discovered file",
            "- `duplicates.csv`: one row per redundant exact copy",
            "- `review_queue.csv`: exception and filename-risk review list",
            "- `summary.json`: machine-readable metrics and provenance",
            "- `report.md`: this human-readable decision-support report",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_outputs(
    result: AuditResult,
    output_dir: Path,
    *,
    title: str = "Knowledge-Asset Audit",
    provenance: str = "Provenance was not supplied; confirm data handling before sharing.",
    generated_at_utc: str | None = None,
) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at_utc = generated_at_utc or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()

    inventory_path = output_dir / "inventory.csv"
    fieldnames = [field.name for field in AssetRecord.__dataclass_fields__.values()]
    with inventory_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(record) for record in result.records)

    duplicates_path = output_dir / "duplicates.csv"
    with duplicates_path.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = [
            "duplicate_group",
            "suggested_representative",
            "redundant_copy",
            "size_bytes",
            "sha256",
        ]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record in result.records:
            if record.duplicate_of:
                writer.writerow(
                    {
                        "duplicate_group": record.duplicate_group,
                        "suggested_representative": record.duplicate_of,
                        "redundant_copy": record.relative_path,
                        "size_bytes": record.size_bytes,
                        "sha256": record.sha256,
                    }
                )

    review_path = output_dir / "review_queue.csv"
    with review_path.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = ["relative_path", "reason", "suggested_action"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record in result.records:
            reasons = []
            if record.read_error:
                reasons.append(record.read_error)
            if record.duplicate_of:
                reasons.append(f"exact duplicate of {record.duplicate_of}")
            if record.lifecycle_hint in {"Working-copy hint", "Archive/backup hint"}:
                reasons.append(record.lifecycle_hint)
            if reasons:
                writer.writerow(
                    {
                        "relative_path": record.relative_path,
                        "reason": "; ".join(reasons),
                        "suggested_action": "Review with the asset owner; do not auto-delete.",
                    }
                )

    summary_path = output_dir / "summary.json"
    summary_document = {
        "title": title,
        "generated_at_utc": generated_at_utc,
        "audited_root": result.root,
        "provenance": provenance,
        "method": {
            "duplicate_detection": "Exact SHA-256 content match",
            "classification": "Deterministic filename/path and extension rules",
            "symlink_policy": "Skip and report file symlinks",
        },
        "summary": result.summary,
    }
    summary_path.write_text(
        json.dumps(summary_document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report_path = output_dir / "report.md"
    report_path.write_text(
        render_report(
            result,
            title=title,
            provenance=provenance,
            generated_at_utc=generated_at_utc,
        ),
        encoding="utf-8",
    )

    return {
        "inventory": inventory_path,
        "duplicates": duplicates_path,
        "review_queue": review_path,
        "summary": summary_path,
        "report": report_path,
    }
