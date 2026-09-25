#!/usr/bin/env python3
"""Secret-safe, read-only AI provider connection control.

This module reports and validates the canonical OpenAI/GPT and Gemini connection
boundary. It never returns credentials and never grants execution authority.
"""
from __future__ import annotations
import hashlib, json, os
from dataclasses import dataclass, asdict

CONTRACT="current/RESEARCH_OS_AI_PROVIDER_CONNECTION_CONTRACT.json"
PROVIDERS={
 "openai":{"label":"OpenAI / GPT","adapter":"openai-compatible","key":"RESEARCH_OS_OPENAI_API_KEY","endpoint":"RESEARCH_OS_OPENAI_ENDPOINT","model":"RESEARCH_OS_OPENAI_MODEL"},
 "gemini":{"label":"Google Gemini","adapter":"gemini","key":"RESEARCH_OS_GEMINI_API_KEY","endpoint":"RESEARCH_OS_GEMINI_ENDPOINT_TEMPLATE","model":"RESEARCH_OS_GEMINI_MODEL"},
}
@dataclass(frozen=True)
class ProviderStatus:
 provider:str
 label:str
 state:str
 adapter:str
 credential_configured:bool
 endpoint_configured:bool
 model_configured:bool
 api_fallback_available:bool
 secret_exposed:bool=False

def _configured(name:str)->ProviderStatus:
 if name not in PROVIDERS: raise ValueError(f"unsupported provider: {name}")
 p=PROVIDERS[name]
 key_ok=bool(os.getenv(p["key"]))
 endpoint_ok=bool(os.getenv(p["endpoint"])) or name=="openai"
 model_ok=bool(os.getenv(p["model"]))
 if key_ok and model_ok: state="CONNECTED"
 elif key_ok or model_ok: state="DEGRADED"
 else: state="NOT_CONNECTED"
 return ProviderStatus(name,p["label"],state,p["adapter"],key_ok,endpoint_ok,model_ok,True)

def inspect()->dict:
 items=[asdict(_configured(name)) for name in PROVIDERS]
 return {"contract":CONTRACT,"providers":items,"routing":{"primary":"PLATFORM_CONNECTOR","secondary":"PLATFORM_API_FALLBACK"},"authority":"FINAL_GATE","safe":all(not x["secret_exposed"] for x in items)}

def evidence(provider:str, operation:str, state:str, source_sha:str)->dict:
 raw=f"{provider}|{operation}|{state}|{source_sha}".encode()
 return {"provider":provider,"operation":operation,"state":state,"source_sha":source_sha,"result_hash":hashlib.sha256(raw).hexdigest(),"secret_exposed":False}

if __name__=="__main__":
 print(json.dumps(inspect(),ensure_ascii=False,indent=2))
