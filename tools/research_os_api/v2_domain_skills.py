#!/usr/bin/env python3
"""Versioned domain skill packs for Research OS AI Brain.

A skill is an operational contract: capabilities, prerequisite skills, tool
requirements, permissions and evidence. Packs intentionally do not contain
provider/model names and do not grant execution permission. Missing adapters
remain missing; registering a skill never makes a tool executable.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from v2_skill_registry import SkillDefinition, SkillRegistry


DOMAIN_SKILLS_CONTRACT = "brain-domain-skills-phase-10"


def _skill(
    skill_id: str,
    name: str,
    description: str,
    capabilities: tuple[str, ...],
    *,
    required_skills: tuple[str, ...] = (),
    required_tools: tuple[str, ...] = (),
    required_tool_capabilities: tuple[str, ...] = (),
    permissions: tuple[str, ...] = (),
    required_evidence: tuple[str, ...] = (),
) -> SkillDefinition:
    return SkillDefinition(
        skill_id,
        "1.0.0",
        name,
        description,
        capabilities,
        required_skills=required_skills,
        required_tools=required_tools,
        required_tool_capabilities=required_tool_capabilities,
        permissions=permissions,
        required_evidence=required_evidence,
    )


SOFTWARE_DEVELOPMENT_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "software.repo-cartography", "Repository Cartography",
        "Map repository structure and locate canonical modules before proposing changes.",
        ("code", "architecture", "repository_map"),
        required_tool_capabilities=("repository_map",), permissions=("workspace.read",),
        required_evidence=("entries",),
    ),
    _skill(
        "software.code-search", "Semantic Source Discovery",
        "Locate source symbols, entry points, feature ownership and cross-file references.",
        ("code", "debug", "code_search"),
        required_tool_capabilities=("code_search",), permissions=("workspace.read",),
        required_evidence=("matches",),
    ),
    _skill(
        "software.architecture-inspection", "Architecture Inspection",
        "Inspect repository layout and build contracts before architecture decisions.",
        ("architecture", "code"), required_skills=("software.repo-cartography",),
        required_tool_capabilities=("architecture_discovery",), permissions=("workspace.read",),
        required_evidence=("entries",),
    ),
    _skill(
        "software.build-inspection", "Build Contract Inspection",
        "Discover manifests, CI workflows, installer definitions and test surfaces without executing them.",
        ("build", "test", "ci"), required_tool_capabilities=("build_inspection",),
        permissions=("workspace.read",), required_evidence=("summary",),
    ),
    _skill(
        "software.debug-diagnosis", "Debug Diagnosis",
        "Trace a failure from evidence to likely root cause before any code mutation.",
        ("debug", "code"), required_skills=("software.code-search", "software.build-inspection"),
        permissions=("workspace.read",), required_evidence=("root_cause", "evidence"),
    ),
    _skill(
        "software.change-preview", "Code Change Preview",
        "Prepare a bounded source change and review its exact diff before approval.",
        ("code", "workspace_file_edit"), required_tool_capabilities=("workspace_diff_preview",),
        permissions=("workspace.read", "workspace.write"),
        required_evidence=("approval_fingerprint", "diff"),
    ),
    _skill(
        "software.controlled-test", "Controlled Test Execution",
        "Execute only a host-defined test profile through the governed command boundary.",
        ("test", "test_execution"), required_tool_capabilities=("test_execution",),
        permissions=("workspace.execute",), required_evidence=("executed", "output"),
    ),
    _skill(
        "software.controlled-build", "Controlled Build Execution",
        "Execute only a host-defined build profile through the governed command boundary.",
        ("build", "build_execution"), required_tool_capabilities=("build_execution",),
        permissions=("workspace.execute",), required_evidence=("executed", "output"),
    ),
    _skill(
        "software.regression-verification", "Regression Verification",
        "Require test/build evidence and unresolved-gap reporting before declaring a change complete.",
        ("verification", "test", "build"),
        required_skills=("brain.evidence-verification",),
        required_evidence=("checks", "evidence"),
    ),
)


GITHUB_CI_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "github.repository-status", "GitHub Repository Status",
        "Read repository, commit, pull-request and workflow status from one bounded repository.",
        ("github", "repository", "workflow"),
        required_tool_capabilities=("github_repository_read",), permissions=("github.read",),
        required_evidence=("repository",),
    ),
    _skill(
        "github.ci-diagnosis", "GitHub CI Diagnosis",
        "Correlate exact revision, workflow status and source/build evidence before a CI fix.",
        ("github", "workflow", "ci", "debug"),
        required_skills=("github.repository-status", "software.debug-diagnosis"),
        permissions=("github.read", "workspace.read"), required_evidence=("evidence", "root_cause"),
    ),
    _skill(
        "github.branch-file-change", "GitHub Branch File Change",
        "Preview and approval-gate one file create/update on a non-protected branch.",
        ("github", "github_write", "code"),
        required_tool_capabilities=("github_branch_file_write",), permissions=("github.write",),
        required_evidence=("approval_fingerprint",),
    ),
    _skill(
        "github.pr-evidence-comment", "Pull Request Evidence Comment",
        "Approval-gate a concise evidence comment without changing PR merge/state.",
        ("github", "pull_request"), required_tool_capabilities=("github_pull_request_comment",),
        permissions=("github.write",), required_evidence=("approval_fingerprint",),
    ),
    _skill(
        "github.exact-sha-verification", "Exact SHA Verification",
        "Verify that tests, builds and artifacts belong to the intended exact commit revision.",
        ("github", "workflow", "verification"), required_skills=("github.repository-status",),
        permissions=("github.read",), required_evidence=("commit_sha", "workflow_evidence"),
    ),
)


RESEARCH_KNOWLEDGE_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "research.evidence-gathering", "Evidence Gathering",
        "Collect task-relevant evidence while preserving source/provenance and unknowns.",
        ("research", "knowledge_create"), permissions=("knowledge.read", "memory.read"),
        required_evidence=("evidence",),
    ),
    _skill(
        "research.source-comparison", "Source Comparison",
        "Compare independent evidence, disagreements and freshness without flattening conflicts.",
        ("research", "synthesize"), required_skills=("research.evidence-gathering",),
        permissions=("knowledge.read",), required_evidence=("sources", "conflicts"),
    ),
    _skill(
        "research.synthesis", "Grounded Synthesis",
        "Produce a concise synthesis tied to evidence, gaps and confidence rather than unsupported certainty.",
        ("research", "summarize", "synthesize"),
        required_skills=("research.source-comparison", "brain.evidence-verification"),
        permissions=("knowledge.read", "memory.read"), required_evidence=("evidence",),
    ),
    _skill(
        "knowledge.unknown-tracking", "Known Unknown Tracking",
        "Preserve unresolved questions and evidence gaps so later tasks fetch rather than guess.",
        ("research", "memory_search", "verification"), permissions=("memory.read",),
        required_evidence=("unknowns",),
    ),
)


DOCUMENT_DATA_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "document.structure-reading", "Document Structure Reading",
        "Identify headings, tables, pages and semantic sections before extraction.",
        ("document_read", "pdf", "word", "markdown"), permissions=("documents.read",),
        required_evidence=("structure",),
    ),
    _skill(
        "document.table-extraction", "Table Extraction",
        "Extract bounded table structure with row/column provenance instead of flattening it to prose.",
        ("document_read", "excel", "table"), permissions=("documents.read",),
        required_evidence=("table", "provenance"),
    ),
    _skill(
        "data.schema-inference", "Data Schema Inference",
        "Infer typed columns, identifiers, missing values and constraints while marking uncertainty.",
        ("excel", "sheets", "data", "schema"), required_skills=("document.table-extraction",),
        permissions=("documents.read",), required_evidence=("schema",),
    ),
    _skill(
        "data.conflict-detection", "Data Conflict Detection",
        "Detect duplicated, contradictory or temporally incompatible records without overwriting source truth.",
        ("data", "conflict", "excel", "sheets"), required_skills=("data.schema-inference",),
        permissions=("documents.read",), required_evidence=("conflicts",),
    ),
)


GOOGLE_WORKSPACE_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "google.workspace-reading", "Google Workspace Reading",
        "Coordinate read-only Drive, Docs, Sheets, Calendar, Gmail and Contacts context through authorized adapters.",
        ("drive", "docs", "sheets", "calendar", "gmail", "contacts"),
        permissions=("google.read",), required_evidence=("source",),
    ),
    _skill(
        "google.workspace-change-plan", "Google Workspace Change Plan",
        "Prepare a change proposal with target, ownership, side effects and approval requirement before any write.",
        ("drive", "docs", "sheets", "calendar"), required_skills=("google.workspace-reading",),
        permissions=("google.write.with_confirmation",), required_evidence=("change_plan",),
    ),
)


SHIFT_SCHEDULING_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "shift.roster-reading", "Roster Reading",
        "Normalize shift assignments, locations, dates and personnel while preserving source rows/cells.",
        ("shift", "roster", "schedule"), required_skills=("document.table-extraction",),
        permissions=("documents.read",), required_evidence=("assignments", "provenance"),
    ),
    _skill(
        "shift.conflict-analysis", "Shift Conflict Analysis",
        "Detect overlapping duty, leave, absence and staffing conflicts from normalized assignments.",
        ("shift", "conflict", "leave", "absence"), required_skills=("shift.roster-reading",),
        permissions=("documents.read",), required_evidence=("conflicts",),
    ),
    _skill(
        "shift.replacement-planning", "Shift Replacement Planning",
        "Propose candidate replacement/coverage changes with constraints and explanation; no calendar write by itself.",
        ("shift", "replacement", "schedule"), required_skills=("shift.conflict-analysis",),
        permissions=("documents.read",), required_evidence=("candidates", "constraints"),
    ),
    _skill(
        "shift.calendar-change-plan", "Shift Calendar Change Plan",
        "Convert a verified roster change into an approval-required calendar update proposal.",
        ("shift", "calendar", "calendar_sync"), required_skills=("shift.replacement-planning",),
        permissions=("calendar.write.with_confirmation",), required_evidence=("change_plan",),
    ),
)


RELIABILITY_SECURITY_SKILLS: tuple[SkillDefinition, ...] = (
    _skill(
        "reliability.incident-diagnosis", "Incident Diagnosis",
        "Classify symptoms, affected components, evidence, blast radius and recovery options before intervention.",
        ("debug", "reliability", "incident"), required_skills=("brain.risk-assessment",),
        required_evidence=("symptoms", "evidence", "blast_radius"),
    ),
    _skill(
        "reliability.recovery-plan", "Recovery Plan",
        "Produce bounded retry/resume/rollback steps with checkpoints and stop conditions.",
        ("reliability", "recovery", "rollback"), required_skills=("reliability.incident-diagnosis",),
        required_evidence=("recovery_plan", "stop_conditions"),
    ),
    _skill(
        "security.permission-review", "Permission Review",
        "Check requested capabilities against least-privilege permission and approval boundaries.",
        ("security", "permission", "verification"), required_skills=("brain.risk-assessment",),
        required_evidence=("permissions", "risk"),
    ),
    _skill(
        "security.secret-boundary-review", "Secret Boundary Review",
        "Verify that credentials remain brokered/ephemeral and do not enter durable task, log or evidence state.",
        ("security", "secret", "verification"), required_evidence=("checks", "evidence"),
    ),
)


DOMAIN_SKILLS: tuple[SkillDefinition, ...] = (
    SOFTWARE_DEVELOPMENT_SKILLS
    + GITHUB_CI_SKILLS
    + RESEARCH_KNOWLEDGE_SKILLS
    + DOCUMENT_DATA_SKILLS
    + GOOGLE_WORKSPACE_SKILLS
    + SHIFT_SCHEDULING_SKILLS
    + RELIABILITY_SECURITY_SKILLS
)

PACKS: dict[str, tuple[SkillDefinition, ...]] = {
    "software_development": SOFTWARE_DEVELOPMENT_SKILLS,
    "github_ci": GITHUB_CI_SKILLS,
    "research_knowledge": RESEARCH_KNOWLEDGE_SKILLS,
    "documents_data": DOCUMENT_DATA_SKILLS,
    "google_workspace": GOOGLE_WORKSPACE_SKILLS,
    "shift_scheduling": SHIFT_SCHEDULING_SKILLS,
    "reliability_security": RELIABILITY_SECURITY_SKILLS,
}


def install_domain_skill_packs(
    registry: SkillRegistry,
    *,
    packs: Iterable[str] | None = None,
) -> dict[str, Any]:
    requested = tuple(packs) if packs is not None else tuple(PACKS)
    unknown = [name for name in requested if name not in PACKS]
    if unknown:
        raise ValueError(f"unknown domain skill pack: {unknown[0]}")

    installed: list[str] = []
    for pack_name in requested:
        for definition in PACKS[pack_name]:
            try:
                existing = registry.get(definition.skill_id)
            except ValueError:
                registry.register(definition)
                installed.append(definition.skill_id)
            else:
                if asdict(existing) != asdict(definition):
                    raise ValueError(f"domain skill definition collision: {definition.skill_id}")

    return {
        "contract": DOMAIN_SKILLS_CONTRACT,
        "packs": list(requested),
        "installed_skill_ids": installed,
        "installed_count": len(installed),
        "total_domain_skills": sum(len(PACKS[name]) for name in requested),
        "permission_grants": False,
        "tool_adapters_created": False,
        "provider_specific": False,
    }


def catalog() -> dict[str, Any]:
    return {
        "contract": DOMAIN_SKILLS_CONTRACT,
        "pack_count": len(PACKS),
        "skill_count": len(DOMAIN_SKILLS),
        "packs": {
            name: [definition.skill_id for definition in definitions]
            for name, definitions in PACKS.items()
        },
        "invariants": {
            "skill_registration_grants_permissions": False,
            "skill_registration_creates_tools": False,
            "missing_adapter_fails_closed": True,
            "provider_neutral": True,
        },
    }
