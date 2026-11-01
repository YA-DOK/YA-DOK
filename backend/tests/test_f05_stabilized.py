"""Regression tests for phase-independent clinical action and leakage guards."""
from app.feature05.clinical_integration import clinical_options
from app.simulation.engine import (
    create_session,
    request_examination,
    request_investigation,
)


def _sample():
    return create_session({
        "exam_items":[{"id":"respiratory_rate","label":"Respiratory Rate","value":42,"unit":"/min","system":"vitals","relevance":"essential"}],
        "case_investigation_items":[{"id":"cbc","label":"CBC","results":[{"id":"wbc","label":"WBC","value":15000,"unit":"/uL","ref_range":"4000-11000","flag":"high"}],"relevance":"helpful"}],
        "imaging":[{"id":"cxr","label":"Chest X-ray","report_text":"Perihilar changes","image_asset":"case/path.jpg","relevance":"helpful"}],
        "investigations":{},
    })


def test_f05_tools_are_available_during_introduction_and_persist():
    s=_sample()
    assert s.current_phase.value == "introduction"
    exam=request_examination(s,"respiratory_rate")
    lab=request_investigation(s,"cbc")
    assert exam["result"]["value"]==42
    assert lab["result"][0]["value"]==15000
    assert len([e for e in s.events if e.event_type=="examination_requested"])==1
    assert s.requested_investigations == ["cbc"]


def test_f05_catalog_does_not_leak_findings_or_relevance():
    s=_sample()
    summary=str(clinical_options(s))
    for secret in ["15000","Perihilar","case/path.jpg","essential","helpful"]:
        assert secret not in summary


def test_f05_duplicate_and_unavailable_are_logged():
    s=_sample()
    request_examination(s,"respiratory_rate")
    duplicate=request_examination(s,"respiratory_rate")
    missing=request_investigation(s,"something_not_present")
    assert duplicate["status"]=="already_requested"
    assert missing["status"]=="unavailable"
    assert s.events[-2].details["repeated"] is True
    assert "relevance" not in str(s.to_dict())


def test_f05_imaging_does_not_expose_storage_path():
    s=_sample()
    r=request_investigation(s,"cxr")
    assert r["result"]["image_available"] is True
    assert "case/path.jpg" not in str(s.to_dict())
    assert "case/path.jpg" not in str(r)


def test_f05_completed_or_paused_session_rejects_new_orders():
    from app.simulation.engine import SimulationError
    for state in ("is_paused","is_completed"):
        s=_sample();setattr(s,state,True)
        try:request_examination(s,"respiratory_rate")
        except SimulationError:pass
        else:assert False, f"{state} must block clinical ordering"
