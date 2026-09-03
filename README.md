# Knowledge-Asset Audit Demo

A portable, clean-room demonstration of how a scattered file collection can be
turned into a reviewable knowledge-asset inventory. The tool discovers files,
computes SHA-256 hashes, detects exact duplicates, applies transparent
classifications, creates a human review queue, and writes both machine-readable
and executive-friendly reports.

> **Portfolio safety:** this repository contains only fictional data and new,
> clean-room code. It includes no employer files or code, no internal prompts or
> manuscripts, and no customer, partner, employee, or analytics data.

## Why this project exists

Knowledge-heavy teams often inherit shared drives containing useful work mixed
with drafts, backups, renamed copies, and unclear folder structures. Before a
migration, archive, or cleanup, decision-makers need a defensible map of what is
present—and a way to surface exceptions without automatically deleting anything.

This demonstration turns that problem into a reproducible workflow:

```text
Synthetic files
      |
      v
Discovery -> metadata -> SHA-256 hashing -> deterministic classification
      |                                            |
      +---------------- exact-match groups --------+
                                                   v
                             inventory + review queue + report
```

## What it demonstrates

- Recursive inventory with portable relative paths
- Streaming SHA-256 hashing for exact-content duplicate detection
- Deterministic project, asset-type, and lifecycle-hint classifications
- A conservative representative-file heuristic for duplicate groups
- Explicit read-error handling so exceptions do not silently disappear
- CSV outputs for analysis, JSON for integration, and Markdown for decisions
- Safe handling: the tool never deletes, moves, or modifies audited files
- Reproducible synthetic inputs and dependency-free automated tests

The supplied corpus represents four fictional workstreams—self-injectable
medicine returns, medical-waste vehicle operations, drone systems, and a
publishing workflow—plus shared strategy and finance material. These names are
high-level portfolio themes only; every file and every value is invented.

## Quick start

Requires Python 3.10 or newer. No third-party packages are needed.

```bash
python -m knowledge_audit generate sample_data
python -m knowledge_audit audit sample_data sample_output \
  --title "Synthetic Knowledge-Asset Audit" \
  --synthetic
```

On PowerShell, the audit command can be entered on one line:

```powershell
python -m knowledge_audit audit sample_data sample_output --title "Synthetic Knowledge-Asset Audit" --synthetic
```

To regenerate known synthetic inputs, add `--overwrite`. The generator replaces
only its known files and never deletes unrelated files.

## Outputs

| File | Purpose |
|---|---|
| `inventory.csv` | File metadata, hash, classifications, duplicate annotations, and errors |
| `duplicates.csv` | Suggested representative and redundant paths for exact-match groups |
| `review_queue.csv` | Duplicate, draft/archive-name, and read-error exceptions for a human owner |
| `summary.json` | Metrics, provenance, and method description for downstream use |
| `report.md` | Decision-support report with scope, counts, duplicate groups, and boundaries |

Committed examples are available in [`sample_data`](sample_data) and
[`sample_output`](sample_output). Their timestamps and content are synthetic.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover classification rules, collision-safe data generation, expected
duplicate groups, canonical-file selection, and the integrity of all report
formats.

## Design decisions

**Exact matches only.** SHA-256 identifies files with identical bytes. It does
not imply that differently formatted or slightly revised documents are related.
This keeps the result explainable and avoids overstating similarity.

**No automated cleanup.** A duplicate is evidence for review, not authorization
to delete. Retention duties, ownership, business context, and access rules need
a human decision.

**Filename-derived status is only a hint.** Words such as `draft`, `backup`, and
`final` help prioritize review, but filenames cannot establish approval status.

**Symlinks are skipped.** Following a link could make a scan escape the intended
root. File symlinks are reported as exceptions instead.

## Limitations and production extensions

This demonstration does not extract document text, detect near-duplicates,
inspect permissions, apply retention schedules, or connect to cloud drives. A
production implementation could add MIME detection, OCR, document fingerprints,
owner-approved taxonomy rules, access-control review, and a governed remediation
workflow. Those additions should follow the organization's privacy, security,
legal, and records-management requirements.

## Role and AI disclosure

Ted Kang defined the problem, audit boundaries, output requirements, and review
controls, and accepted responsibility for the portfolio presentation. AI
assistance accelerated implementation, documentation, testing, and review. See
[`AI_ASSISTANCE.md`](AI_ASSISTANCE.md) for the full disclosure.

## License

Code is released under the [MIT License](LICENSE). The synthetic sample data may
also be used under the same terms.
