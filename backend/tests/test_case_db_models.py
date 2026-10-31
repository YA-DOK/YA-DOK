"""Metadata-only tests: they do not require or modify any running database."""
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from app.models.case import ClinicalCase, CaseVersion, CaseAsset


def test_three_storage_models_use_same_metadata():
    assert {m.__tablename__ for m in (ClinicalCase, CaseVersion, CaseAsset)} == {
        "cases", "case_versions", "case_assets"
    }
    assert len({id(m.metadata) for m in (ClinicalCase, CaseVersion, CaseAsset)}) == 1


def test_blueprint_is_stored_as_postgresql_jsonb():
    assert isinstance(CaseVersion.__table__.c.blueprint.type, JSONB)
    assert "JSONB" in str(CreateTable(CaseVersion.__table__).compile(dialect=postgresql.dialect()))


def test_versions_must_be_unique_per_case():
    constraints = CaseVersion.__table__.constraints
    assert any(isinstance(c, UniqueConstraint) and {x.name for x in c.columns} == {"case_id", "version_number"} for c in constraints)


def test_published_pointer_cannot_target_another_case():
    constraints = ClinicalCase.__table__.constraints
    assert any(isinstance(c, ForeignKeyConstraint) and c.name == "fk_cases_published_version" and {x.name for x in c.columns} == {"id", "published_version_number"} for c in constraints)


def test_assets_are_private_storage_references():
    cols = CaseAsset.__table__.c.keys()
    assert "storage_path" in cols
    assert "public_url" not in cols
