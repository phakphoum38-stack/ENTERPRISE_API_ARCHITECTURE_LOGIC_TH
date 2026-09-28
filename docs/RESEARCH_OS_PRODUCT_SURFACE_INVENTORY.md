# Research OS Product Surface Inventory

This inventory is the first Product/UI completion slice after the platform-wide
cycle. It records what is already real in the canonical
apps/research_os_flutter product surface before any new UI is created.

## Verified existing surface

The canonical navigation registry contains exactly 18 destinations, indexed
0–17, and the app shell wires the corresponding existing feature pages.

The inventory does not create another navigation registry. The existing
researchNavigationItems registry remains authoritative for presentation
navigation metadata.

## Explicit boundaries

- apps/research_os_flutter remains the canonical cross-platform Research OS UI.
- phakphoum38-stack/flutter remains an External Tool.
- owner_special/flutter_app remains a separate Owner Special/Friend lineage.
- v3/flutter_app remains a V3 compatibility/release lineage.
- Capability metadata does not grant authorization.
- Final Gate remains the single release authority.
- No new runtime, queue, scheduler, evidence ledger, authorization engine, or navigation registry is introduced.

## Findings

The existing 18 product destinations are present and wired:

Home, AI Chat, Agent Center, Library, Knowledge Graph, GitHub,
Google Workspace, Local API & Service, System Monitor, Settings,
Developer Access, Brain Skills, Google Sign-In, Friend Connect, and
Control Center, Workflows, and Owner.

Control Center already contains the Main Final Audit surface.

Projects exposes the existing ProjectRegistry through the canonical API and a read-only product surface.

Workflows now exposes the existing orchestration lifecycle through a read-only product workspace using the canonical API client. Project association is never inferred when the orchestration API does not return it.

### Owner Experience

Owner Experience is now a canonical read-only surface over the existing authenticated Research OS session and shared platform APIs. Owner Special remains a separate runtime/UI boundary; the canonical surface observes that boundary without duplicating or replacing its runtime.

