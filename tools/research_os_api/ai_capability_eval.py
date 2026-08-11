#!/usr/bin/env python3
"""Live Research OS AI capability benchmark.

The benchmark exercises the public Research OS AI API instead of calling a
vendor SDK directly. It records only pass/fail metadata and latency; full model
responses and secrets are intentionally not written to logs or reports.
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


def _clean(text: str) -> str:
    value = text.strip()
    value = re.sub(r"^```(?:json|text)?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*```$", "", value)
    return value.strip()


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", _clean(text))


def _post(path: str, payload: dict[str, object]) -> tuple[dict[str, object], int]:
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


def _contains(expected: str) -> Callable[[str], bool]:
    expected_folded = expected.casefold()
    return lambda text: expected_folded in _clean(text).casefold()


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

    for case in CASES:
        try:
            payload, elapsed_ms = _post(case.path, case.payload)
            provider = str(payload.get("provider") or provider)
            model = str(payload.get("model") or model)
            text = str(payload.get("text") or payload.get("answer") or "")
            passed = bool(text.strip()) and case.validator(text)
            results.append(
                {
                    "name": case.name,
                    "category": case.category,
                    "passed": passed,
                    "critical": case.critical,
                    "elapsed_ms": elapsed_ms,
                    "response_received": bool(text.strip()),
                }
            )
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            results.append(
                {
                    "name": case.name,
                    "category": case.category,
                    "passed": False,
                    "critical": case.critical,
                    "elapsed_ms": None,
                    "response_received": False,
                    "error_type": type(exc).__name__,
                }
            )

    passed_count = sum(1 for result in results if result["passed"])
    critical_failed = [
        str(result["name"])
        for result in results
        if result["critical"] and not result["passed"]
    ]
    score = round(100 * passed_count / len(results))
    latencies = [
        int(result["elapsed_ms"])
        for result in results
        if isinstance(result.get("elapsed_ms"), int)
    ]
    median_latency = round(statistics.median(latencies)) if latencies else None
    pass_threshold = 80
    overall_passed = score >= pass_threshold and not critical_failed

    report = {
        "benchmark": "research-os-live-ai-capability-v1",
        "provider": provider,
        "model": model,
        "score": score,
        "pass_threshold": pass_threshold,
        "passed_cases": passed_count,
        "total_cases": len(results),
        "critical_failures": critical_failed,
        "median_latency_ms": median_latency,
        "overall_passed": overall_passed,
        "responses_logged": False,
        "cases": results,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"AI_CAPABILITY_SCORE={score}")
    print(f"AI_CAPABILITY_PASSED={passed_count}/{len(results)}")
    print(f"AI_CAPABILITY_CRITICAL_FAILURES={len(critical_failed)}")
    print(f"AI_CAPABILITY_MEDIAN_LATENCY_MS={median_latency}")
    print(f"AI_CAPABILITY_RESULT={'PASS' if overall_passed else 'FAIL'}")
    for result in results:
        state = "PASS" if result["passed"] else "FAIL"
        print(f"  {state} {result['category']}/{result['name']} ({result.get('elapsed_ms')} ms)")

    return 0 if overall_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
