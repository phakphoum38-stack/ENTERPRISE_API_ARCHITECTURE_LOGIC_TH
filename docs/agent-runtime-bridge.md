# Friend Workspace Agent Mesh bridge

The Friend Workspace now exposes an explicit Agent Mesh runtime path alongside chat.

## Flow

1. Enter an objective.
2. Create a durable orchestration plan with `understand`, `plan`, and `verify` steps.
3. Keep the run in a planned state until the user chooses **Explicit Execute**.
4. Execute through the existing Research OS orchestration API with `confirmed: true`.

This preserves the permission boundary: planning is not execution, and external writes remain behind an explicit execution path.
