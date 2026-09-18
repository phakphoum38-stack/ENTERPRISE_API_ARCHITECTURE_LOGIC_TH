#!/usr/bin/env python3
"""Bounded World Research intake layer; external content remains untrusted input."""
from __future__ import annotations
import argparse,hashlib,json,sys
from dataclasses import dataclass,asdict
from pathlib import Path
from typing import Any

SOURCE_STATES={"DISCOVERED","ACQUIRED","PARSED","VERIFIED","CONFLICTED","REJECTED","UNKNOWN"}
EVIDENCE_STATES={"UNASSESSED","PARTIAL","SUPPORTED","CONTRADICTED","INSUFFICIENT"}
SOURCE_KINDS={"OFFICIAL_DOCUMENT","PRIMARY_RESEARCH","DATASET","REPOSITORY","TECHNICAL_DOCUMENTATION","NEWS","SECONDARY_ANALYSIS","COMMUNITY"}

@dataclass(frozen=True)
class ResearchSource:
    source_id:str
    locator:str
    source_kind:str
    scope:str
    query_or_intent:str
    retrieved_at:str
    content_fingerprint:str
    state:str="DISCOVERED"

@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id:str
    source_id:str
    claim:str
    evidence_state:str="UNASSESSED"
    processing_step:str="intake"

class WorldResearch:
    def __init__(self,contract_path:str|Path):
        self.contract_path=Path(contract_path)
        self.contract=json.loads(self.contract_path.read_text(encoding="utf-8"))
        if self.contract.get("contract_id")!="research-os-world-research-v1": raise ValueError("invalid world research contract")
        self.sources={}; self.evidence={}

    @staticmethod
    def fingerprint(content:str|bytes)->str:
        raw=content if isinstance(content,bytes) else content.encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def register_source(self,source:ResearchSource)->None:
        if source.source_id in self.sources or not source.locator: raise ValueError("duplicate or empty source identity")
        if source.source_kind not in SOURCE_KINDS or source.state not in SOURCE_STATES: raise ValueError("invalid source")
        if len(source.content_fingerprint)!=64: raise ValueError("invalid content fingerprint")
        self.sources[source.source_id]=source

    def record_evidence(self,record:EvidenceRecord)->None:
        if record.evidence_id in self.evidence: raise ValueError("duplicate evidence identity")
        if record.source_id not in self.sources: raise ValueError("evidence source missing")
        if record.evidence_state not in EVIDENCE_STATES: raise ValueError("invalid evidence state")
        self.evidence[record.evidence_id]=record

    def classify(self,evidence_id:str,state:str)->EvidenceRecord:
        if state not in EVIDENCE_STATES: raise ValueError("invalid evidence state")
        old=self.evidence[evidence_id]
        updated=EvidenceRecord(old.evidence_id,old.source_id,old.claim,state,old.processing_step)
        self.evidence[evidence_id]=updated
        return updated

    def source_manifest(self)->list[dict[str,Any]]:
        return [asdict(x) for x in self.sources.values()]

    def validate(self)->list[str]:
        errors=[]
        if self.contract.get("authority",{}).get("mode")!="descriptive_only": errors.append("authority_not_descriptive_only")
        limits=self.contract.get("bounded_execution",{})
        if not all(isinstance(limits.get(k),int) and limits[k]>0 for k in ("max_sources_per_run","max_depth","max_items_per_source")): errors.append("invalid_execution_bounds")
        for x in self.sources.values():
            if not x.retrieved_at: errors.append("missing_retrieved_at:"+x.source_id)
            if len(x.content_fingerprint)!=64: errors.append("invalid_fingerprint:"+x.source_id)
        return errors

    def summary(self)->dict[str,Any]:
        return {"contract_id":self.contract["contract_id"],"sources":len(self.sources),"evidence":len(self.evidence),"bounded":self.contract["bounded_execution"],"network_retrieval":"explicit_external_adapter_required","automatic_truth_promotion":False,"automatic_authority":False}

def main(argv:list[str])->int:
    p=argparse.ArgumentParser(); p.add_argument("--contract",default="current/WORLD_RESEARCH_CONTRACT.json"); p.add_argument("--summary",action="store_true"); p.add_argument("--validate",action="store_true"); a=p.parse_args(argv)
    w=WorldResearch(a.contract); errors=w.validate()
    print(json.dumps(w.summary() if a.summary else {"status":"PASS" if not errors else "FAIL","errors":errors},sort_keys=True))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main(sys.argv[1:]))
