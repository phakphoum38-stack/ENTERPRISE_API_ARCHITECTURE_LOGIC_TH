#!/usr/bin/env python3
"""Build a source-SHA-pinned searchable M.2 inventory and relationship graph."""
from __future__ import annotations
import argparse,json,re,subprocess,hashlib,os
try:
 from research_os_test_case_inventory import discover as discover_test_cases
except ModuleNotFoundError:
 from tools.research_os_test_case_inventory import discover as discover_test_cases
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXCLUDES={
 ".git",".dart_tool","build","dist","node_modules","__pycache__",".venv","venv",
 ".research_os_data",
 "m2_audit_index.json","m2_audit_index_summary.txt",
}
M2_STATE_DIR_NAME="m2"
M2_STATE_FILE_NAME="audit_snapshot_state.json"
M2_STATE_SCHEMA="RESEARCH_OS_M2_AUDIT_SNAPSHOT_V2"
TEXT_SUFFIXES={".py",".dart",".json",".yml",".yaml",".md",".txt",".ps1",".sh",".toml",".html",".css",".js",".cs",".cpp",".h"}
CONTRACT_RE=re.compile(r"current/[A-Z0-9_./-]+\.(?:json|ya?ml)")
INV_RE=re.compile(r"\bINV-\d{3}\b")
CAPABILITY_RULES=[
 ("final_gate",("final_gate","final-gate","release_spine")),
 ("evidence",("evidence","provenance","lineage")),
 ("authorization",("authorization","auth","entitlement","owner")),
 ("workflow",("workflow","orchestrat","queue","runner")),
 ("project_scale",("100_project","project_scale","scale_execution")),
 ("schedule",("schedule","scheduler","reconciliation")),
 ("control_center",("control_center","control-center")),
 ("surface",("surface","navigation","flutter","ios","windows","web")),
 ("assurance",("aeos","assurance","invariant")),
 ("release",("release","artifact","installer","distribution")),
]
def git_sha():
 return subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()

def data_root():
 configured=os.getenv("RESEARCH_OS_DATA_DIR","").strip()
 if configured:
  return Path(configured).expanduser().resolve()
 return (ROOT/".research_os_data").resolve()

def m2_state_path():
 return data_root()/M2_STATE_DIR_NAME/M2_STATE_FILE_NAME

def file_sha256(p):
 digest=hashlib.sha256()
 with p.open("rb") as handle:
  for chunk in iter(lambda: handle.read(1024*1024),b""):
   digest.update(chunk)
 return digest.hexdigest()

def files():
 return sorted(p for p in ROOT.rglob("*") if p.is_file() and not any(x in EXCLUDES for x in p.parts))

def rel(p): return p.relative_to(ROOT).as_posix()

def load_snapshot_state():
 path=m2_state_path()
 if not path.exists():
  return {"schema":M2_STATE_SCHEMA,"files":{}}
 try:
  payload=json.loads(path.read_text(encoding="utf-8"))
 except (OSError,UnicodeDecodeError,json.JSONDecodeError):
  return {"schema":M2_STATE_SCHEMA,"files":{}}
 if payload.get("schema")!=M2_STATE_SCHEMA or not isinstance(payload.get("files"),dict):
  return {"schema":M2_STATE_SCHEMA,"files":{}}
 return payload

def save_snapshot_state(source,rows):
 path=m2_state_path()
 path.parent.mkdir(parents=True,exist_ok=True)
 payload={
  "schema":M2_STATE_SCHEMA,
  "source_sha":source,
  "root":str(ROOT),
  "files":{row["path"]:row for row in rows},
 }
 temp=path.with_suffix(".tmp")
 temp.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 temp.replace(path)
 return path
def contract_stem(path):
 """Return the canonical semantic stem for a contract path."""
 stem=Path(path).stem.lower()
 for suffix in ("_contract","-contract"):
  if stem.endswith(suffix):
   stem=stem[:-len(suffix)]
   break
 return stem

def kind(path, required_contracts=()):
 if path.startswith(".github/workflows/"): return "workflow"
 if "/test" in path or path.startswith("tests/") or Path(path).name.startswith("test_") or "_test." in path: return "test"
 if path.startswith("docs/") or path.endswith((".md",".txt")): return "documentation"
 if path.startswith("scripts/"): return "script"
 if path.endswith((".py",".dart",".ps1",".sh",".cs",".cpp",".h")): return "implementation"
 name=Path(path).name.upper()
 if Path(path).suffix.lower()==".diff": return "other"
 if path in required_contracts: return "contract"
 if "CONTRACT" in name or path.startswith("current/CONTRACTS/"): return "contract"
 return "other"
def read_text(p):
 if p.suffix.lower() not in TEXT_SUFFIXES: return ""
 try: return p.read_text(encoding="utf-8")
 except (OSError,UnicodeDecodeError): return ""
def capabilities(path,text):
 hay=(path+" "+text[:12000]).lower()
 found=[n for n,needles in CAPABILITY_RULES if any(x in hay for x in needles)]
 return found or ["general"]
def nid(k,path): return k.upper()+":"+path

SEMANTIC_ASSURANCE_RELATIONS=frozenset({"VERIFIED_BY","ENFORCED_BY","DISPATCHED_BY","SUPPORTED_BY","BOUND_TO"})

def contract_stem(path: str) -> str:
 stem=Path(path).stem.lower()
 for suffix in ("_contract","-contract"):
  if stem.endswith(suffix):
   stem=stem[:-len(suffix)]
   break
 return stem

def _declared_identities(path: str, text: str) -> set[str]:
 """Extract conservative canonical identities from artifact metadata."""
 values={contract_stem(path)}
 for pattern in (
  r'"(?:contract|contract_id|capability_id|component_id)"\\s*:\\s*"([A-Za-z0-9_.:/-]+)"',
  r'^(?:contract|contract_id|capability_id|component_id):\\s*([A-Za-z0-9_.:/-]+)',
 ):
  values.update(x.lower() for x in re.findall(pattern,text,re.MULTILINE))
 return {x for x in values if x}

def resolve_semantic_bindings(contract: str, rows: list[dict], by_path: dict[str,Path],
                              contracts: list[str], implementations: list[str],
                              workflows: list[str], tests: list[str]) -> dict:
 """Resolve assurance bindings generically; ambiguity is never auto-selected."""
 contract_text=read_text(by_path[contract])
 bindings=[]
 for row in rows:
  target=row["path"]
  if target==contract:
   continue
  if row["kind"]=="contract" and contract in row["contract_refs"]:
   bindings.append(("BOUND_TO",target,"explicit_contract_reference"))
  elif row["kind"] in {"implementation","workflow"} and contract in row["contract_refs"]:
   relation="ENFORCED_BY" if row["kind"]=="implementation" else "DISPATCHED_BY"
   bindings.append((relation,target,"explicit_contract_reference"))
 for target in tests:
  if contract in read_text(by_path[target]) or contract_stem(contract) in Path(target).stem.lower():
   bindings.append(("VERIFIED_BY",target,"test_identity"))
 for target in by_path:
  if target.startswith("evidence/") and contract in read_text(by_path[target]):
   bindings.append(("SUPPORTED_BY",target,"explicit_contract_reference"))
 # Semantic fallback is deliberately unique: identity overlap must identify one target.
 identities=_declared_identities(contract,contract_text)
 for kind_name, candidates, relation in (
  ("implementation",implementations,"ENFORCED_BY"),
  ("workflow",workflows,"DISPATCHED_BY"),
 ):
  semantic=[p for p in candidates if identities & _declared_identities(p,read_text(by_path[p]))]
  if len(semantic)==1:
   bindings.append((relation,semantic[0],"unique_semantic_identity"))
  elif len(semantic)>1:
   return {"bindings":sorted(set(bindings)),"unresolved":False,"ambiguous":True,"ambiguous_targets":sorted(semantic)}
 return {"bindings":sorted(set(bindings)),"unresolved":not bindings,"ambiguous":False,"ambiguous_targets":[]}

def required_authority_paths(by_path):
 gate_path="current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
 if gate_path not in by_path:
  return [], []
 text=read_text(by_path[gate_path])
 def section(name):
  match=re.search(rf"^{name}:\n((?:  - .+\n)+)",text,re.MULTILINE)
  return [line[4:].strip() for line in match.group(1).splitlines()] if match else []
 return section("required_contracts"), section("required_workflows")

def build_index():
 source=git_sha(); ps=files(); by_path={rel(p):p for p in ps}; rows=[]
 test_case_inventory=discover_test_cases()
 required_contracts,required_workflows=required_authority_paths(by_path)
 snapshot=load_snapshot_state()
 previous=snapshot.get("files",{})
 current_paths={rel(p) for p in ps}
 rows=[]
 for p in ps:
  path=rel(p)
  stat=p.stat()
  old=previous.get(path)
  unchanged=False
  if old:
   unchanged=(
    old.get("size")==stat.st_size and
    old.get("mtime_ns")==stat.st_mtime_ns and
    isinstance(old.get("sha256"),str) and
    len(old.get("sha256",""))==64
   )
  if unchanged:
   row=dict(old)
  else:
   txt=read_text(p)
   digest=file_sha256(p)
   if old and old.get("sha256")==digest:
    row=dict(old)
    row["size"]=stat.st_size
    row["mtime_ns"]=stat.st_mtime_ns
    row["sha256"]=digest
   else:
    row={"path":path,"kind":kind(path,required_contracts),"size":stat.st_size,
     "mtime_ns":stat.st_mtime_ns,"sha256":digest,
     "capabilities":capabilities(path,txt),
     "contract_refs":sorted({x for x in CONTRACT_RE.findall(txt) if x in by_path}),
     "invariant_refs":sorted(set(INV_RE.findall(txt))),
     "has_contract_reference":bool(CONTRACT_RE.search(txt)),
     "has_test_reference":bool(re.search(r"(?:test_|_test\.)",txt)),
     "has_workflow_reference":".github/workflows/" in txt,
     "has_evidence_reference":bool(re.search(r"evidence|provenance|lineage",txt,re.I)),
     "has_final_gate_reference":bool(re.search(r"final[_ -]?gate|release_authority",txt,re.I))}
  rows.append(row)
 contracts=[r["path"] for r in rows if r["kind"]=="contract"]
 tests=[r["path"] for r in rows if r["kind"]=="test"]
 workflows=[r["path"] for r in rows if r["kind"]=="workflow"]
 implementations=[r["path"] for r in rows if r["kind"]=="implementation"]
 nodes=[]; node_ids=set(); edges=[]
 def add_node(i,k,path=None,state="UNKNOWN"):
  if i not in node_ids:
   node_ids.add(i); nodes.append({"id":i,"kind":k,"path":path,"state":state})
 contract_set=set(contracts)

 for r in rows:
  k=r["kind"].upper()
  add_node(nid(k,r["path"]),k,r["path"])

  for c in r["contract_refs"]:
   # Only authoritative inventory entries may become CONTRACT nodes.
   if c in contract_set:
    add_node(nid("CONTRACT",c),"CONTRACT",c)
    edges.append({"from":nid(k,r["path"]),"relation":"REFERENCES","to":nid("CONTRACT",c)})

    # Existing references are also semantic assurance evidence when the
    # referencing artifact has an assurance-bearing role.
    if k=="IMPLEMENTATION":
     edges.append({"from":nid("CONTRACT",c),"relation":"ENFORCED_BY","to":nid(k,r["path"])})
    elif k=="WORKFLOW":
     edges.append({"from":nid("CONTRACT",c),"relation":"DISPATCHED_BY","to":nid(k,r["path"])})
    elif r["path"].startswith("evidence/") or r["path"].startswith("evidence\\"):
     edges.append({"from":nid("CONTRACT",c),"relation":"SUPPORTED_BY","to":nid(k,r["path"])})

  for inv in r["invariant_refs"]:
   add_node("INVARIANT:"+inv,"INVARIANT",inv)
   edges.append({"from":nid(k,r["path"]),"relation":"ENFORCES_OR_REFERENCES","to":"INVARIANT:"+inv})
 def contract_test_matches(c,t):
  """Return True for explicit or strong semantic contract/test binding."""
  text=read_text(by_path[t])
  cp=Path(c)
  stem=contract_stem(c)
  test_stem=Path(t).stem.lower()

  if c in text or cp.name in text:
   return True

  if stem and stem in test_stem:
   return True

  return False

 for c in contracts:
  for t in tests:
   if contract_test_matches(c,t):
    edges.append({"from":nid("CONTRACT",c),"relation":"VERIFIED_BY","to":nid("TEST",t)})
 workflow_names={Path(w).name:w for w in workflows}
 for w in workflows:
  txt=read_text(by_path[w])
  for name,target in workflow_names.items():
   if target!=w and name in txt:
    edges.append({"from":nid("WORKFLOW",w),"relation":"DISPATCHES_OR_REFERENCES","to":nid("WORKFLOW",target)})
 final_gate_path="current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
 final_gate_exists=final_gate_path in by_path
 if final_gate_exists:
  add_node("FINAL_GATE:UNIFIED","AUTHORITY",final_gate_path,"VERIFIED")
 for r in rows:
  if r["has_final_gate_reference"] and r["kind"]!="workflow":
   edges.append({"from":nid(r["kind"],r["path"]),"relation":"BINDS_TO","to":"FINAL_GATE:UNIFIED"})
   if r["kind"]=="contract":
    edges.append({"from":nid("CONTRACT",r["path"]),"relation":"BOUND_TO","to":"FINAL_GATE:UNIFIED"})
 for w in workflows:
  if "unified-final-gate" in w or "RESEARCH_OS_UNIFIED_FINAL_GATE" in read_text(by_path[w]):
   edges.append({"from":nid("WORKFLOW",w),"relation":"PARTICIPATES_IN","to":"FINAL_GATE:UNIFIED"})
 edges=sorted({(e["from"],e["relation"],e["to"]):e for e in edges}.values(),key=lambda e:(e["from"],e["relation"],e["to"]))
 targets={n["id"] for n in nodes}; dangling=[e for e in edges if e["from"] not in targets or e["to"] not in targets]
 findings=[]
 for required in required_contracts:
  if required not in by_path or required not in contracts:
   findings.append({"state":"MISSING","code":"REQUIRED_FINAL_GATE_CONTRACT_MISSING_FROM_M2","path":required})
 for required in required_workflows:
  if required not in by_path or required not in workflows:
   findings.append({"state":"MISSING","code":"REQUIRED_FINAL_GATE_WORKFLOW_MISSING_FROM_M2","path":required})
 assurance_relations={"VERIFIED_BY","ENFORCED_BY","DISPATCHED_BY","BOUND_TO","SUPPORTED_BY"}

 for c in contracts:
  verified=any(contract_test_matches(c,t) for t in tests)
  has_assurance=any(
   e["from"]==nid("CONTRACT",c) and e["relation"] in assurance_relations
   for e in edges
  )

  if not verified and not has_assurance:
   findings.append({
    "state":"INCOMPLETE",
    "code":"CONTRACT_WITHOUT_ASSURANCE_BINDING",
    "path":c,
   })
 integrity={
  "exact_source_sha":bool(re.fullmatch(r"[0-9a-f]{40}",source)),
  "inventory_completeness":bool(rows),
  "test_case_inventory":test_case_inventory["source_sha"]==source and test_case_inventory["inventory"]["test_files"]>0 and test_case_inventory["inventory"]["discovered_test_cases"]>0,
  "duplicate_path_detection":len({r["path"] for r in rows})==len(rows),
  "unique_node_ids":len(node_ids)==len(nodes),
  "no_dangling_edges":not dangling,
  "contract_test_linkage":bool(contracts) and any(e["from"].startswith("CONTRACT:") and e["relation"]=="VERIFIED_BY" and e["to"].startswith("TEST:") for e in edges) and all(any(e["from"]==nid("CONTRACT",c) and e["relation"]=="VERIFIED_BY" for e in edges) for c in contracts if any(contract_test_matches(c,t) for t in tests)),
  "contract_nodes_are_inventory_backed":all(
   n["id"]==nid("CONTRACT",n["path"])
   and n["path"] in contract_set
   for n in nodes
   if n["kind"]=="CONTRACT"
  ),
  "semantic_assurance_graph":any(
   e["relation"] in {"VERIFIED_BY","ENFORCED_BY","DISPATCHED_BY","BOUND_TO","SUPPORTED_BY"}
   for e in edges
  ),
  "contract_implementation_linkage":bool(implementations) and any(e["from"].startswith("IMPLEMENTATION:") and e["relation"]=="REFERENCES" and e["to"].startswith("CONTRACT:") for e in edges) and all(any(e["from"]==nid("IMPLEMENTATION",i) and e["relation"]=="REFERENCES" and e["to"].startswith("CONTRACT:") for e in edges) for i in implementations if any(c in read_text(by_path[i]) for c in contracts)),
  "semantic_binding_integrity":all(not v["ambiguous"] for v in semantic_results.values()),
  "workflow_inventory":bool(workflows),
  "contract_inventory":bool(contracts),
  "required_contract_inventory":bool(required_contracts) and all(path in contracts for path in required_contracts),
  "required_workflow_inventory":bool(required_workflows) and all(path in workflows for path in required_workflows),
  "invariant_inventory":any(r["invariant_refs"] for r in rows),
  "final_gate_node":final_gate_exists and "FINAL_GATE:UNIFIED" in targets,
 }
 save_snapshot_state(source,rows)
 return {"schema":"RESEARCH_OS_M2_AUDIT_GRAPH_V2","source_sha":source,"root":str(ROOT),
  "inventory":{"files":len(rows),"contracts":len(contracts),"implementations":len(implementations),"tests":len(tests),"workflows":len(workflows),"required_contracts":len(required_contracts),"required_workflows":len(required_workflows),"test_case_inventory":test_case_inventory["inventory"],"nodes":len(nodes),"edges":len(edges),"findings":len(findings)},
  "integrity":integrity,"findings":findings,"nodes":nodes,"edges":edges,"files":rows,"dangling_edges":dangling,
  "incremental":{"state_path":str(m2_state_path()),"previous_files":len(previous),"current_files":len(current_paths),
   "reused_files":sum(1 for r in rows if r["path"] in previous and previous[r["path"]].get("size")==r.get("size") and previous[r["path"]].get("mtime_ns")==r.get("mtime_ns")),
   "deleted_files":sorted(set(previous)-current_paths)}}
def build_graph(): return build_index()
def main():
 p=argparse.ArgumentParser(); p.add_argument("--output",default="m2_audit_index.json"); p.add_argument("--summary",default="m2_audit_index_summary.txt"); p.add_argument("--query",default=""); a=p.parse_args()
 g=build_index()
 if not all(g["integrity"].values()):
  print("M2_AUDIT_INDEX=FAIL")
  for k,v in g["integrity"].items():
   if not v: print("INTEGRITY_FAIL="+k)
  return 2
 if a.query:
  q=a.query.lower()
  nodes=[n for n in g["nodes"] if q in n["id"].lower() or q in (n.get("path") or "").lower()]
  edges=[e for e in g["edges"] if q in json.dumps(e).lower()]
  print(json.dumps({"query":a.query,"nodes":nodes,"edges":edges},ensure_ascii=False,indent=2)); return 0
 Path(a.output).write_text(json.dumps(g,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 s=["RESEARCH OS M.2 WHOLE-SYSTEM AUDIT GRAPH",f"SOURCE_SHA={g['source_sha']}",
    *[f"{k.upper()}={v}" for k,v in g["inventory"].items()],
    "M2_AUDIT_GRAPH=PASS","M2_AUDIT_INDEX=PASS"]
 Path(a.summary).write_text("\n".join(s)+"\n",encoding="utf-8"); print("\n".join(s)); return 0
if __name__=="__main__": raise SystemExit(main())
