# Research OS — Virtual Figma Delta Plan

Remote target already identified:

- Figma file key: `8QkAcmOAPrXyS64HCOWIQq`
- Page node: `5:2`
- Existing page name: `Research OS — Self Designed v3.6`

## Existing remote frames observed

- `00 — Design System & Principles`
- `01 — Command Center`
- `02 — Friend Workspace`
- `03 — Agent Mesh`
- `04 — Skills & Tool Bus`
- `05 — Memory & Evidence`
- `06 — AI Design Studio`

## Existing design tokens observed

- Canvas `#090E1A`
- Sidebar `#0D1424`
- Surface `#11192B`
- Surface 2 `#172238`
- Primary `#5B7CFF`
- Success `#3DDC97`
- Warning `#F7C65C`
- Danger `#FF6B7A`
- AI Accent `#C17CFF`
- Research `#45D4E8`

## Virtual-first rule

Use Research OS Virtual Figma flow before any remote write:

1. `figma.virtual.templates`
2. `figma.virtual.compose`
3. GUI audit
4. freeze delta
5. `figma.virtual.batch`
6. remote Figma write batch when permitted
7. at most one verification read

Remote Figma should not be used as the iteration scratchpad.

## New GUI delta

### Global shell

- Preserve current dark Research OS visual language and tokens.
- Replace/extend the information architecture with MAIN / WORKSPACE / SYSTEM groups.
- Add official Research OS app mark consistently to launcher and shell.
- Keep the sidebar collapsible.
- Add top live-status strip sourced from runtime state, not hard-coded values.

### Chat AI

The main center workspace is Chat.

Primary empty-state greeting:

`สวัสดีเริ่มทำอะไรดี`

Planned layout:

- left: conversation list / search / new chat
- center: messages + empty state + composer
- right: live context / system / agents / memory panel
- bottom: tool-discovery execution workflow only when backed by real execution state

### Navigation target

MAIN:
- Home
- Chat AI
- Agents
- Memory
- Skills
- Tools
- Factory
- Providers

WORKSPACE:
- Files
- Repositories
- GitHub
- Drive

SYSTEM:
- Runtime
- Installer
- Backup
- Restore
- Shell

## Do not duplicate working modules

The visual delta must wrap/reuse the current Flutter feature modules first. New screens are required only for capabilities not currently surfaced as a dedicated destination.

## Status semantics

- Green = runtime evidence says usable/ready.
- Amber = attention/auth/degraded state.
- Red = blocked/error.
- Unknown = explicitly shown as unknown; never converted to green by UI defaults.

## Remote sync gate

Do not claim the remote Figma file is updated until a write succeeds. Current connected Figma seat reports View access, so remote mutation must remain gated by actual permission evidence.
