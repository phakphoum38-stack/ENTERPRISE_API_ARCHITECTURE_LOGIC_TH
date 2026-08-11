#!/usr/bin/env python3
"""Live Research OS AI capability benchmark.

This benchmark exercises the public Research OS AI API rather than a vendor SDK.
It deliberately separates model-answer failures from provider/infrastructure
failures so a temporary HTTP error is never scored as a reasoning mistake.
Full model replies and secrets are not written to logs or reports.
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
CASE_MAX_ATTEMPTS = int(os.getenv("RESEARCH_OS_EVAL_CASE_ATTEMPTS", "2"))


class ProviderUnavailable(RuntimeError):
    def __init__(self, error_class: str, attempts: int):
        super().__init__(error_class)
        self.error_class = error_class
        self.attempts = attempts


def _clean(text: str) -> str:
    value = text.strip()
    value = re.sub(r"^```(?:json|text)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", _clean(text))


def _request_once(path: str, payload: dict[str, object]) -> tuple[dict[str, object], int]:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result, round((time.monotonic() - started) * 1000)


def _safe_http_error_class(exc: urllib.error.HTTPError) -> str:
    code = f"HTTP_{exc.code}"
    try:
        raw = exc.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
        if isinstance(payload, dict):
            error = str(payload.get("error", "")).strip()
            if error and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", error):
                return f"{code}_{error}"
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        pass
    return code


def _post(path: str, payload: dict[str, object]) -> tuple[dict[str, object], int, int]:
    last_error = "provider_unavailable"
    started = time.monotonic()
    for attempt in range(1, CASE_MAX_ATTEMPTS + 1):
        try:
            result, _ = _request_once(path, payload)
            elapsed_ms = round((time.monotonic() - started) * 1000)
            return result, elapsed_ms, attempt
        except urllib.error.HTTPError as exc:
            last_error = _safe_http_error_class(exc)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = type(exc).__name__
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = type(exc).__name__

        if attempt < CASE_MAX_ATTEMPTS:
            # The provider adapter already performs bounded retries internally.
            # This longer scenario-level pause handles a quota/service recovery
            # window without turning a temporary outage into an ability failure.
            time.sleep(8.0)

    raise ProviderUnavailable(last_error, CASE_MAX_ATTEMPTS)


@dataclass(frozen=True)
class EvalCase:
    name: str
    category: str
    path: str
    payload: dict[str, object]
    validator: Callable[[str], bool]
    critical: bool = False


def _exact(expected: str) -> Callable[[str], bool]:
    expected_compact = _compact(expected).casefold()
    return lambda text: _compact(text).casefold() == expected_compact


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
    uncertainty_markers = ("ยังไม่", "ไม่ยืนยัน", "ไม่แน่นอน", "ยังไม่ได้")
    return any(marker in value for marker in uncertainty_markers)


CASES = (
    EvalCase(
        name="thai_instruction_precision",
        category="instruction_following",
        path="/v1/ai/generate",
        payload={
            "prompt": "ตอบเพียงคำว่า พร้อม ห้ามใส่เครื่องหมายหรือคำอื่น",
            "system": "ทำตามรูปแบบคำตอบของผู้ใช้ให้เคร่งครัด",
        },
        validator=_exact("พร้อม"),
        critical=True,
    ),
    EvalCase(
        name="arithmetic_reasoning",
        category="reasoning",
        path="/v1/ai/generate",
        payload={
            "prompt": "มีกล่อง 17 กล่อง กล่องละ 24 ชิ้น แจกไป 53 ชิ้น เหลือกี่ชิ้น? ตอบตัวเลขอย่างเดียว",
        },
        validator=_exact("355"),
    ),
    EvalCase(
        name="constraint_ordering",
        category="reasoning",
        path="/v1/ai/generate",
        payload={
            "prompt": "เงื่อนไข: A มาก่อน B, C หลัง B, D ก่อน A. เรียง D A B C ให้ถูกต้องและตอบรูปแบบ D,A,B,C เท่านั้น",
        },
        validator=_exact("D,A,B,C"),
    ),
    EvalCase(
        name="conflict_detection",
        category="judgment",
        path="/v1/ai/generate",
        payload={
            "prompt": "ข้อมูลเดียวกันสองบรรทัด: นัดตรวจวันจันทร์เวลา 10:00 และนัดตรวจวันจันทร์เวลา 11:00 ถ้าขัดกันให้ตอบ CONFLICT เท่านั้น",
        },
        validator=_exact("CONFLICT"),
    ),
    EvalCase(
        name="uncertainty_no_hallucination",
        category="honesty",
        path="/v1/ai/generate",
        payload={
            "prompt": "คุณไม่มีภาพโต๊ะของฉันและไม่มีข้อมูลเพิ่มเติม หมายเลขซีเรียลบนอุปกรณ์ที่วางอยู่บนโต๊ะฉันคืออะไร? ถ้าไม่รู้ให้ตอบ UNKNOWN เท่านั้น",
        },
        validator=_exact("UNKNOWN"),
        critical=True,
    ),
    EvalCase(
        name="conversation_context_recall",
        category="memory_context",
        path="/v1/ai/answer-with-memory",
        payload={
            "question": "Conversation so far:\nUser: รหัสทดสอบคือ KITE-731\nAssistant: รับทราบ KITE-731\n\nUser: รหัสทดสอบคืออะไร? ตอบเฉพาะรหัส",
        },
        validator=_exact("KITE-731"),
        critical=True,
    ),
    EvalCase(
        name="ambiguity_clarification",
        category="wit",
        path="/v1/ai/generate",
        payload={
            "prompt": "ผู้ใช้บอกว่า 'ส่งไฟล์ให้เขาพรุ่งนี้' แต่ไม่มีข้อมูลว่า 'เขา' คือใคร อย่าเดาชื่อ ให้ถามกลับเพียง 1 ประโยคเพื่อแก้ความกำกวม",
        },
        validator=_ambiguity_check,
    ),
    EvalCase(
        name="false_premise_correction",
        category="wit",
        path="/v1/ai/generate",
        payload={
            "prompt": "มีคนบอกว่า 2+2=5 และถามว่า 'ถูกใช่ไหม' ตอบสั้น ๆ โดยแก้ข้อเท็จจริงให้ถูก",
        },
        validator=_correction_check,
    ),
    EvalCase(
        name="multi_constraint_json",
        category="instruction_following",
        path="/v1/ai/generate",
        payload={
            "prompt": "เหตุการณ์ด่วนต้องโทรแจ้งทันที ตอบเป็น JSON object เท่านั้น มี key แค่ priority และ next_action โดยค่าต้องเป็น priority=สูง และ next_action=โทรแจ้ง",
        },
        validator=_valid_json_constraint,
    ),
    EvalCase(
        name="thai_pragmatic_nuance",
        category="language_judgment",
        path="/v1/ai/generate",
        payload={
            "prompt": "ในบริบทงาน ถ้ามีคนตอบว่า 'เดี๋ยวค่อยว่ากัน' นี่ถือว่ายืนยันเวลานัดแน่นอนแล้วหรือยัง? ตอบภาษาไทย 1 ประโยค",
        },
        validator=_thai_nuance_check,
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
            results.append(
                {
                    "name": case.name,
                    "category": case.category,
                    "evaluated": True,
                    "passed": passed,
                    "critical": case.critical,
                    "elapsed_ms": elapsed_ms,
                    "attempts": attempts,
                    "response_received": bool(text.strip()),
                    "infrastructure_error": False,
                }
            )
        except ProviderUnavailable as exc:
            results.append(
                {
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
                }
            )

    evaluated = [result for result in results if result["evaluated"]]
    passed_count = sum(1 for result in evaluated if result["passed"])
    evaluated_count = len(evaluated)
    provider_errors = len(results) - evaluated_count
    ability_score = round(100 * passed_count / evaluated_count) if evaluated_count else 0
    coverage = round(100 * evaluated_count / len(results))
    critical_failed = [
        str(result["name"])
        for result in evaluated
        if result["critical"] and not result["passed"]
    ]
    critical_unavailable = [
        str(result["name"])
        for result in results
        if result["critical"] and not result["evaluated"]
    ]
    latencies = [
        int(result["elapsed_ms"])
        for result in evaluated
        if isinstance(result.get("elapsed_ms"), int)
    ]
    median_latency = round(statistics.median(latencies)) if latencies else None
    pass_threshold = 80
    capability_passed = ability_score >= pass_threshold and not critical_failed
    reliability_passed = provider_errors == 0 and not critical_unavailable
    overall_passed = capability_passed and reliability_passed
    if overall_passed:
        result_kind = "PASS"
    elif not reliability_passed and not capability_passed:
        result_kind = "FAIL_CAPABILITY_AND_RELIABILITY"
    elif not reliability_passed:
        result_kind = "FAIL_RELIABILITY"
    else:
        result_kind = "FAIL_CAPABILITY"

    report = {
        "benchmark": "research-os-live-ai-capability-v2",
        "provider": provider,
        "model": model,
        "score": ability_score,
        "ability_score": ability_score,
        "coverage_percent": coverage,
        "pass_threshold": pass_threshold,
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
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"AI_CAPABILITY_SCORE={ability_score}")
    print(f"AI_CAPABILITY_EVALUATED={evaluated_count}/{len(results)}")
    print(f"AI_CAPABILITY_PASSED={passed_count}/{evaluated_count or 0}")
    print(f"AI_CAPABILITY_PROVIDER_ERRORS={provider_errors}")
    print(f"AI_CAPABILITY_CRITICAL_FAILURES={len(critical_failed)}")
    print(f"AI_CAPABILITY_CRITICAL_UNAVAILABLE={len(critical_unavailable)}")
    print(f"AI_CAPABILITY_MEDIAN_LATENCY_MS={median_latency}")
    print(f"AI_CAPABILITY_RESULT={result_kind}")
    for result in results:
        if not result["evaluated"]:
            state = "INFRA"
        else:
            state = "PASS" if result["passed"] else "FAIL"
        print(
            f"  {state} {result['category']}/{result['name']} "
            f"({result.get('elapsed_ms')} ms, attempts={result.get('attempts')})"
        )

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
