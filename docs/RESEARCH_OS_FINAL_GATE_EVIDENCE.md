# Research OS Final Gate Evidence

## Purpose

Bind one workflow lifecycle to one immutable canonical identity before Final Gate evaluation.

The evidence identity is:

`workflow_id -> run_id -> execution_id -> delivery_ids -> resource_versions -> terminal_status -> canonical_sha256`

## Contract

- Canonical SHA uses deterministic JSON serialization.
- Workflow, run, and execution identity must match the expected Final Gate target.
- Delivery IDs and resource versions remain explicit lineage inputs.
- Identity mismatch fails closed.
- The governed runtime exposes the evidence builder without introducing another queue, event bus, or evidence store.

## Deferred failures

Known Flutter failures in `apps/research_os_flutter/test/developer_access_page_test.dart` and `apps/research_os_flutter/test/flutter_code_tool_page_test.dart` remain deferred by project decision and are not modified by this integration.
