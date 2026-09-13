# Phase 6G — Tool, MCP & Computer Use Action Routing

Prove that action-oriented UI cannot bypass the canonical Tool/MCP/Computer Use boundaries.

## Requirements
- all action requests enter FriendOrchestrator first;
- Tool selection remains read-only discovery until execution is authorized;
- MCP remains a connectivity boundary, never an authorization bypass;
- Computer Use remains planning/safety/approval bounded;
- OS input is unavailable directly to UI;
- no browser, shell, subprocess or network side effect from presentation code;
- preserve exact owner/session and approval context through downstream routing;
- reject arbitrary tool names, MCP endpoints, browser commands, OS actions and dynamic execution descriptors;
- evidence must come from canonical runtime traces.

## Tests
Tool/MCP/Computer Use valid routing, bypass attempts, owner mismatch, missing approval, malformed descriptors, executable injection, network-side-effect attempts and evidence integrity.

## Evidence
Create clean `current/AUTOBOT_MISSION_CONTROL_PHASE6G_TOOL_MCP_COMPUTER_USE_ACTION_ROUTING.diff` and machine-readable evidence.

No manual dispatch, merge, or gate weakening.
