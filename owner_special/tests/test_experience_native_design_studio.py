import json

import pytest

from tools.experience_studio import (
    ColorToken,
    Component,
    ComponentState,
    EvidenceRef,
    ExperienceState,
    ExperienceStudio,
    MotionMode,
    MotionSpec,
)


def test_contract_is_bounded_and_descriptive():
    payload = json.loads(open("current/EXPERIENCE_NATIVE_DESIGN_STUDIO_CONTRACT.json", encoding="utf-8").read())
    assert payload["authority"] == "descriptive_only"
    assert payload["logical_coverage"] == "10^1000"
    assert payload["materialization"] == "bounded_only"


def test_component_requires_evidence_before_release_states():
    studio = ExperienceStudio()
    component = Component("control-center", "Control Center")
    studio.add_component(component)
    with pytest.raises(ValueError, match="requires evidence"):
        component.transition(ExperienceState.RELEASED)


def test_state_complete_component_and_motion():
    studio = ExperienceStudio()
    studio.add_color(ColorToken("surface.primary", "Surface", "#101418", 7.0))
    component = Component("live-status", "Live Status")
    for name in ("default", "loading", "empty", "error", "offline", "recovery"):
        component.add_state(ComponentState(name, MotionMode.REDUCED if name == "error" else MotionMode.FULL))
    component.add_motion(MotionSpec("loading-to-ready", "loading", "default", 240, True, 0))
    component.add_evidence(EvidenceRef("EV-UX-001", "a" * 64, "functional"))
    component.transition(ExperienceState.EVIDENCED)
    studio.add_component(component)
    audit = studio.audit()
    assert audit["status"] == "PASS"
    assert studio.fingerprint() and len(studio.fingerprint()) == 64


def test_audit_holds_on_missing_states_and_low_contrast():
    studio = ExperienceStudio()
    studio.add_color(ColorToken("text.muted", "Text", "#888888", 2.0))
    studio.add_component(Component("partial", "Partial"))
    audit = studio.audit()
    assert audit["status"] == "HOLD"
    assert any(item.startswith("low_contrast:") for item in audit["issues"])
    assert any(item.startswith("missing_states:") for item in audit["issues"])


def test_bad_evidence_fingerprint_rejected():
    with pytest.raises(ValueError, match="SHA-256"):
        EvidenceRef("EV-UX-002", "short", "visual").validate()
