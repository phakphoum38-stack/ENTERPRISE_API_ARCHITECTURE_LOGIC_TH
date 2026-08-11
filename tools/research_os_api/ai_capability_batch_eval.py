#!/usr/bin/env python3
"""Quota-safe live AI capability benchmark for Research OS.

Nine independent capability tasks are evaluated in a single generation call and
conversation recall is evaluated through answer-with-memory in one additional
call.  This keeps the live benchmark representative while remaining compatible
with low request-rate/free-tier provider quotas.

Full model responses and secrets are intentionally never written to logs or the
report.  Only normalized pass/fail metadata is persisted.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

BASE_URL = os.getenv("RESEARCH_OS_EVAL_BASE_URL", "http://127.0.0.1:8787").rstrip("/")
REPORT_PATH = Path(os.getenv("RESEARCH_OS_EVAL_REPORT", "ai-capability-report.json"))


def _clean(text: str) -> str:
    value = text.strip()
    value = re.sub(r"^```(?:json|text)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _post(path: str, payload: dict[str, object]) -> tuple[dict[str, Any], int]:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not surface the provider body: it can contain provider diagnostics
        # and should not be copied into capability artifacts.
        raise RuntimeError(f"HTTP_{exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(type(exc).__name__) from exc

    if not isinstance(decoded, dict):
        raise RuntimeError("unexpected_response_shape")
    return decoded, round((time.monotonic() - started) * 1000)


def _parse_json_text(text: str) -> dict[str, Any]:
    try:
        value = json.loads(_clean(text))
    except json.JSONDecodeError as exc:
        raise ValueError("model_response_not_json") from exc
    if not isinstance(value, dict):
        raise ValueError("model_response_not_object")
    return value


def _same(value: Any, expected: str) -> bool:
    return str(value).strip().casefold() == expected.casefold()


def _contains_uncertainty(value: Any) -> bool:
    text = str(value).strip().casefold()
    return any(marker in text for marker in ("ยังไม่", "ไม่ยืนยัน", "ไม่แน่นอน", "ยังไม่ได้"))


def _ambiguity_question(value: Any) -> bool:
    text = str(value).strip()
    return "ใคร" in text and ("?" in text or "ไหม" in text or "ครับ" in text or "คะ" in text) and len(text) <= 180


def _corrects_false_premise(value: Any) -> bool:
    text = str(value).strip()
    has_four = bool(re.search(r"(?<!\d)4(?!\d)", text))
    endorses_five = bool(re.search(r"(?:ถูก|ใช่|เท่ากับ)\s*5", text))
    return has_four and not endorses_five


def _structured_action(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value.keys()) == {"priority", "next_action"}
        and value.get("priority") == "สูง"
        and value.get("next_action") == "โทรแจ้ง"
    )


def _case(name: str, category: str, passed: bool, *, critical: bool = False) -> dict[str, object]:
    return {
        "name": name,
        "category": category,
        "evaluated": True,
        "passed": bool(passed),
        "critical": critical,
        "infrastructure_error": False,
    }


STATIC_PROMPT = """คุณกำลังทำ capability benchmark ของ Research OS
ทำโจทย์ทั้ง 9 ข้อต่อไปนี้แยกจากกัน ห้ามใช้คำตอบจากข้อหนึ่งเป็นข้อมูลของอีกข้อ
ตอบเป็น JSON object เพียงก้อนเดียว ห้าม markdown ห้ามคำอธิบายนอก JSON
ต้องมี key ทั้ง 9 key ตาม schema ด้านล่างเท่านั้น

1) instruction_precision:
ผู้ใช้สั่งว่า "ตอบเพียงคำว่า พร้อม ห้ามใส่เครื่องหมายหรือคำอื่น"

2) arithmetic_reasoning:
มีกล่อง 17 กล่อง กล่องละ 24 ชิ้น แจกไป 53 ชิ้น เหลือกี่ชิ้น? ตอบเป็นจำนวนเต็ม

3) constraint_ordering:
A มาก่อน B, C หลัง B, D ก่อน A. ตอบลำดับในรูป "D,A,B,C"

4) conflict_detection:
ข้อมูลเดียวกันระบุว่า นัดตรวจวันจันทร์ 10:00 และนัดตรวจวันจันทร์ 11:00
ถ้าขัดกันให้ตอบ "CONFLICT"

5) uncertainty_no_hallucination:
คุณไม่มีภาพโต๊ะของผู้ใช้และไม่มีข้อมูลอื่น หมายเลขซีเรียลบนอุปกรณ์ที่วางอยู่บนโต๊ะคืออะไร?
ถ้าไม่รู้ให้ตอบ "UNKNOWN"

6) ambiguity_clarification:
ผู้ใช้บอกว่า "ส่งไฟล์ให้เขาพรุ่งนี้" แต่ไม่มีข้อมูลว่า "เขา" คือใคร
อย่าเดาชื่อ ให้ถามกลับ 1 ประโยคเพื่อแก้ความกำกวม

7) false_premise_correction:
มีคนบอกว่า 2+2=5 และถามว่า "ถูกใช่ไหม" ตอบสั้น ๆ โดยแก้ข้อเท็จจริงให้ถูก

8) multi_constraint_json:
เหตุการณ์ด่วนต้องโทรแจ้งทันที ให้สร้าง object ที่มี key แค่ priority และ next_action
โดย priority ต้องเป็น "สูง" และ next_action ต้องเป็น "โทรแจ้ง"

9) thai_pragmatic_nuance:
ในบริบทงาน ถ้ามีคนตอบว่า "เดี๋ยวค่อยว่ากัน" ถือว่ายืนยันเวลานัดแน่นอนแล้วหรือยัง?
ตอบภาษาไทย 1 ประโยค

schema ที่ต้องตอบ:
{
  "instruction_precision": "...",
  "arithmetic_reasoning": 0,
  "constraint_ordering": "...",
  "conflict_detection": "...",
  "uncertainty_no_hallucination": "...",
  "ambiguity_clarification": "...",
  "false_premise_correction": "...",
  "multi_constraint_json": {"priority": "...", "next_action": "..."},
  "thai_pragmatic_nuance": "..."
}
"""


def main() -> int:
    results: list[dict[str, object]] = []
    provider = "unknown"
    model = "unknown"
    latencies: list[int] = []
    infrastructure_errors: list[str] = []

    try:
        generated, elapsed_ms = _post("/v1/ai/generate", {"prompt": STATIC_PROMPT})
        latencies.append(elapsed_ms)
        provider = str(generated.get("provider") or provider)
        model = str(generated.get("model") or model)
        answers = _parse_json_text(str(generated.get("text") or ""))

        results.extend(
            [
                _case(
                    "thai_instruction_precision",
                    "instruction_following",
                    _same(answers.get("instruction_precision"), "พร้อม"),
                    critical=True,
                ),
                _case(
                    "arithmetic_reasoning",
                    "reasoning",
                    answers.get("arithmetic_reasoning") == 355
                    or _same(answers.get("arithmetic_reasoning"), "355"),
                ),
                _case(
                    "constraint_ordering",
                    "reasoning",
                    _same(answers.get("constraint_ordering"), "D,A,B,C"),
                ),
                _case(
                    "conflict_detection",
                    "judgment",
                    _same(answers.get("conflict_detection"), "CONFLICT"),
                ),
                _case(
                    "uncertainty_no_hallucination",
                    "honesty",
                    _same(answers.get("uncertainty_no_hallucination"), "UNKNOWN"),
                    critical=True,
                ),
                _case(
                    "ambiguity_clarification",
                    "wit",
                    _ambiguity_question(answers.get("ambiguity_clarification")),
                ),
                _case(
                    "false_premise_correction",
                    "wit",
                    _corrects_false_premise(answers.get("false_premise_correction")),
                ),
                _case(
                    "multi_constraint_json",
                    "instruction_following",
                    _structured_action(answers.get("multi_constraint_json")),
                ),
                _case(
                    "thai_pragmatic_nuance",
                    "language_judgment",
                    _contains_uncertainty(answers.get("thai_pragmatic_nuance")),
                ),
            ]
        )
    except (RuntimeError, ValueError) as exc:
        infrastructure_errors.append(f"static_batch:{type(exc).__name__}:{exc}")
        for name, category, critical in (
            ("thai_instruction_precision", "instruction_following", True),
            ("arithmetic_reasoning", "reasoning", False),
            ("constraint_ordering", "reasoning", False),
            ("conflict_detection", "judgment", False),
            ("uncertainty_no_hallucination", "honesty", True),
            ("ambiguity_clarification", "wit", False),
            ("false_premise_correction", "wit", False),
            ("multi_constraint_json", "instruction_following", False),
            ("thai_pragmatic_nuance", "language_judgment", False),
        ):
            results.append(
                {
                    "name": name,
                    "category": category,
                    "evaluated": False,
                    "passed": False,
                    "critical": critical,
                    "infrastructure_error": True,
                }
            )

    try:
        memory, elapsed_ms = _post(
            "/v1/ai/answer-with-memory",
            {
                "question": (
                    "Conversation so far:\n"
                    "User: รหัสทดสอบบริบทคือ KITE-731\n"
                    "Assistant: รับทราบ KITE-731\n\n"
                    "User: รหัสทดสอบบริบทคืออะไร? ตอบให้มีรหัสนั้นในคำตอบ"
                )
            },
        )
        latencies.append(elapsed_ms)
        provider = str(memory.get("provider") or provider)
        model = str(memory.get("model") or model)
        memory_text = str(memory.get("text") or memory.get("answer") or "")
        results.append(
            _case(
                "conversation_context_recall",
                "memory_context",
                "KITE-731" in memory_text,
                critical=True,
            )
        )
    except RuntimeError as exc:
        infrastructure_errors.append(f"memory_context:{type(exc).__name__}:{exc}")
        results.append(
            {
                "name": "conversation_context_recall",
                "category": "memory_context",
                "evaluated": False,
                "passed": False,
                "critical": True,
                "infrastructure_error": True,
            }
        )

    evaluated = [item for item in results if item["evaluated"]]
    passed_count = sum(1 for item in evaluated if item["passed"])
    evaluated_count = len(evaluated)
    total_count = len(results)
    provider_errors = total_count - evaluated_count
    ability_score = round(100 * passed_count / evaluated_count) if evaluated_count else 0
    coverage = round(100 * evaluated_count / total_count) if total_count else 0
    critical_failures = [
        str(item["name"])
        for item in evaluated
        if item["critical"] and not item["passed"]
    ]
    critical_unavailable = [
        str(item["name"])
        for item in results
        if item["critical"] and not item["evaluated"]
    ]
    capability_passed = ability_score >= 80 and not critical_failures
    reliability_passed = provider_errors == 0 and not critical_unavailable
    overall_passed = capability_passed and reliability_passed

    if overall_passed:
        result_kind = "PASS"
    elif not capability_passed and not reliability_passed:
        result_kind = "FAIL_CAPABILITY_AND_RELIABILITY"
    elif not capability_passed:
        result_kind = "FAIL_CAPABILITY"
    else:
        result_kind = "FAIL_RELIABILITY"

    report = {
        "benchmark": "research-os-live-ai-capability-batch-v1",
        "provider": provider,
        "model": model,
        "ability_score": ability_score,
        "coverage_percent": coverage,
        "pass_threshold": 80,
        "passed_cases": passed_count,
        "evaluated_cases": evaluated_count,
        "total_cases": total_count,
        "provider_errors": provider_errors,
        "critical_failures": critical_failures,
        "critical_unavailable": critical_unavailable,
        "median_request_latency_ms": round(statistics.median(latencies)) if latencies else None,
        "live_model_calls": 2,
        "capability_passed": capability_passed,
        "reliability_passed": reliability_passed,
        "overall_passed": overall_passed,
        "result_kind": result_kind,
        "responses_logged": False,
        "infrastructure_error_classes": infrastructure_errors,
        "cases": results,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"AI_CAPABILITY_SCORE={ability_score}")
    print(f"AI_CAPABILITY_EVALUATED={evaluated_count}/{total_count}")
    print(f"AI_CAPABILITY_PASSED={passed_count}/{evaluated_count or 0}")
    print(f"AI_CAPABILITY_PROVIDER_ERRORS={provider_errors}")
    print(f"AI_CAPABILITY_CRITICAL_FAILURES={len(critical_failures)}")
    print(f"AI_CAPABILITY_CRITICAL_UNAVAILABLE={len(critical_unavailable)}")
    print(f"AI_CAPABILITY_LIVE_MODEL_CALLS=2")
    print(f"AI_CAPABILITY_RESULT={result_kind}")
    for item in results:
        state = "INFRA" if not item["evaluated"] else ("PASS" if item["passed"] else "FAIL")
        print(f"  {state} {item['category']}/{item['name']}")

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
