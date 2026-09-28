from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_duration(value: str) -> timedelta:
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"invalid duration: {value}")
    return timedelta(hours=int(parts[0]), minutes=int(parts[1]))


@dataclass(frozen=True)
class Department:
    id: str
    code: str
    name: str


@dataclass(frozen=True)
class Employee:
    id: str
    employee_code: str
    first_name: str
    last_name: str
    nickname: str
    department: Department
    position: str
    active: bool = True


@dataclass(frozen=True)
class ShiftType:
    id: str
    code: str
    name: str
    start_time: timedelta
    end_time: timedelta
    working_hours: float

    def is_night_shift(self) -> bool:
        return (
            self.start_time >= timedelta(hours=18)
            or self.end_time <= self.start_time
        )


@dataclass(frozen=True)
class ShiftAssignment:
    employee_id: str
    shift_type_id: str
    location: str | None = None
    remark: str | None = None


@dataclass
class ScheduleDay:
    date: date
    assignments: list[ShiftAssignment] = field(default_factory=list)
    holiday_name: str | None = None

    @property
    def is_holiday(self) -> bool:
        return (
            self.holiday_name is not None
            or self.date.weekday() >= 5
        )


@dataclass
class Schedule:
    id: str
    name: str
    days: dict[date, ScheduleDay] = field(default_factory=dict)

    @classmethod
    def empty_month(cls, year: int, month: int, *, schedule_id: str = "schedule", name: str = "Schedule") -> "Schedule":
        first = date(year, month, 1)
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)

        days: dict[date, ScheduleDay] = {}
        current = first
        while current < next_month:
            days[current] = ScheduleDay(current)
            current += timedelta(days=1)

        return cls(id=schedule_id, name=name, days=days)

    def day(self, target: date) -> ScheduleDay:
        if target not in self.days:
            self.days[target] = ScheduleDay(target)
        return self.days[target]

    def copy(self) -> "Schedule":
        return Schedule(
            id=self.id,
            name=self.name,
            days={
                d: ScheduleDay(
                    date=day.date,
                    assignments=list(day.assignments),
                    holiday_name=day.holiday_name,
                )
                for d, day in self.days.items()
            },
        )


@dataclass(frozen=True)
class CoverageRequirement:
    id: str
    date: date
    department_id: str
    shift_type_id: str
    required_employees: int
    location: str | None = None


@dataclass(frozen=True)
class EmployeeAvailability:
    employee_id: str
    date: date
    available: bool = True
    shift_type_ids: frozenset[str] = frozenset()

    def allows(self, shift_type_id: str) -> bool:
        return self.available and (
            not self.shift_type_ids
            or shift_type_id in self.shift_type_ids
        )


@dataclass(frozen=True)
class DepartmentCapacity:
    department_id: str
    date: date
    maximum_assignments: int


class ConflictType:
    DUPLICATE_ASSIGNMENT = "duplicateAssignment"
    OVERLAPPING_SHIFT = "overlappingShift"
    UNAVAILABLE_EMPLOYEE = "unavailableEmployee"
    DEPARTMENT_CAPACITY = "departmentCapacity"
    INSUFFICIENT_COVERAGE = "insufficientCoverage"


@dataclass(frozen=True)
class ScheduleConflict:
    type: str
    message: str
    severity: str
    employee_id: str | None = None
    date: date | None = None
    requirement_id: str | None = None


@dataclass(frozen=True)
class GenerationResult:
    schedule: Schedule
    conflicts: tuple[ScheduleConflict, ...]
    uncovered_requirements: tuple[CoverageRequirement, ...]
    assignments_created: int

    @property
    def completed(self) -> bool:
        return (
            not self.uncovered_requirements
            and not any(c.severity == "error" for c in self.conflicts)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "assignments_created": self.assignments_created,
            "conflicts": [
                {
                    "type": c.type,
                    "message": c.message,
                    "severity": c.severity,
                    "employee_id": c.employee_id,
                    "date": c.date.isoformat() if c.date else None,
                    "requirement_id": c.requirement_id,
                }
                for c in self.conflicts
            ],
            "uncovered_requirements": [
                {
                    "id": r.id,
                    "date": r.date.isoformat(),
                    "department_id": r.department_id,
                    "shift_type_id": r.shift_type_id,
                    "required_employees": r.required_employees,
                    "location": r.location,
                }
                for r in self.uncovered_requirements
            ],
            "schedule": {
                "id": self.schedule.id,
                "name": self.schedule.name,
                "days": {
                    d.isoformat(): [
                        {
                            "employee_id": a.employee_id,
                            "shift_type_id": a.shift_type_id,
                            "location": a.location,
                            "remark": a.remark,
                        }
                        for a in day.assignments
                    ]
                    for d, day in sorted(self.schedule.days.items())
                },
            },
        }
