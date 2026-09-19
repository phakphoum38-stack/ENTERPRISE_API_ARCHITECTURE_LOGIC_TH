#!/usr/bin/env python3
"""Deterministic, bounded Mathematical Root for Research OS."""
from __future__ import annotations
import argparse, hashlib, json, sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_STATES={"UNKNOWN","DISCOVERED","UNDERSTANDING_PARTIAL","UNDERSTOOD","PRACTICED","TESTED","EVIDENCED","CONFIDENT","MASTERED","SUPERSEDED","CONFLICTED"}
REALITY_STATES={"CLAIMED","DESIGNED","IMPLEMENTED","EXECUTED","OBSERVED","MEASURED","REPRODUCED","VERIFIED","CONTRADICTED","UNKNOWN"}
RELATIONS={"REQUIRES","ENABLES","DEPENDS_ON","CAUSES","CORRELATES_WITH","CONFLICTS_WITH","TRANSFORMS","PRODUCES","OBSERVES","MEASURES","VERIFIES","PROVES","RECOVERS","LEARNS_FROM","SUPERSEDES"}

@dataclass(frozen=True)
class RootObject:
    object_id:str
    kind:str
    state:str="UNKNOWN"
    reality:str="UNKNOWN"
    attrs:dict[str,Any]=field(default_factory=dict)

@dataclass(frozen=True)
class RootRelation:
    source:str
    relation:str
    target:str
    attrs:dict[str,Any]=field(default_factory=dict)

class MathematicalRoot:
    def __init__(self, contract_path:str|Path):
        self.contract_path=Path(contract_path)
        self.contract=json.loads(self.contract_path.read_text(encoding="utf-8"))
        if self.contract.get("contract_id")!="research-os-mathematical-root-v1":
            raise ValueError("invalid mathematical root contract")
        self.objects={}
        self.relations=[]

    def add_object(self,obj:RootObject)->None:
        if not obj.object_id or obj.object_id in self.objects: raise ValueError("duplicate or empty object identity")
        if obj.state not in ROOT_STATES or obj.reality not in REALITY_STATES: raise ValueError("invalid object state")
        self.objects[obj.object_id]=obj

    def relate(self,edge:RootRelation)->None:
        if edge.relation not in RELATIONS: raise ValueError("invalid relation")
        if edge.source not in self.objects or edge.target not in self.objects: raise ValueError("relation endpoint missing")
        if edge in self.relations: raise ValueError("duplicate relation")
        self.relations.append(edge)

    def transition(self,object_id:str,state:str,*,evidence:bool=False)->RootObject:
        if state not in ROOT_STATES: raise ValueError("invalid state")
        obj=self.objects[object_id]
        if state in {"CONFIDENT","MASTERED"} and not evidence: raise ValueError("confidence/mastery requires evidence")
        updated=RootObject(obj.object_id,obj.kind,state,obj.reality,dict(obj.attrs))
        self.objects[object_id]=updated
        return updated

    def set_reality(self,object_id:str,reality:str)->RootObject:
        if reality not in REALITY_STATES: raise ValueError("invalid reality state")
        obj=self.objects[object_id]
        updated=RootObject(obj.object_id,obj.kind,obj.state,reality,dict(obj.attrs))
        self.objects[object_id]=updated
        return updated

    def trace(self,start:str,depth:int=3)->list[list[str]]:
        if start not in self.objects: raise KeyError(start)
        depth=max(0,min(depth,32)); paths=[]
        def walk(node,path,remaining):
            if remaining==0 or not [e for e in self.relations if e.source==node]:
                paths.append(path); return
            for e in [e for e in self.relations if e.source==node]:
                if e.target in path: paths.append(path+[e.target])
                else: walk(e.target,path+[e.target],remaining-1)
        walk(start,[start],depth); return paths

    def validate(self)->list[str]:
        errors=[]
        if self.contract.get("authority",{}).get("mode")!="descriptive_only": errors.append("authority_not_descriptive_only")
        if self.contract.get("cardinality",{}).get("materialization")!="forbidden": errors.append("logical_space_materialization_not_forbidden")
        for e in self.relations:
            if e.source not in self.objects or e.target not in self.objects: errors.append("missing_relation_endpoint")
        return errors

    def fingerprint(self)->str:
        payload={"contract_id":self.contract["contract_id"],"objects":[vars(v) for v in self.objects.values()],"relations":[vars(v) for v in self.relations]}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

    def summary(self)->dict[str,Any]:
        return {"contract_id":self.contract["contract_id"],"dimensions":len(self.contract.get("dimensions",[])),"objects":len(self.objects),"relations":len(self.relations),"logical_space":self.contract["cardinality"]["logical_space"],"materialization":"forbidden","authority":"descriptive_only"}

def main(argv:list[str])->int:
    p=argparse.ArgumentParser(); p.add_argument("--contract",default="current/MATHEMATICAL_ROOT_CONTRACT.json"); p.add_argument("--summary",action="store_true"); p.add_argument("--validate",action="store_true"); a=p.parse_args(argv)
    root=MathematicalRoot(a.contract); errors=root.validate()
    print(json.dumps(root.summary() if a.summary else ({"status":"PASS" if not errors else "FAIL","errors":errors} if a.validate else {"fingerprint":root.fingerprint()}),sort_keys=True))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main(sys.argv[1:]))
