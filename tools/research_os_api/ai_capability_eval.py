#!/usr/bin/env python3
"""Live Research OS AI capability benchmark.

Measures model ability through the public Research OS API while separating
model-answer failures from transient provider/infrastructure errors. Full model
replies and API secrets are intentionally never written to logs or reports.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

BASE_URL = os.getenv("RESEARCH_OS_EVAL_BASE_URL", "http://127.0.0.1:8787").rstrip("/")
REPORT_PATH = Path(os.getenv("RESEARCH_OS_EVAL_REPORT", "ai-capability-report.json"))
CASE_COOLDOWN_SECONDS = float(os.getenv("RESEARCH_OS_EVAL_CASE_COOLDOWN", "2"))
# Always allow at least three scenario attempts. The provider adapter already
# does bounded HTTP-level retries; these attempts cover a longer recovery window.
CASE_MAX_ATTEMPTS = max(3, int(os.getenv("RESEARCH_OS_EVAL_CASE_ATTEMPTS", "3")))


class ProviderUnavailable(RuntimeError):
    def __init__(self, error_class: str, attempts: int):
        super().__init__(error_class)
        self.error_class = error_class
        self.attempts = attempts


@dataclass(frozen=True)
class EvalCase:
    name: str
    category: str
    path: str
    payload: dict[str, object]
    validator: Callable[[str], bool]
    critical: bool = False


def _clean(text: str) -> str:
    value = text.strip()
    value = re.sub(r"^```(?:json|text)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", _clean(text))


def _exact(expected: str) -> Callable[[str], bool]:
    target = _compact(expected).casefold()
    return lambda text: _compact(text).casefold() == target


def _contains_marker(marker: str) -> Callable[[str], bool]:
    target = marker.casefold()
    return lambda text: target in _clean(text).casefold()


def _valid_json_constraint(text: str) -> bool:
    try:
        value = json.loads(_clean(text))
    except json.JSONDecodeError:
        return False
    return (
        isinstance(value, dict)
        and set(value) == {"priority", "next_action"}
        and value.get("priority") == "สูง"
        and value.get("next_action") == "โทรแจ้ง"
    )


def _ambiguity_check(text: str) -> bool:
    value = _clean(text)
    return "ใคร" in value and len(value) <= 180


def _correction_check(text: str) -> bool:
    value = _clean(text)
    return bool(re.search(r"(?<!\d)4(?!\d)", value)) and "ถูกต้องว่า 5" not in value


def _thai_nuance_check(text: str) -> bool:
    value = _clean(text).casefold()
    return any(mark in value for mark in ("ยังไม่", "ไม่ยืนยัน", "ไม่แน่นอน", "ยังไม่ได้"))


def _safe_http_error_class(exc: urllib.error.HTTPError) -> str:
    base = f"HTTP_{exc.code}"
    try:
        payload = json.loads(exc.read().decode("utf-8", errors="replace"))
        if isinstance(payload, dict):
            error = str(payload.get("error", "")).strip()
            if error and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", error):
                return f"{base}_{error}"
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        pass
    return base


def _request_once(path: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("unexpected_response_shape")
    return decoded


def _post(path: str, payload: dict[str, object]) -> tuple[dict[str, object], int, int]:
    started = time.monotonic()
    last_error = "provider_unavailable"
    for attempt in range(1, CASE_MAX_ATTEMPTS + 1):
        try:
            result = _request_once(path, payload)
            return result, round((time.monotonic() - started) * 1000), attempt
        except urllib.error.HTTPError as exc:
            last_error = _safe_http_error_class(exc)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
            last_error = type(exc).__name__
        if attempt < CASE_MAX_ATTEMPTS:
            time.sleep(8.0)
    raise ProviderUnavailable(last_error, CASE_MAX_ATTEMPTS)


CASES = (
    EvalCase(
        "thai_instruction_precision",
        "instruction_following",
        "/v1/ai/generate",
        {"prompt": "ตอบเพียงคำว่า พร้อม ห้ามใส่เครื่องหมายหรือคำอื่น"},
        _exact("พร้อม"),
        True,
    ),
    EvalCase(
        "arithmetic_reasoning",
        "reasoning",
        "/v1/ai/generate",
        {"prompt": "มีกล่อง 17 กล่อง กล่องละ 24 ชิ้น แจกไป 53 ชิ้น เหลือกี่ชิ้น? ตอบตัวเลขอย่างเดียว"},
        _exact("355"),
    ),
    EvalCase(
        "constraint_ordering",
        "reasoning",
        "/v1/ai/generate",
        {"prompt": "เงื่อนไข: A มาก่อน B, C หลัง B, D ก่อน A. ตอบ D,A,B,C เท่านั้น"},
        _exact("D,A,B,C"),
    ),
    EvalCase(
        "conflict_detection",
        "judgment",
        "/v1/ai/generate",
        {"prompt": "นัดตรวจวันจันทร์ 10:00 และนัดตรวจวันจันทร์ 11:00 เป็นข้อมูลเดียวกัน ถ้าขัดกันตอบ CONFLICT เท่านั้น"},
        _exact("CONFLICT"),
    ),
    EvalCase(
        "uncertainty_no_hallucination",
        "honesty",
        "/v1/ai/generate",
        {"prompt": "คุณไม่มีภาพโต๊ะของฉัน หมายเลขซีเรียลบนอุปกรณ์บนโต๊ะคืออะไร? ถ้าไม่รู้ตอบ UNKNOWN เท่านั้น"},
        _exact("UNKNOWN"),
        True,
    ),
    EvalCase(
        "conversation_context_recall",
        "memory_context",
        "/v1/ai/answer-with-memory",
        {"question": "Conversation so far:\nUser: รหัสทดสอบคือ KITE-731\nAssistant: รับทราบ KITE-731\n\nUser: รหัสทดสอบคืออะไร?"},
        _contains_marker("KITE-731"),
        True,
    ),
    EvalCase(
        "ambiguity_clarification",
        "wit",
        "/v1/ai/generate",
        {"prompt": "ผู้ใช้บอกว่า 'ส่งไฟล์ให้เขาพรุ่งนี้' แต่ไม่มีข้อมูลว่า 'เขา' คือใคร อย่าเดาชื่อ ให้ถามกลับ 1 ประโยคเพื่อแก้ความกำกวม"},
        _ambiguity_check,
    ),
    EvalCase(
        "false_premise_correction",
        "wit",
        "/v1/ai/generate",
        {"prompt": "มีคนบอกว่า 2+2=5 และถามว่า 'ถูกใช่ไหม' ตอบสั้น ๆ โดยแก้ข้อเท็จจริงให้ถูก"},
        _correction_check,
    ),
    EvalCase(
        "multi_constraint_json",
        "instruction_following",
        "/v1/ai/generate",
        {"prompt": "เหตุการณ์ด่วนต้องโทรแจ้งทันที ตอบ JSON object เท่านั้น มี key แค่ priority และ next_action ค่า priority=สูง และ next_action=โทรแจ้ง"},
        _valid_json_constraint,
    ),
    EvalCase(
        "thai_pragmatic_nuance",
        "language_judgment",
        "/v1/ai/generate",
        {"prompt": "ในบริบทงาน ถ้ามีคนตอบว่า 'เดี๋ยวค่อยว่ากัน' ถือว่ายืนยันเวลานัดแน่นอนแล้วหรือยัง? ตอบไทย 1 ประโยค"},
        _thai_nuance_check,
    ),
)


def main() -> int:
    results: list[dict[str, object]] = []
    provider = "unknown"
    model = "unknown"

    for index, case in enumerate(CASES):
        if index:
            time.sleep(CASE_COOLDOWN_SECONDS)
        try:
            payload, elapsed_ms, attempts = _post(case.path, case.payload)
            provider = str(payload.get("provider") or provider)
            model = str(payload.get("model") or model)
            text = str(payload.get("text") or payload.get("answer") or "")
            passed = bool(text.strip()) and case.validator(text)
            results.append({
                "name": case.name,
                "category": case.category,
                "evaluated": True,
                "passed": passed,
                "critical": case.critical,
                "elapsed_ms": elapsed_ms,
                "attempts": attempts,
                "response_received": bool(text.strip()),
                "infrastructure_error": False,
            })
        except ProviderUnavailable as exc:
            results.append({
                "name": case.name,
                "category": case.category,
                "evaluated": False,
                "passed": False,
                "critical": case.critical,
                "elapsed_ms": None,
                "attempts": exc.attempts,
                "response_received": False,
                "infrastructure_error": True,
                "error_class": exc.error_class,
            })

    evaluated = [r for r in results if r["evaluated"]]
    passed_count = sum(1 for r in evaluated if r["passed"])
    evaluated_count = len(evaluated)
    provider_errors = len(results) - evaluated_count
    ability_score = round(100 * passed_count / evaluated_count) if evaluated_count else 0
    coverage = round(100 * evaluated_count / len(results))
    critical_failed = [str(r["name"]) for r in evaluated if r["critical"] and not r["passed"]]
    critical_unavailable = [str(r["name"]) for r in results if r["critical"] and not r["evaluated"]]
    latencies = [int(r["elapsed_ms"]) for r in evaluated if isinstance(r.get("elapsed_ms"), int)]
    median_latency = round(statistics.median(latencies)) if latencies else None
    capability_passed = ability_score >= 80 and not critical_failed
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
        "benchmark": "research-os-live-ai-capability-v3",
        "provider": provider,
        "model": model,
        "score": ability_score,
        "ability_score": ability_score,
        "coverage_percent": coverage,
        "pass_threshold": 80,
        "passed_cases": passed_count,
        "evaluated_cases": evaluated_count,
        "total_cases": len(results),
        "provider_errors": provider_errors,
        "critical_failures": critical_failed,
        "critical_unavailable": critical_unavailable,
        "median_latency_ms": median_latency,
        "capability_passed": capability_passed,
        "reliability_passed": reliability_passed,
        "overall_passed": overall_passed,
        "result_kind": result_kind,
        "responses_logged": False,
        "cases": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"AI_CAPABILITY_SCORE={ability_score}")
    print(f"AI_CAPABILITY_EVALUATED={evaluated_count}/{len(results)}")
    print(f"AI_CAPABILITY_PASSED={passed_count}/{evaluated_count or 0}")
    print(f"AI_CAPABILITY_PROVIDER_ERRORS={provider_errors}")
    print(f"AI_CAPABILITY_CRITICAL_FAILURES={len(critical_failed)}")
    print(f"AI_CAPABILITY_CRITICAL_UNAVAILABLE={len(critical_unavailable)}")
    print(f"AI_CAPABILITY_MEDIAN_LATENCY_MS={median_latency}")
    print(f"AI_CAPABILITY_RESULT={result_kind}")
    for result in results:
        state = "INFRA" if not result["evaluated"] else ("PASS" if result["passed"] else "FAIL")
        print(f"  {state} {result['category']}/{result['name']} ({result.get('elapsed_ms')} ms, attempts={result.get('attempts')})")

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
