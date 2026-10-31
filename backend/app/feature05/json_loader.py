
import json
import re
from pathlib import Path
from copy import deepcopy


DATA_PATH = Path(__file__).resolve().parent / "Data" / "cases"


# Educational ranges only.
# The source Blueprint does not confirm CBC units.
CBC_REFERENCE_RANGES = {
    "wbc": ("WBC", "x10^9/L", "4.5 - 13.5"),
    "hemoglobin": ("Hemoglobin", "g/dL", "11.5 - 15.5"),
    "rbc": ("RBC", "x10^12/L", "4.0 - 5.2"),
    "platelets": ("Platelets", "x10^9/L", "150 - 450"),
}


def find_timeline_event(timeline, event_type):
    return next(
        (
            event for event in timeline
            if event.get("event_type") == event_type
        ),
        {},
    )


def make_measurement(
    name,
    value,
    source_page=None,
    confidence="not_verified",
    unit=None,
    reference_range=None,
    unit_source=None,
):
    return {
        "name": name,
        "value": str(value),
        "unit": unit,
        "reference_range": reference_range,
        "source_page": source_page,
        "confidence": confidence,
        "unit_source": unit_source,
    }


def build_cbc_result(labs):
    crosscheck = labs.get("flow_sheet_crosscheck", {})
    measurements = []

    for field, details in CBC_REFERENCE_RANGES.items():
        if crosscheck.get(field) is None:
            continue

        name, unit, reference_range = details

        measurements.append(
            make_measurement(
                name=name,
                value=crosscheck[field],
                source_page=crosscheck.get("source_page"),
                confidence="crosscheck_unit_not_specified",
                unit=unit,
                reference_range=reference_range,
                unit_source="Educational assumption, not source-confirmed",
            )
        )

    if not measurements:
        return None

    return {
        "findings": "CBC values from the case Blueprint.",
        "measurements": measurements,
        "reference_range_note": (
            "Approximate pediatric educational ranges. "
            "Units are assumed and require verification."
        ),
        "source_page": crosscheck.get("source_page"),
        "source_notes": {
            "flow_sheet_crosscheck": deepcopy(crosscheck),
            "alternative_readings": deepcopy(
                labs.get("hematology", {})
            ),
        },
    }


def build_crp_result(labs):
    inflammatory = labs.get("inflammatory_markers", {})

    if inflammatory.get("crp_result") is None:
        return None

    return {
        "findings": inflammatory["crp_result"],
        "measurements": [],
        "result_type": "qualitative",
        "confidence": inflammatory.get("confidence"),
        "source_page": inflammatory.get("source_page"),
        "note": "Original Blueprint result; confidence preserved.",
    }


def build_chemistry_results(labs):
    series = labs.get("chemistry_series", [])

    if not series:
        return {}

    # These are partial results, not complete BMP/CMP panels.
    # Only map tests supported by the Blueprint fields.
    first_record = series[0]
    source = first_record.get("source_page")

    results = {}

    electrolyte_fields = [
        ("sodium", "Sodium"),
        ("potassium", "Potassium"),
        ("calcium", "Calcium"),
    ]

    electrolyte_measurements = []

    for key, label in electrolyte_fields:
        if first_record.get(key) is not None:
            electrolyte_measurements.append(
                make_measurement(
                    name=label,
                    value=first_record[key],
                    source_page=source,
                    confidence="source_value_unit_unverified",
                )
            )

    if electrolyte_measurements:
        results["electrolytes"] = {
            "findings": "Partial electrolyte values from Blueprint.",
            "measurements": electrolyte_measurements,
            "source_page": source,
            "note": (
                "Original units and reference ranges are "
                "not confirmed. Values are not interpreted."
            ),
        }

    lactate_value = first_record.get(
        "Lactic Acid",
        first_record.get("lactate"),
    )

    if lactate_value is not None:
        results["lactate"] = {
            "findings": "Lactate value from Blueprint.",
            "measurements": [
                make_measurement(
                    name="Lactate",
                    value=lactate_value,
                    source_page=source,
                    confidence="source_value_unit_unverified",
                )
            ],
            "source_page": source,
            "note": "Unit and reference range not confirmed.",
        }

    return results


def build_blood_gas_result(labs):
    gas = labs.get("blood_gas", {})

    fields = [
        ("ph", "pH", None),
        ("pco2_mmHg", "PCO2", "mmHg"),
        ("po2_mmHg", "PO2", "mmHg"),
    ]

    measurements = []

    for field, name, unit in fields:
        if gas.get(field) is not None:
            measurements.append(
                make_measurement(
                    name=name,
                    value=gas[field],
                    unit=unit,
                    source_page=gas.get("source_page"),
                    confidence=gas.get("confidence", "best_guess"),
                )
            )

    if not measurements:
        return None

    return {
        "findings": "Blood gas readings from Blueprint.",
        "measurements": measurements,
        "confidence": gas.get("confidence", "best_guess"),
        "source_page": gas.get("source_page"),
        "note": (
            "Uncertain readings require verification. "
            "No reference ranges are assigned."
        ),
    }


def build_vitals_result(blueprint):
    vitals = blueprint.get("vitals_trend", {})
    readings = vitals.get("readings", [])

    fields = [
        ("Temperature", "C"),
        ("Respiratory Rate", "breaths/min"),
        ("Pulse Rate", "beats/min"),
    ]

    measurements = []

    # Mapping follows the supplied unit_notes order.
    # The source does not confidently establish a time trend.
    for index, (name, unit) in enumerate(fields):
        if index < len(readings):
            measurements.append(
                make_measurement(
                    name=name,
                    value=readings[index],
                    unit=unit,
                    source_page=vitals.get("source_page"),
                    confidence="inferred_from_readings_order",
                )
            )

    return {
        "measurements": measurements,
        "raw_readings": deepcopy(readings),
        "readings_note": vitals.get("readings_note"),
        "unit_notes": vitals.get("unit_notes"),
        "trend_summary": vitals.get("trend_summary"),
        "source_page": vitals.get("source_page"),
    }


def adapt_blueprint(case_id, blueprint):
    identity = blueprint.get("identity", {})
    presenting = blueprint.get("presenting_problem", {})
    timeline = blueprint.get("clinical_timeline", [])
    labs = blueprint.get("labs_trend", {})
    treatment = blueprint.get("treatment", {})
    encounter = blueprint.get("encounter", {})
    outcome = blueprint.get("outcome_summary", {})

    admission = find_timeline_event(
        timeline, "admission_exam"
    )
    imaging = find_timeline_event(
        timeline, "imaging"
    )

    vitals = build_vitals_result(blueprint)
    imaging_findings = imaging.get("findings", {})

    results = {}

    # General physical examination
    if vitals["measurements"]:
        results["general_exam"] = {
            "findings": "Available admission vital-sign observations.",
            "measurements": vitals["measurements"],
            "source_page": vitals.get("source_page"),
            "note": vitals.get("readings_note"),
        }

    # Respiratory clinical examination
    if admission.get("findings"):
        results["respiratory_exam"] = {
            "findings": deepcopy(admission["findings"]),
            "measurements": [],
            "confidence": admission.get("findings_confidence"),
            "source_page": admission.get("source_page"),
        }

    cbc = build_cbc_result(labs)
    if cbc is not None:
        results["cbc"] = cbc

    crp = build_crp_result(labs)
    if crp is not None:
        results["crp"] = crp

    # Electrolytes and lactate only.
    # An incomplete chemistry series is not a full BMP or CMP.
    results.update(build_chemistry_results(labs))

    blood_gas = build_blood_gas_result(labs)
    if blood_gas is not None:
        results["blood_gas"] = blood_gas

    if imaging_findings.get("result") is not None:
        xray_result = {
            "findings": imaging_findings.get("result"),
            "measurements": [],
            "modality": imaging_findings.get("modality"),
            "body_part": imaging_findings.get("body_part"),
            "performed_at": imaging_findings.get("performed_at"),
            "confidence": imaging.get("findings_confidence"),
            "source_page": imaging.get("source_page"),
        }

        # Explicit synthetic educational image for case_002.
        # Do not automatically reuse it for future cases.
        if case_id == "case_002":
            xray_result["image_path"] = (
                "Data/medical_images/"
                "xray_case_002_synthetic.png"
            )
            xray_result["image_type"] = (
                "synthetic_educational_illustration"
            )

        results["chest_xray"] = xray_result

    # The available list describes configured case results.
    # It does NOT restrict the universal catalog.
    available = list(results.keys())

    relevance = {}
    for investigation_id in available:
        relevance[investigation_id] = {
            "relevance": (
                "essential"
                if investigation_id in (
                    "general_exam",
                    "respiratory_exam",
                )
                else "relevant"
            ),
            "penalty": 0,
        }

    return {
        "id": case_id,
        "title": blueprint.get(
            "title",
            "Clinical Case",
        ),
        "description": presenting.get("chief_complaint", ""),
        "patient": {
            "age": identity.get("age"),
            "sex": identity.get("sex"),
            "weight_kg": identity.get("weight_kg"),
            "source_page": identity.get("source_page"),
        },
        "encounter": deepcopy(encounter),
        "chief_complaint": presenting.get("chief_complaint"),
        "chief_complaint_confidence": presenting.get(
            "chief_complaint_confidence"
        ),
        "present_history": presenting.get("present_history"),
        "medical_history": presenting.get("present_history"),
        "presenting_problem_source_page": presenting.get(
            "source_page"
        ),
        "working_diagnosis": imaging_findings.get("result"),
        "clinical_timeline": deepcopy(timeline),
        "vitals_trend": vitals,
        "labs_trend": deepcopy(labs),
        "treatment": deepcopy(treatment),
        "outcome_summary": deepcopy(outcome),
        "available_investigations": available,
        "investigation_results": results,
        "educational_relevance": relevance,
        "default_unnecessary_penalty": 0,
        "blueprint_source": deepcopy(blueprint),
        "educational_configuration_note": (
            "Investigation relevance is a simulation setting, "
            "not an original clinical finding."
        ),
    }


def get_case_by_id(case_id: str):
    if (
        not isinstance(case_id, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]+", case_id)
    ):
        return None

    path = DATA_PATH / f"{case_id}.json"

    if not path.is_file():
        return None

    with path.open("r", encoding="utf-8") as file:
        case_data = json.load(file)

    # Existing Feature 05 cases remain unchanged.
    if "available_investigations" in case_data:
        if case_data.get("id") != case_id:
            raise ValueError("Case ID does not match filename")
        return case_data

    # Adapt original clinical Blueprint.
    return adapt_blueprint(case_id, case_data)
