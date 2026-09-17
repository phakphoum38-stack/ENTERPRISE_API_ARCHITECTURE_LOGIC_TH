# P1-01 Execution Plane Integration

Status: experimental, branch-only.

This slice connects the P0 canonical identity and attempt contracts to the existing API Agent Plane and V3 Research Plane.

## Existing-plane rules
- API keeps its existing orchestration and AgentTaskQueue.
- V3 keeps its existing DurableTaskQueue and StatelessResearchRunner.
- No new scheduler, queue, worker, state machine, retry engine, or execution engine is introduced.
- Native task IDs remain authoritative inside each plane.
- Canonical attempt_id is the cross-plane retry identity.

## Retry semantics
### API Agent Plane
An API orchestration retry may create a new native RuntimeTask.task_id. The canonical task_id and run_id remain stable; canonical attempt_id must be unique and retry_of must reference the immediately previous attempt.

### V3 Research Plane
The native queue task ID remains stable while the queue retry counter changes. Each retry gets a new canonical attempt_id with the same mission/work/task/run lineage.

## Safety boundary
The adapter only creates immutable correlation records. It does not execute, schedule, lease, authorize, verify, repair, merge, or mutate Git state.
