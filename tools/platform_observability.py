#!/usr/bin/env python3
REQUIRED=("request_id","correlation_id","actor","contract_version")
LINEAGE=("request","workflow","delivery","worker","evidence","audit","gate")
def validate(context:dict,lineage:list[str])->dict:
    missing=[k for k in REQUIRED if not context.get(k)]
    absent=[k for k in LINEAGE if k not in lineage]
    return {"status":"PASS" if not missing and not absent else "HOLD","missing_context":missing,"missing_lineage":absent,"health_is_not_authorization":True}
