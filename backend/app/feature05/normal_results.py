
"""Synthetic normal results for non-indicated investigations.

These results are used for educational simulation only.
They are not actual patient findings and must not be saved
back into the original case Blueprint.

Numeric values require clinically reviewed reference ranges.
"""

from __future__ import annotations

from typing import Any


NORMAL_LAB_CATEGORIES = frozenset({
    "laboratory",
    "urinalysis",
    "microbiology",
    "hormones",
})

CARDIAC_BIOMARKERS = frozenset({
    "troponin_i",
    "troponin_t",
    "bnp",
    "ck_mb",
})


def build_normal_training_result(
    *,
    investigation_id: str,
    category: str,
) -> dict[str, Any] | None:
    """Build a qualitative normal result for supported tests."""

    is_supported_lab = category in NORMAL_LAB_CATEGORIES

    is_cardiac_biomarker = (
        category == "cardiac"
        and investigation_id in CARDIAC_BIOMARKERS
    )

    if not is_supported_lab and not is_cardiac_biomarker:
        return None

    if category == "microbiology":
        finding = (
            "Negative / no pathogen detected "
            "(simulated training result)."
        )
    else:
        finding = (
            "Within normal reference range "
            "(simulated training result)."
        )

    return {
        "findings": finding,
        "measurements": [],
        "simulated_normal": True,
        "result_type": "synthetic_qualitative_normal",
        "release_delay_seconds": 0,
        "reference_range_note": (
            "Numeric reference ranges require test-specific, "
            "age-appropriate, clinician-reviewed templates."
        ),
    }
