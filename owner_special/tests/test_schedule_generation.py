from __future__ import annotations

import json
import unittest
from datetime import date, timedelta

from research_os_friend.schedule_generation import (
    CoverageRequirement,
    Department,
    DepartmentCapacity,
    Employee,
    EmployeeAvailability,
    Schedule,
    ShiftAssignment,
    ShiftType,
)
from research_os_friend.schedule_generation.adapter import ScheduleGenerateTool
from research_os_friend.schedule_generation.generator import ScheduleGenerator


class ScheduleGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.department = Department(
            id="er",
            code="ER",
            name="Emergency",
        )

        self.e1 = Employee(
            id="e1",
            employee_code="001",
            first_name="Anan",
            last_name="Sukjai",
            nickname="Nan",
            department=self.department,
            position="Nurse",
        )

        self.e2 = Employee(
            id="e2",
            employee_code="002",
            first_name="Mali",
            last_name="Dee",
            nickname="Mai",
            department=self.department,
            position="Nurse",
        )

        self.day_shift = ShiftType(
            id="day",
            code="D",
            name="Day",
            start_time=timedelta(hours=8),
            end_time=timedelta(hours=16),
            working_hours=8,
        )

        self.test_date = date(2026, 7, 6)

        self.schedule = Schedule.empty_month(
            2026,
            7,
            schedule_id="test",
            name="July",
        )

        self.generator = ScheduleGenerator()

    def _requirement(self, count: int = 1) -> CoverageRequirement:
        return CoverageRequirement(
            id="r1",
            date=self.test_date,
            department_id="er",
            shift_type_id="day",
            required_employees=count,
        )

    def test_auto_assigns_two_eligible_employees(self):
        result = self.generator.auto_assign(
            schedule=self.schedule,
            month=self.test_date,
            employees=[self.e1, self.e2],
            shift_types=[self.day_shift],
            coverage_requirements=[self._requirement(2)],
        )

        self.assertEqual(result.assignments_created, 2)
        self.assertTrue(result.completed)
        self.assertEqual(
            len(result.schedule.day(self.test_date).assignments),
            2,
        )

    def test_unavailable_employee_is_rejected(self):
        result = self.generator.auto_assign(
            schedule=self.schedule,
            month=self.test_date,
            employees=[self.e1],
            shift_types=[self.day_shift],
            coverage_requirements=[self._requirement()],
            availability=[
                EmployeeAvailability(
                    employee_id="e1",
                    date=self.test_date,
                    available=False,
                )
            ],
        )

        self.assertEqual(result.assignments_created, 0)
        self.assertEqual(len(result.uncovered_requirements), 1)

    def test_capacity_one_leaves_one_uncovered(self):
        result = self.generator.auto_assign(
            schedule=self.schedule,
            month=self.test_date,
            employees=[self.e1, self.e2],
            shift_types=[self.day_shift],
            coverage_requirements=[self._requirement(2)],
            department_capacities=[
                DepartmentCapacity(
                    department_id="er",
                    date=self.test_date,
                    maximum_assignments=1,
                )
            ],
        )

        self.assertEqual(result.assignments_created, 1)
        self.assertEqual(len(result.uncovered_requirements), 1)

    def test_duplicate_assignment_detected(self):
        self.schedule.day(self.test_date).assignments.extend(
            [
                ShiftAssignment(
                    employee_id="e1",
                    shift_type_id="day",
                ),
                ShiftAssignment(
                    employee_id="e1",
                    shift_type_id="day",
                ),
            ]
        )

        conflicts = ScheduleGenerator.validate_schedule(
            self.schedule,
            [self.day_shift],
            [self.e1],
        )

        self.assertTrue(
            any(
                conflict.type == "duplicateAssignment"
                for conflict in conflicts
            )
        )

    def test_coverage_checker_reports_unmet_requirement(self):
        result = self.generator.auto_assign(
            schedule=self.schedule,
            month=self.test_date,
            employees=[],
            shift_types=[self.day_shift],
            coverage_requirements=[self._requirement()],
        )

        self.assertEqual(
            len(result.uncovered_requirements),
            1,
        )

    def test_tool_accepts_explicit_json_command(self):
        payload = {
            "operation": "auto",
            "month": "2026-07",
            "schedule": {
                "id": "schedule",
                "name": "July 2026",
            },
            "employees": [
                {
                    "id": "e1",
                    "employee_code": "001",
                    "first_name": "Anan",
                    "last_name": "Sukjai",
                    "nickname": "Nan",
                    "position": "Nurse",
                    "department": {
                        "id": "er",
                        "code": "ER",
                        "name": "Emergency",
                    },
                }
            ],
            "shift_types": [
                {
                    "id": "day",
                    "code": "D",
                    "name": "Day",
                    "start_time": "08:00",
                    "end_time": "16:00",
                    "working_hours": 8,
                }
            ],
            "coverage_requirements": [
                {
                    "id": "r1",
                    "date": "2026-07-06",
                    "department_id": "er",
                    "shift_type_id": "day",
                    "required_employees": 1,
                }
            ],
        }

        output = json.loads(
            ScheduleGenerateTool()(
                json.dumps(payload, ensure_ascii=False)
            )
        )

        self.assertTrue(output["completed"])
        self.assertEqual(output["assignments_created"], 1)


if __name__ == "__main__":
    unittest.main()
