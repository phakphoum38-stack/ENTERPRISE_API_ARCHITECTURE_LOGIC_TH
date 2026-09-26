#!/usr/bin/env python3
"""Canonical read-only Platform Spine engine."""
from __future__ import annotations
import argparse, json
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
FINAL_GATE=ROOT/"current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
LIFECYCLES=("PROPOSED","EXPERIMENTAL","ACTIVE","DEPRECATED","RETIRED")
HEALTH_STATES=("READY","DEGRADED","BLOCKED","RETIRED")
ALLOWED_TRANSITIONS={("PROPOSED","EXPERIMENTAL"),("EXPERIMENTAL","ACTIVE"),("ACTIVE","DEPRECATED"),("DEPRECATED","RETIRED")}
BLAST_RADIUS=("LOCAL","COMPONENT","PROJECT","CROSS_PROJECT","PLATFORM")
CLASS_TO_PLANE={"CORE":"CORE","PLATFORM":"PLATFORM","ASSURANCE":"ASSURANCE","EXPERIENCE":"EXPERIENCE","EXTENSION":"EXTENSION"}
@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str,...]
    warnings: tuple[str,...]=()
    def as_dict(self)->dict[str,Any]:
        return {"status":"PASS" if self.ok else "FAIL","errors":list(self.errors),"warnings":list(self.warnings)}
class PlatformSpine:
    def __init__(self,root:Path=ROOT)->None:
        self.root=root
        self.contract=self._load("current/RESEARCH_OS_PLATFORM_SPINE_ENGINE_CONTRACT.json")
        self.registry=self._load("current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json")
        self.schema=self._load("current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json")
        self.plane=self._load("current/PLANE_BOUNDARY_CONTRACT.json")
        self.components={c["id"]:c for c in self.registry.get("components",[])}
    def _load(self,p:str)->dict[str,Any]:
        return json.loads((self.root/p).read_text(encoding="utf-8"))
    def validate_authority(self)->list[str]:
        a=self.contract.get("authority",{}); e=[]
        for k in ("may_execute","may_authorize","may_approve","may_merge","may_release"):
            if a.get(k) is not False: e.append("authority:"+k)
        if a.get("release_authority")!="FINAL_GATE": e.append("authority:release_authority")
        return e
    def validate_registry(self)->list[str]:
        e=[]
        if self.registry.get("status")!="ACTIVE": e.append("registry:not_active")
        if self.registry.get("count_is_informational") is not True: e.append("registry:count_is_not_informational")
        if not self.components: e.append("registry:empty")
        for c in self.components.values():
            cid=c["id"]
            if c.get("lifecycle") not in LIFECYCLES: e.append(f"{cid}:invalid_lifecycle")
            if c.get("required") and c.get("lifecycle")!="ACTIVE": e.append(f"{cid}:required_not_active")
            if not c.get("authority",{}).get("mode"): e.append(f"{cid}:authority_missing")
            compat=c.get("compatibility",{})
            if not compat.get("registry_schema") or not compat.get("platform_contract"): e.append(f"{cid}:compatibility_missing")
            if c.get("lifecycle")!="RETIRED":
                if not c.get("canonical") or not (self.root/c["canonical"]).is_file(): e.append(f"{cid}:canonical_missing")
                for field in ("contracts","tests","evidence"):
                    for ref in c.get(field,[]):
                        if not (self.root/ref).is_file(): e.append(f"{cid}:{field}_missing:{ref}")
            if len(c.get("capabilities",[]))!=len(set(c.get("capabilities",[]))): e.append(f"{cid}:duplicate_capabilities")
            for dep in c.get("dependencies",[]):
                if dep not in self.components: e.append(f"{cid}:unknown_dependency:{dep}")
        return e
    def dependency_graph(self)->dict[str,tuple[str,...]]:
        return {cid:tuple(c.get("dependencies",[])) for cid,c in self.components.items()}
    def detect_cycles(self)->list[tuple[str,...]]:
        graph=self.dependency_graph(); cycles=[]; visiting=[]; visited=set()
        def visit(n):
            if n in visiting:
                cycles.append(tuple(visiting[visiting.index(n):]+[n])); return
            if n in visited: return
            visiting.append(n)
            for dep in graph.get(n,()): visit(dep)
            visiting.pop(); visited.add(n)
        for n in graph: visit(n)
        return cycles
    def forbidden_plane_edges(self)->list[tuple[str,str,str]]:
        forbidden=set(self.plane.get("forbidden_dependency_direction",[])); out=[]
        for source,c in self.components.items():
            sp=CLASS_TO_PLANE.get(c.get("class",""))
            for target in c.get("dependencies",[]):
                tp=CLASS_TO_PLANE.get(self.components.get(target,{}).get("class",""))
                if sp and tp and f"{sp}->{tp}" in forbidden: out.append((source,f"{sp}->{tp}",target))
        return out
    def transitive_dependents(self,targets:list[str])->tuple[str,...]:
        reverse=defaultdict(set)
        for source,deps in self.dependency_graph().items():
            for dep in deps: reverse[dep].add(source)
        seen=set(targets); q=deque(targets)
        while q:
            cur=q.popleft()
            for d in sorted(reverse.get(cur,())):
                if d not in seen: seen.add(d); q.append(d)
        return tuple(sorted(seen))
    def impact(self,targets:list[str],blast_radius="COMPONENT")->dict[str,Any]:
        if blast_radius not in BLAST_RADIUS: raise ValueError("invalid_blast_radius:"+blast_radius)
        unknown=sorted(set(targets)-set(self.components))
        if unknown: return {"status":"HOLD","unknown_targets":unknown,"blast_radius":blast_radius}
        return {"status":"PASS","targets":sorted(set(targets)),"direct_impact":sorted(set(targets)),"transitive_impact":list(self.transitive_dependents(targets)),"blast_radius":blast_radius,"required_categories":["contracts","workflows","tests","final_gate","invariants","product_surfaces"],"unknown_impact":False}
    def validate_lifecycle_transition(self,current,target,required=False)->ValidationResult:
        e=[]
        if current not in LIFECYCLES or target not in LIFECYCLES: e.append("unknown_lifecycle_state")
        elif (current,target) not in ALLOWED_TRANSITIONS: e.append(f"forbidden_transition:{current}->{target}")
        if required and target=="RETIRED": e.append("required_component_retirement_requires_registry_governance_change")
        return ValidationResult(not e,tuple(e))
    def validate_compatibility(self,component_id,registry_schema="1.x",platform_contract="1.x",breaking=False,migration_present=False)->ValidationResult:
        c=self.components.get(component_id)
        if c is None: return ValidationResult(False,(f"unknown_component:{component_id}",))
        d=c.get("compatibility",{}); e=[]
        if not d.get("registry_schema","").startswith(registry_schema.split(".",1)[0]+"."): e.append(f"{component_id}:registry_schema_incompatible")
        if not d.get("platform_contract","").startswith(platform_contract.split(".",1)[0]+"."): e.append(f"{component_id}:platform_contract_incompatible")
        if breaking and not migration_present: e.append(f"{component_id}:breaking_change_requires_migration")
        return ValidationResult(not e,tuple(e))
    def validate_health(self,state,authorization_decision=None)->ValidationResult:
        e=[]
        if state not in HEALTH_STATES: e.append("unknown_health:"+state)
        if authorization_decision is not None: e.append("health_cannot_create_authorization")
        return ValidationResult(not e,tuple(e))
    def drift_report(self)->dict[str,Any]:
        f=[]
        for cid,c in self.components.items():
            if c.get("lifecycle")=="RETIRED": continue
            if not c.get("canonical") or not (self.root/c["canonical"]).is_file(): f.append({"component":cid,"domain":"architecture","status":"MISSING"})
            for field in ("contracts","tests","evidence"):
                for ref in c.get(field,[]):
                    if not (self.root/ref).is_file(): f.append({"component":cid,"domain":field,"status":"MISSING","reference":ref})
        return {"status":"PASS" if not f else "DRIFT","finding_count":len(f),"findings":f}
    def migration_plan(self,component_id,from_version,to_version,breaking=False)->dict[str,Any]:
        if component_id not in self.components: return {"status":"HOLD","reason":"unknown_component","component":component_id}
        if not breaking: return {"status":"PASS","required":False,"sequence":["COMPATIBILITY","VALIDATE","EVIDENCE"],"rollback_required":False}
        return {"status":"REQUIRED","required":True,"component":component_id,"from":from_version,"to":to_version,"sequence":["PLAN","COMPATIBILITY","MIGRATE","VALIDATE","EVIDENCE","RETIRE_OLD"],"rollback_required":True,"new_contract_version_required":True}
    def simulate(self,targets,blast_radius="COMPONENT")->dict[str,Any]:
        impact=self.impact(targets,blast_radius)
        if impact["status"]!="PASS": return {"status":"HOLD","checks":{"impact":impact}}
        cycles=self.detect_cycles(); forbidden=self.forbidden_plane_edges(); registry_errors=self.validate_registry()
        checks={"dependency":"PASS" if not cycles else "FAIL","impact":"PASS","contract":"PASS" if not registry_errors else "FAIL","failure":"DECLARED","rollback":"REQUIRED"}
        errors=[f"dependency_cycle:{c}" for c in cycles]+[f"forbidden_plane_edge:{v}" for v in forbidden]+registry_errors
        if errors: return {"status":"FAIL","checks":checks,"errors":errors,"release_authority":"FINAL_GATE"}
        if BLAST_RADIUS.index(blast_radius)>=BLAST_RADIUS.index("CROSS_PROJECT"): checks["failure"]="REQUIRED_BEFORE_CHANGE"
        return {"status":"PASS","checks":checks,"impact":impact,"release_authority":"FINAL_GATE","simulation_has_no_release_authority":True}
    def validate(self)->ValidationResult:
        e=self.validate_authority()+self.validate_registry()
        e += [f"dependency_cycle:{c}" for c in self.detect_cycles()]
        e += [f"forbidden_plane_edge:{s}:{edge}:{t}" for s,edge,t in self.forbidden_plane_edges()]
        d=self.drift_report()
        if d["status"]!="PASS": e.append("drift:"+str(d["finding_count"]))
        gate=FINAL_GATE.read_text(encoding="utf-8")
        for anchor in ("release_authority: final_gate","current/RESEARCH_OS_PLATFORM_ONE_PASS_COMPLETION_CONTRACT.json","platform_one_pass_completion:","current/RESEARCH_OS_PLATFORM_SPINE_ENGINE_CONTRACT.json","platform_spine_engine:"):
            if anchor not in gate: e.append("final_gate_anchor:"+anchor)
        if self.contract.get("security",{}).get("chain")!=["Identity","Capability","Policy","Authorization","Entitlement","Execution","Evidence"]: e.append("security_chain")
        if self.contract.get("security",{}).get("resource_conflict")!="REJECT_AND_RELEASE": e.append("resource_conflict")
        if self.contract.get("runtime",{}).get("direct_engine_to_runner") is not False: e.append("direct_engine_to_runner")
        return ValidationResult(not e,tuple(e))
    def report(self):
        r=self.validate()
        return {"status":"PASS" if r.ok else "FAIL","errors":list(r.errors),"component_count":len(self.components),"required_components":sum(1 for c in self.components.values() if c.get("required")),"cycles":[list(c) for c in self.detect_cycles()],"forbidden_plane_edges":[list(v) for v in self.forbidden_plane_edges()],"drift":self.drift_report(),"release_authority":"FINAL_GATE","authority":"DESCRIPTIVE_VALIDATING_ONLY"}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--validate",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--impact",nargs="+"); p.add_argument("--blast-radius",default="COMPONENT",choices=BLAST_RADIUS); p.add_argument("--simulate",nargs="+"); p.add_argument("--lifecycle",nargs=2); p.add_argument("--health"); a=p.parse_args(); e=PlatformSpine()
    if a.validate:
        r=e.validate(); print("PLATFORM_SPINE=PASS" if r.ok else "PLATFORM_SPINE=FAIL"); print("\n".join(r.errors)); return 0 if r.ok else 1
    if a.report: print(json.dumps(e.report(),sort_keys=True)); return 0 if e.validate().ok else 1
    if a.impact: print(json.dumps(e.impact(a.impact,a.blast_radius),sort_keys=True)); return 0
    if a.simulate:
        r=e.simulate(a.simulate,a.blast_radius); print(json.dumps(r,sort_keys=True)); return 0 if r["status"]=="PASS" else 1
    if a.lifecycle:
        r=e.validate_lifecycle_transition(a.lifecycle[0],a.lifecycle[1]); print(json.dumps(r.as_dict(),sort_keys=True)); return 0 if r.ok else 1
    if a.health:
        r=e.validate_health(a.health); print(json.dumps(r.as_dict(),sort_keys=True)); return 0 if r.ok else 1
    print(json.dumps(e.report(),sort_keys=True)); return 0 if e.validate().ok else 1
if __name__=="__main__": raise SystemExit(main())
