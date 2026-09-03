"""Deterministic synthetic input generation for the portfolio demonstration."""

from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path


FIXED_TIMESTAMP = 1_768_435_200  # 2026-01-15 00:00:00 UTC


LANDSCAPE_NOTES = b"""# Synthetic collection landscape\n\nThis fictional note compares pharmacy drop-off, mail-back, and scheduled\ncollection concepts for a hypothetical self-injectable medicine return model.\nNo organization, customer, patient, or market data is represented.\n"""

COLLECTION_SCENARIOS = b"""scenario,sites,pickups_per_month,units_per_pickup\nPilot A,8,2,35\nPilot B,20,4,50\nPilot C,45,4,70\n"""

PORTFOLIO_MAP = b"""# Synthetic project portfolio map\n\n- Self-injectable medicine return model: concept research\n- Medical-waste vehicle operations: routing assumptions\n- Drone systems: inspection learning model\n- Publishing workflow: quality-control demonstration\n+"""


def _deterministic_zip() -> bytes:
    """Return a small valid ZIP with stable bytes and metadata."""

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        entry = zipfile.ZipInfo("README.txt", date_time=(2026, 1, 15, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o644 << 16
        archive.writestr(
            entry,
            "Synthetic archive retained only to exercise asset-type classification.\n",
        )
    return stream.getvalue()


def synthetic_files() -> dict[str, bytes]:
    """Return the complete deterministic demo corpus as relative-path bytes."""

    files: dict[str, bytes] = {
        "README_SYNTHETIC.txt": (
            "SYNTHETIC DATA ONLY\n"
            "This generated corpus contains fictional examples and no company data.\n"
        ).encode("utf-8"),
        "01_self_injection_return_model/research/landscape_notes.md": LANDSCAPE_NOTES,
        "01_self_injection_return_model/research/landscape_notes - Copy.md": LANDSCAPE_NOTES,
        "01_self_injection_return_model/analysis/collection_scenarios.csv": COLLECTION_SCENARIOS,
        "01_self_injection_return_model/analysis/collection_scenarios_backup.csv": COLLECTION_SCENARIOS,
        "01_self_injection_return_model/deliverables/concept_brief_draft.md": (
            "# Draft concept brief\n\n"
            "Fictional working draft: compare return channels, stakeholders, and pilot gates.\n"
        ).encode("utf-8"),
        "01_self_injection_return_model/deliverables/concept_brief_final.md": (
            "# Final synthetic concept brief\n\n"
            "Recommendation: validate assumptions with a small, permissioned pilot before scale-up.\n"
        ).encode("utf-8"),
        "02_medical_waste_vehicle/compliance/handling_checklist.md": (
            "# Synthetic handling checklist\n\n"
            "- Confirm applicable rules with qualified personnel.\n"
            "- Separate incompatible materials.\n"
            "- Record custody events and exceptions.\n"
            "- Stop work when a safety condition is uncertain.\n"
        ).encode("utf-8"),
        "02_medical_waste_vehicle/operations/route_assumptions.csv": (
            "route,stops,distance_km,service_minutes_per_stop\n"
            "North,12,38,14\nSouth,9,31,16\n"
        ).encode("utf-8"),
        "02_medical_waste_vehicle/operations/route_assumptions_v2.csv": (
            "route,stops,distance_km,service_minutes_per_stop\n"
            "North,12,36,14\nSouth,10,33,15\n"
        ).encode("utf-8"),
        "02_medical_waste_vehicle/deliverables/vehicle_model_summary_final.md": (
            "# Synthetic vehicle model\n\n"
            "A fictional scenario model connects pickup density, service time, and routing capacity.\n"
        ).encode("utf-8"),
        "03_drone_systems/research/inspection_use_cases.md": (
            "# Synthetic drone inspection use cases\n\n"
            "Candidate learning scenarios include visual coverage mapping and anomaly triage.\n"
            "This is not a flight plan or operational safety document.\n"
        ).encode("utf-8"),
        "03_drone_systems/technical/coverage_model.py": (
            "\"\"\"Tiny synthetic coverage calculation; not flight-control software.\"\"\"\n\n"
            "def coverage_ratio(observed: int, total: int) -> float:\n"
            "    if total <= 0:\n"
            "        raise ValueError(\"total must be positive\")\n"
            "    return max(0.0, min(1.0, observed / total))\n"
        ).encode("utf-8"),
        "03_drone_systems/technical/sample_flight_data.json": json.dumps(
            {
                "synthetic": True,
                "mission_id": "DEMO-001",
                "observations": [
                    {"segment": "A", "coverage": 0.82},
                    {"segment": "B", "coverage": 0.91},
                ],
            },
            indent=2,
        ).encode("utf-8")
        + b"\n",
        "03_drone_systems/deliverables/drone_program_brief_final.md": (
            "# Synthetic drone program brief\n\n"
            "Decision gate: proceed only after safety, regulatory, and data-quality review.\n"
        ).encode("utf-8"),
        "04_publishing_workflow/docs/workflow_overview.md": (
            "# Synthetic publishing workflow\n\n"
            "Structured source -> build -> format checks -> visual review -> release manifest.\n"
        ).encode("utf-8"),
        "04_publishing_workflow/qa/validation_rules.json": json.dumps(
            {
                "synthetic": True,
                "checks": ["required_sections", "link_format", "output_manifest"],
            },
            indent=2,
        ).encode("utf-8")
        + b"\n",
        "04_publishing_workflow/tools/link_check_stub.py": (
            "\"\"\"Synthetic placeholder showing an interface, with no network access.\"\"\"\n\n"
            "def is_http_url(value: str) -> bool:\n"
            "    return value.startswith((\"https://\", \"http://\"))\n"
        ).encode("utf-8"),
        "04_publishing_workflow/outputs/release_checklist_final.txt": (
            "SYNTHETIC RELEASE CHECKLIST\n"
            "[x] Inputs identified\n[x] Automated checks passed\n[x] Human review recorded\n"
        ).encode("utf-8"),
        "05_cross_project/finance/budget_template.csv": (
            "workstream,amount_usd,confidence\nResearch,12000,illustrative\nPilot,28000,illustrative\n"
        ).encode("utf-8"),
        "05_cross_project/strategy/portfolio_map.md": PORTFOLIO_MAP,
        "05_cross_project/archive/portfolio_map_backup.md": PORTFOLIO_MAP,
        "05_cross_project/temp/meeting_notes_temp.txt": (
            "Synthetic temporary note. Decisions are not approved and names are fictional.\n"
        ).encode("utf-8"),
        "05_cross_project/empty_placeholder.txt": b"",
        "05_cross_project/archive/prior_demo_bundle.zip": _deterministic_zip(),
    }
    return files


def generate_synthetic_dataset(target: Path, *, overwrite: bool = False) -> list[Path]:
    """Write the synthetic corpus without deleting unrelated files.

    Existing generated paths are replaced only when ``overwrite`` is true. The
    function deliberately never removes the target directory or extra files.
    """

    target = Path(target)
    files = synthetic_files()
    collisions = [target / relative for relative in files if (target / relative).exists()]
    if collisions and not overwrite:
        preview = ", ".join(str(path) for path in collisions[:3])
        raise FileExistsError(
            f"Refusing to replace {len(collisions)} existing generated file(s): {preview}"
        )

    written: list[Path] = []
    for relative, payload in files.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        os.utime(destination, (FIXED_TIMESTAMP, FIXED_TIMESTAMP))
        written.append(destination)
    return written
