from .catalog import get_investigation_by_id


def validate_case_investigations(case_data):
    errors = []

    available = case_data.get("available_investigations", [])
    results = case_data.get("investigation_results", {})

    for investigation_id in available:
        if get_investigation_by_id(investigation_id) is None:
            errors.append(
                f"Unknown investigation: {investigation_id}"
            )

        if investigation_id not in results:
            errors.append(
                f"Missing result: {investigation_id}"
            )

    for investigation_id in results:
        if investigation_id not in available:
            errors.append(
                f"Result for unavailable investigation: {investigation_id}"
            )

    return errors