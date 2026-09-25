#!/usr/bin/env python3
"""Canonical AI-provider connection boundary for Research OS."""
from __future__ import annotations
import hashlib, json, os, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_PATH=ROOT/"current/RESEARCH_OS_AI_PROVIDER_CONNECTION_CONTRACT.json"
EVIDENCE_CONTRACT_PATH=ROOT/"current/RESEARCH_OS_AI_PROVIDER_CONNECTION_EVIDENCE_CONTRACT.json"
EVIDENCE_PATH=ROOT/"research/artifacts/ai_provider_connections.jsonl"
STATES=("NOT_CONNECTED","CONNECTING","CONNECTED","DEGRADED","API_FALLBACK","UNAVAILABLE","HOLD")
PROVIDERS={
 "openai":{"label":"OpenAI / GPT","adapter":"openai-compatible","credential_env":("RESEARCH_OS_OPENAI_API_KEY",),"model_env":"RESEARCH_OS_OPENAI_MODEL","default_model":"gpt-5.6","endpoint_env":"RESEARCH_OS_OPENAI_ENDPOINT","default_health_endpoint":"https://api.openai.com/v1/models"},
 "gemini":{"label":"Google Gemini","adapter":"gemini","credential_env":("RESEARCH_OS_GEMINI_API_KEY","GEMINI_API_KEY"),"model_env":"RESEARCH_OS_GEMINI_MODEL","default_model":"gemini-2.5-flash","endpoint_env":"RESEARCH_OS_GEMINI_ENDPOINT","default_health_endpoint":"https://generativelanguage.googleapis.com/v1beta/models"}}
class AIProviderConnectionError(RuntimeError): pass
def _contract_sha(path:Path)->str:
 data=path.read_bytes(); return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def _now()->str: return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def _result_hash(payload:dict[str,Any])->str: return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
def _credential(provider:str)->str|None:
 for name in PROVIDERS[provider]["credential_env"]:
  value=os.getenv(name,"").strip()
  if value:return value
 return None
def _model(provider:str)->str:
 c=PROVIDERS[provider]; return os.getenv(c["model_env"],"").strip() or c["default_model"]
def _connector_available(provider:str)->bool:
 return os.getenv(f"RESEARCH_OS_{provider.upper()}_CONNECTOR_ENABLED","").strip().lower() in {"1","true","yes"}
def _health_check(provider:str)->tuple[bool,str]:
 c=PROVIDERS[provider]; credential=_credential(provider)
 if not credential:return False,"credential_missing"
 endpoint=os.getenv(c["endpoint_env"],"").strip() or c["default_health_endpoint"]
 headers={"Accept":"application/json"}
 if provider=="openai":headers["Authorization"]=f"Bearer {credential}"
 else:headers["x-goog-api-key"]=credential
 try:
  with urllib.request.urlopen(urllib.request.Request(endpoint,headers=headers,method="GET"),timeout=8) as response:
   return (True,"healthy") if 200<=response.status<300 else (False,f"http_{response.status}")
 except urllib.error.HTTPError as exc:
  if exc.code in {401,403}:return False,"credential_rejected"
  if exc.code in {429,500,502,503,504}:return False,f"provider_transient_{exc.code}"
  return False,f"http_{exc.code}"
 except (urllib.error.URLError,TimeoutError):return False,"provider_unreachable"
def _evidence(provider:str,operation:str,state:str,*,detail:str)->dict[str,Any]:
 r={"provider":provider,"operation":operation,"state":state,"source_sha":_contract_sha(CONTRACT_PATH),"timestamp":_now(),"result_hash":"","detail":detail,"secrets_excluded":True}
 r["result_hash"]=_result_hash({k:v for k,v in r.items() if k!="result_hash"});return r
def _append_evidence(record:dict[str,Any])->None:
 EVIDENCE_PATH.parent.mkdir(parents=True,exist_ok=True)
 with EVIDENCE_PATH.open("a",encoding="utf-8") as h:h.write(json.dumps(record,sort_keys=True,ensure_ascii=True)+"\n")
def inspect()->dict[str,Any]:
 providers=[]
 for provider,c in PROVIDERS.items():
  credential_present=_credential(provider) is not None; connector=_connector_available(provider)
  state,route=("CONNECTED","PLATFORM_CONNECTOR") if connector else (("API_FALLBACK","PLATFORM_API_FALLBACK") if credential_present else ("UNAVAILABLE","PLATFORM_API_FALLBACK"))
  providers.append({"id":provider,"label":c["label"],"adapter":c["adapter"],"state":state,"route":route,"credential_configured":credential_present,"model":_model(provider),"credential_env":list(c["credential_env"]),"secrets_excluded":True})
 return {"contract_id":"research-os-ai-provider-connection-v1","status":"ACTIVE","providers":providers,"states":list(STATES),"operations":["STATUS","CONNECT","DISCONNECT","HEALTH_CHECK"],"routing":{"primary":"PLATFORM_CONNECTOR","secondary":"PLATFORM_API_FALLBACK","flutter_direct_provider_calls":False},"authority":{"may_execute":False,"may_authorize":False,"may_approve":False,"may_merge":False,"may_release":False,"release_authority":"FINAL_GATE"},"source_sha":_contract_sha(CONTRACT_PATH),"evidence_contract_sha":_contract_sha(EVIDENCE_CONTRACT_PATH),"evidence_path":str(EVIDENCE_PATH.relative_to(ROOT)),"secrets_excluded":True}
def connect(provider:str)->dict[str,Any]:
 provider=provider.strip().lower()
 if provider not in PROVIDERS:raise AIProviderConnectionError(f"unsupported provider: {provider}")
 if _connector_available(provider):state,route,detail="CONNECTED","PLATFORM_CONNECTOR","connector_available"
 elif _credential(provider) is None:state,route,detail="UNAVAILABLE","PLATFORM_API_FALLBACK","credential_missing"
 else:
  healthy,detail=_health_check(provider);state="CONNECTED" if healthy else "API_FALLBACK";route="PLATFORM_API_FALLBACK"
 evidence=_evidence(provider,"CONNECT",state,detail=detail);_append_evidence(evidence)
 return {"provider":provider,"label":PROVIDERS[provider]["label"],"state":state,"route":route,"model":_model(provider),"credential_configured":_credential(provider) is not None,"evidence":evidence,"secrets_excluded":True}
def health_check(provider:str)->dict[str,Any]:
 provider=provider.strip().lower()
 if provider not in PROVIDERS:raise AIProviderConnectionError(f"unsupported provider: {provider}")
 if _connector_available(provider):state,route,detail="CONNECTED","PLATFORM_CONNECTOR","connector_available"
 elif _credential(provider) is None:state,route,detail="UNAVAILABLE","PLATFORM_API_FALLBACK","credential_missing"
 else:
  healthy,detail=_health_check(provider);state="CONNECTED" if healthy else "API_FALLBACK";route="PLATFORM_API_FALLBACK"
 evidence=_evidence(provider,"HEALTH_CHECK",state,detail=detail);_append_evidence(evidence)
 return {"provider":provider,"state":state,"route":route,"model":_model(provider),"detail":detail,"evidence":evidence,"secrets_excluded":True}
def disconnect(provider:str)->dict[str,Any]:
 provider=provider.strip().lower()
 if provider not in PROVIDERS:raise AIProviderConnectionError(f"unsupported provider: {provider}")
 evidence=_evidence(provider,"DISCONNECT","NOT_CONNECTED",detail="connection_state_cleared");_append_evidence(evidence)
 return {"provider":provider,"state":"NOT_CONNECTED","route":None,"credential_configured":_credential(provider) is not None,"evidence":evidence,"secrets_excluded":True}
if __name__=="__main__":print(json.dumps(inspect(),indent=2,ensure_ascii=False))
