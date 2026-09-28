from datetime import datetime, timezone
from pathlib import Path
import json

from tools.mathematical_root import MathematicalRoot, RootObject, RootRelation
from tools.world_research import EvidenceRecord, ResearchSource, WorldResearch

ROOT=Path("current/MATHEMATICAL_ROOT_CONTRACT.json")
WORLD=Path("current/WORLD_RESEARCH_CONTRACT.json")

def test_root_contract_is_bounded_and_descriptive():
    data=json.loads(ROOT.read_text(encoding="utf-8"))
    assert data["cardinality"]["materialization"]=="forbidden"
    assert data["authority"]["mode"]=="descriptive_only"
    assert len(data["dimensions"])>=60

def test_root_rejects_promotion_without_evidence():
    root=MathematicalRoot(ROOT)
    root.add_object(RootObject("x","KNOWLEDGE"))
    try: root.transition("x","CONFIDENT")
    except ValueError: return
    raise AssertionError("promotion without evidence must fail")

def test_root_relation_and_bounded_trace():
    root=MathematicalRoot(ROOT)
    for x,k in [("a","INTENT"),("b","CAPABILITY"),("c","TOOL")]: root.add_object(RootObject(x,k))
    root.relate(RootRelation("a","REQUIRES","b")); root.relate(RootRelation("b","ENABLES","c"))
    assert ["a","b","c"] in root.trace("a",depth=2)

def test_world_research_preserves_provenance_and_boundaries():
    research=WorldResearch(WORLD)
    source=ResearchSource("SRC-001","https://example.invalid/source","OFFICIAL_DOCUMENT","test","test intent",datetime.now(timezone.utc).isoformat(),WorldResearch.fingerprint("content"))
    research.register_source(source)
    research.record_evidence(EvidenceRecord("EV-001","SRC-001","test claim"))
    assert research.validate()==[]
    assert research.summary()["automatic_truth_promotion"] is False

def test_world_research_rejects_bad_fingerprint():
    research=WorldResearch(WORLD)
    source=ResearchSource("SRC-002","https://example.invalid/source","NEWS","test","intent","2026-01-01T00:00:00+00:00","bad")
    try: research.register_source(source)
    except ValueError: return
    raise AssertionError("bad fingerprint must fail")
