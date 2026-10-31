
import json
from pathlib import Path

from .schemas import InvestigationItem, InvestigationCategory


CATALOG_PATH = (
    Path(__file__).resolve().parent
    / "Data"
    / "catalog"
    / "investigations.json"
)


def get_all_investigations():
    if not CATALOG_PATH.is_file():
        raise FileNotFoundError(
            f"Investigation catalog not found: {CATALOG_PATH}"
        )

    with CATALOG_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Catalog must contain a JSON list")

    investigations = [
        InvestigationItem.model_validate(item)
        for item in data
    ]

    ids = [item.id for item in investigations]

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate investigation IDs found")

    return investigations


def get_investigation_by_id(investigation_id: str):
    for investigation in get_all_investigations():
        if investigation.id == investigation_id:
            return investigation

    return None


def search_investigations(query: str = "", category=None):
    query = (query or "").strip().lower()

    if isinstance(category, InvestigationCategory):
        category = category.value

    if category:
        category = str(category).strip().lower()

    results = []

    for investigation in get_all_investigations():
        searchable = " ".join([
            investigation.id,
            investigation.name,
            investigation.description or "",
            investigation.subcategory or "",
            investigation.category.value
        ]).lower()

        if query and query not in searchable:
            continue

        if category and investigation.category.value != category:
            continue

        results.append(investigation)

    return results
