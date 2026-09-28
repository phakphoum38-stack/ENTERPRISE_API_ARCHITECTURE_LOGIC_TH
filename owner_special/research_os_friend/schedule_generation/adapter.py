from __future__ import annotations

import json
from datetime import date

from .generator import ScheduleGenerator
from .models import (
    CoverageRequirement,
    Department,
    DepartmentCapacity,
    Employee,
    EmployeeAvailability,
    Schedule,
    ShiftType,
    parse_duration,
)


class ScheduleGenerateTool:
    """
    Deterministic schedule-generation boundary.

    Input is an explicit JSON command envelope. No LLM interpretation is used
    for schedule data.
    """

    name = "schedule.generate"
    description = (
        "Deterministically generate or validate a duty schedule from an "
        "explicit structured command."
    )

    def __init__(self) -> None:
        self.generator = ScheduleGenerator()

    def __call__(self, text: str) -> str:
        payload = json.loads(text)

        operation = payload.get("operation", "auto")

        if operation != "auto":
            raise ValueError(
                f"unsupported schedule.generate operation: {operation}"
            )

        month = date.fromisoformat(
            payload["month"] + "-01"
        )

        schedule_payload = payload.get("schedule", {})
        schedule = Schedule.empty_month(
            month.year,
            month.month,
            schedule_id=schedule_payload.get("id", "schedule"),
            name=schedule_payload.get("name", "Schedule"),
        )

        employees = [
            self._employee(item)
            for item in payload.get("employees", [])
        ]

        shift_types = [
            ShiftType(
                id=item["id"],
                code=item["code"],
                name=item["name"],
                start_time=parse_duration(item["start_time"]),
                end_time=parse_duration(item["end_time"]),
                working_hours=float(item["working_hours"]),
            )
            for item in payload.get("shift_types", [])
        ]

        requirements = [
            CoverageRequirement(
                id=item["id"],
                date=date.fromisoformat(item["date"]),
                department_id=item["department_id"],
                shift_type_id=item["shift_type_id"],
                required_employees=int(item["required_employees"]),
                location=item.get("location"),
            )
            for item in payload.get("coverage_requirements", [])
        ]

        availability = [
            EmployeeAvailability(
                employee_id=item["employee_id"],
                date=date.fromisoformat(item["date"]),
                available=bool(item.get("available", True)),
                shift_type_ids=frozenset(
                    item.get("shift_type_ids", [])
                ),
            )
            for item in payload.get("availability", [])
        ]

        capacities = [
            DepartmentCapacity(
                department_id=item["department_id"],
                date=date.fromisoformat(item["date"]),
                maximum_assignments=int(item["maximum_assignments"]),
            )
            for item in payload.get("department_capacities", [])
        ]

        result = self.generator.auto_assign(
            schedule=schedule,
            month=month,
            employees=employees,
            shift_types=shift_types,
            coverage_requirements=requirements,
            availability=availability,
            department_capacities=capacities,
            locked_duty_points_by_employee_id=payload.get(
                "locked_duty_points",
                {},
            ),
        )

        return json.dumps(
            result.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )

    @staticmethod
    def _employee(item: dict) -> Employee:
        department_payload = item["department"]

        return Employee(
            id=item["id"],
            employee_code=item["employee_code"],
            first_name=item["first_name"],
            last_name=item["last_name"],
            nickname=item.get("nickname", ""),
            department=Department(
                id=department_payload["id"],
                code=department_payload["code"],
                name=department_payload["name"],
            ),
            position=item["position"],
            active=bool(item.get("active", True)),
        )
