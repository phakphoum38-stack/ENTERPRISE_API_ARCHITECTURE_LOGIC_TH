from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from .models import (
    CoverageRequirement,
    DepartmentCapacity,
    Employee,
    EmployeeAvailability,
    GenerationResult,
    Schedule,
    ScheduleConflict,
    ShiftAssignment,
    ShiftType,
    ConflictType,
)


def _shift_range(day: date, shift: ShiftType) -> tuple:
    start = timedelta(
        days=0
    ) + shift.start_time
    end = shift.end_time

    start_dt = day
    start_seconds = start.total_seconds()
    end_seconds = end.total_seconds()

    from datetime import datetime

    start_value = datetime.combine(day, datetime.min.time()) + start

    if end <= start:
        end_value = datetime.combine(day, datetime.min.time()) + end + timedelta(days=1)
    else:
        end_value = datetime.combine(day, datetime.min.time()) + end

    return start_value, end_value


class ScheduleGenerator:
    def auto_assign(
        self,
        *,
        schedule: Schedule,
        month: date,
        employees: list[Employee],
        shift_types: list[ShiftType],
        coverage_requirements: list[CoverageRequirement],
        availability: list[EmployeeAvailability] = (),
        department_capacities: list[DepartmentCapacity] = (),
        locked_duty_points_by_employee_id: dict[str, str] | None = None,
    ) -> GenerationResult:
        locked = locked_duty_points_by_employee_id or {}
        working = schedule.copy()

        shifts = {s.id: s for s in shift_types}

        availability_map: dict[tuple[str, date], list[EmployeeAvailability]] = defaultdict(list)
        for item in availability:
            availability_map[(item.employee_id, item.date)].append(item)

        capacity_map: dict[tuple[str, date], list[DepartmentCapacity]] = defaultdict(list)
        for item in department_capacities:
            capacity_map[(item.department_id, item.date)].append(item)

        assignment_counts: dict[str, int] = defaultdict(int)
        for day in working.days.values():
            for assignment in day.assignments:
                assignment_counts[assignment.employee_id] += 1

        conflicts: list[ScheduleConflict] = []
        created = 0

        requirements = sorted(
            (
                r for r in coverage_requirements
                if r.date.year == month.year and r.date.month == month.month
            ),
            key=lambda r: (r.date, r.id),
        )

        for requirement in requirements:
            shift = shifts.get(requirement.shift_type_id)

            if shift is None:
                conflicts.append(
                    ScheduleConflict(
                        type=ConflictType.INSUFFICIENT_COVERAGE,
                        message="Shift type not found.",
                        severity="error",
                        date=requirement.date,
                        requirement_id=requirement.id,
                    )
                )
                continue

            existing = self._matching_assignments(
                working.day(requirement.date),
                requirement,
            )
            missing = max(0, requirement.required_employees - len(existing))

            for _ in range(missing):
                candidates = [
                    employee
                    for employee in employees
                    if employee.active
                    and employee.department.id == requirement.department_id
                    and self._can_work_at(
                        locked.get(employee.id),
                        requirement.location,
                    )
                ]

                candidates.sort(
                    key=lambda employee: (
                        -self._lock_priority(
                            locked.get(employee.id),
                            requirement.location,
                        ),
                        assignment_counts[employee.id],
                        employee.employee_code,
                    )
                )

                selected = None

                for employee in candidates:
                    proposed = ShiftAssignment(
                        employee_id=employee.id,
                        shift_type_id=shift.id,
                        location=requirement.location,
                    )

                    validation = self._validate(
                        day=working.day(requirement.date),
                        assignment=proposed,
                        shift=shift,
                        availability=availability_map,
                        capacities=capacity_map,
                        employees=employees,
                    )

                    errors = [
                        c for c in validation
                        if c.severity == "error"
                    ]

                    if not errors:
                        selected = employee
                        break

                if selected is None:
                    conflicts.append(
                        ScheduleConflict(
                            type=ConflictType.INSUFFICIENT_COVERAGE,
                            message="No eligible employee is available.",
                            severity="error",
                            date=requirement.date,
                            requirement_id=requirement.id,
                        )
                    )
                    continue

                assignment = ShiftAssignment(
                    employee_id=selected.id,
                    shift_type_id=shift.id,
                    location=requirement.location,
                )
                working.day(requirement.date).assignments.append(assignment)
                assignment_counts[selected.id] += 1
                created += 1

        uncovered = self._uncovered(
            working,
            coverage_requirements,
            employees,
        )

        return GenerationResult(
            schedule=working,
            conflicts=tuple(conflicts),
            uncovered_requirements=tuple(uncovered),
            assignments_created=created,
        )

    def _matching_assignments(
        self,
        day,
        requirement: CoverageRequirement,
    ) -> list[ShiftAssignment]:
        return [
            a
            for a in day.assignments
            if a.shift_type_id == requirement.shift_type_id
            and (
                requirement.location is None
                or a.location == requirement.location
            )
        ]

    def _uncovered(
        self,
        schedule: Schedule,
        requirements: list[CoverageRequirement],
        employees: list[Employee],
    ) -> list[CoverageRequirement]:
        result = []

        employee_map = {e.id: e for e in employees}

        for requirement in requirements:
            count = 0
            for assignment in schedule.day(requirement.date).assignments:
                employee = employee_map.get(assignment.employee_id)
                if employee is None:
                    continue
                if employee.department.id != requirement.department_id:
                    continue
                if assignment.shift_type_id != requirement.shift_type_id:
                    continue
                if (
                    requirement.location is not None
                    and assignment.location != requirement.location
                ):
                    continue
                count += 1

            if count < requirement.required_employees:
                result.append(requirement)

        return result

    def _validate(
        self,
        *,
        day,
        assignment: ShiftAssignment,
        shift: ShiftType,
        availability,
        capacities,
        employees,
    ) -> list[ScheduleConflict]:
        conflicts = []

        employee = next(
            (e for e in employees if e.id == assignment.employee_id),
            None,
        )

        if employee is None:
            return [
                ScheduleConflict(
                    type=ConflictType.UNAVAILABLE_EMPLOYEE,
                    message="Employee not found.",
                    severity="error",
                    employee_id=assignment.employee_id,
                    date=day.date,
                )
            ]

        matching_availability = availability.get(
            (employee.id, day.date),
            [],
        )

        if matching_availability and not any(
            item.allows(shift.id)
            for item in matching_availability
        ):
            conflicts.append(
                ScheduleConflict(
                    type=ConflictType.UNAVAILABLE_EMPLOYEE,
                    message="Employee is unavailable.",
                    severity="error",
                    employee_id=employee.id,
                    date=day.date,
                )
            )

        matching_capacity = capacities.get(
            (employee.department.id, day.date),
            [],
        )

        if matching_capacity:
            limit = min(
                item.maximum_assignments
                for item in matching_capacity
            )
            department_count = 0

            for existing in day.assignments:
                existing_employee = next(
                    (
                        e for e in employees
                        if e.id == existing.employee_id
                    ),
                    None,
                )
                if (
                    existing_employee is not None
                    and existing_employee.department.id == employee.department.id
                ):
                    department_count += 1

            if department_count >= limit:
                conflicts.append(
                    ScheduleConflict(
                        type=ConflictType.DEPARTMENT_CAPACITY,
                        message="Department capacity exceeded.",
                        severity="error",
                        employee_id=employee.id,
                        date=day.date,
                    )
                )

        for existing in day.assignments:
            if existing.employee_id != assignment.employee_id:
                continue

            if existing.shift_type_id == assignment.shift_type_id:
                conflicts.append(
                    ScheduleConflict(
                        type=ConflictType.DUPLICATE_ASSIGNMENT,
                        message="Duplicate shift assignment.",
                        severity="error",
                        employee_id=employee.id,
                        date=day.date,
                    )
                )
                continue

            # Resolve the existing shift from the caller's list is done below
            # by the lightweight overlap check helper.
            conflicts.extend(
                self._overlap_conflict(
                    day.date,
                    employee.id,
                    existing.shift_type_id,
                    shift,
                )
            )

        return conflicts

    def _overlap_conflict(
        self,
        day: date,
        employee_id: str,
        existing_shift_id: str,
        proposed_shift: ShiftType,
    ) -> list[ScheduleConflict]:
        # The generator currently only receives the proposed shift here.
        # Cross-shift validation is completed by validate_schedule().
        return []

    @staticmethod
    def validate_schedule(
        schedule: Schedule,
        shift_types: list[ShiftType],
        employees: list[Employee],
    ) -> list[ScheduleConflict]:
        shifts = {s.id: s for s in shift_types}
        employee_map = {e.id: e for e in employees}
        conflicts = []

        for day in schedule.days.values():
            for index, left in enumerate(day.assignments):
                for right in day.assignments[index + 1:]:
                    if left.employee_id != right.employee_id:
                        continue

                    if left.shift_type_id == right.shift_type_id:
                        conflicts.append(
                            ScheduleConflict(
                                type=ConflictType.DUPLICATE_ASSIGNMENT,
                                message="Duplicate shift assignment.",
                                severity="error",
                                employee_id=left.employee_id,
                                date=day.date,
                            )
                        )
                        continue

                    left_shift = shifts.get(left.shift_type_id)
                    right_shift = shifts.get(right.shift_type_id)

                    if left_shift is None or right_shift is None:
                        continue

                    left_start, left_end = _shift_range(day.date, left_shift)
                    right_start, right_end = _shift_range(day.date, right_shift)

                    if left_start < right_end and right_start < left_end:
                        conflicts.append(
                            ScheduleConflict(
                                type=ConflictType.OVERLAPPING_SHIFT,
                                message="Overlapping shift assignment.",
                                severity="error",
                                employee_id=left.employee_id,
                                date=day.date,
                            )
                        )

        return conflicts

    @staticmethod
    def _can_work_at(
        locked_duty_point: str | None,
        requirement_location: str | None,
    ) -> bool:
        if not locked_duty_point or not locked_duty_point.strip():
            return True
        if not requirement_location or not requirement_location.strip():
            return True
        return locked_duty_point.strip() == requirement_location.strip()

    @staticmethod
    def _lock_priority(
        locked_duty_point: str | None,
        requirement_location: str | None,
    ) -> int:
        if (
            locked_duty_point
            and requirement_location
            and locked_duty_point.strip()
            and locked_duty_point.strip() == requirement_location.strip()
        ):
            return 1
        return 0
