#!/usr/bin/env python3
"""Cyber web security standard owner for Research OS.

This module owns web/API cybersecurity policy only. It is intentionally separate
from any file ownership, file ACL, document ownership, storage ownership, or
filesystem authorization subsystem. It never changes file owners or grants file
permissions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


CYBER_WEB_STANDARD_CONTRACT = "research-os-cyber-web-standard-v1"
CYBER_WEB_STANDARD_VERSION = "2026.08"


@dataclass(frozen=True)
class StandardReference:
    standard_id: str
    title: str
    version: str
    status: str
    role: str


@dataclass(frozen=True)
class SecurityControl:
    control_id: str
    category: str
    title: str
    required_public: bool = True
    required_local_loopback: bool = False
    evidence_key: str = ""


REFERENCES: tuple[StandardReference, ...] = (
    StandardReference(
        "OWASP-ASVS",
        "OWASP Application Security Verification Standard",
        "5.0.0",
        "baseline",
        "Application and API verification; target Level 2 with selected Level 3 controls for sensitive surfaces.",
    ),
    StandardReference(
        "OWASP-TOP10",
        "OWASP Top 10",
        "2025",
        "risk-catalog",
        "Risk awareness and regression coverage; not a substitute for ASVS verification.",
    ),
    StandardReference(
        "NIST-SP-800-218",
        "Secure Software Development Framework (SSDF)",
        "1.1",
        "final-baseline",
        "Secure development, supply-chain, build, release, and vulnerability-management practices.",
    ),
    StandardReference(
        "NIST-SP-800-52R2",
        "Guidelines for TLS Implementations",
        "Rev. 2",
        "transport-baseline",
        "TLS configuration, certificates, and secure transport requirements.",
    ),
)


CONTROLS: tuple[SecurityControl, ...] = (
    SecurityControl("WEB-HTTPS-001", "transport", "Public web surfaces use HTTPS", True, False, "https_enabled"),
    SecurityControl("WEB-TLS-002", "transport", "TLS 1.3 supported/preferred; TLS 1.2 only for required compatibility", True, False, "tls_policy_ok"),
    SecurityControl("WEB-CERT-003", "transport", "Trusted certificate and hostname validation", True, False, "certificate_trusted"),
    SecurityControl("WEB-CSP-010", "browser", "Content-Security-Policy is explicitly configured", True, False, "csp_configured"),
    SecurityControl("WEB-HSTS-011", "browser", "HSTS enabled on public HTTPS deployments", True, False, "hsts_configured"),
    SecurityControl("WEB-FRAME-012", "browser", "Clickjacking protection through CSP frame-ancestors or equivalent", True, False, "anti_clickjacking"),
    SecurityControl("WEB-NOSNIFF-013", "browser", "X-Content-Type-Options nosniff", True, False, "nosniff"),
    SecurityControl("WEB-REFERRER-014", "browser", "Referrer-Policy is explicitly configured", True, False, "referrer_policy"),
    SecurityControl("WEB-PERMISSIONS-015", "browser", "Permissions-Policy limits browser capabilities", True, False, "permissions_policy"),
    SecurityControl("WEB-CORS-020", "api", "CORS uses explicit allowlists instead of wildcard trust", True, True, "cors_allowlist"),
    SecurityControl("WEB-INPUT-021", "api", "Request input/schema validation is enforced", True, True, "input_validation"),
    SecurityControl("WEB-RATE-022", "api", "Rate/resource abuse controls are defined for exposed APIs", True, False, "rate_limiting"),
    SecurityControl("WEB-ERROR-023", "api", "Errors fail safely without leaking sensitive internals", True, True, "safe_errors"),
    SecurityControl("WEB-AUTHN-030", "identity", "Authentication is strong where identity is required", True, True, "authentication_ok"),
    SecurityControl("WEB-AUTHZ-031", "identity", "Authorization follows least privilege and server-side enforcement", True, True, "authorization_ok"),
    SecurityControl("WEB-SESSION-032", "identity", "Sessions/tokens are validated, scoped, expired, and protected", True, True, "session_security"),
    SecurityControl("WEB-COOKIE-033", "identity", "Sensitive cookies use Secure, HttpOnly, and appropriate SameSite", True, False, "secure_cookies"),
    SecurityControl("WEB-OAUTH-034", "identity", "OAuth/OIDC callbacks validate state and do not persist secret query values", True, True, "oauth_safe"),
    SecurityControl("WEB-SECRET-040", "data", "Secrets are never returned in UI/API status or persistent logs", True, True, "secret_redaction"),
    SecurityControl("WEB-DATA-041", "data", "Sensitive data exposure is minimized and bounded by explicit policy", True, True, "data_minimization"),
    SecurityControl("WEB-LOG-050", "monitoring", "Security-relevant activity is auditable with secret-safe logs", True, True, "security_logging"),
    SecurityControl("WEB-ALERT-051", "monitoring", "Production security events have alert/response ownership", True, False, "security_alerting"),
    SecurityControl("WEB-SUPPLY-060", "supply_chain", "Dependencies and external components are tracked and reviewed", True, True, "dependency_governance"),
    SecurityControl("WEB-PROV-061", "supply_chain", "Build/release provenance and exact revision evidence are retained", True, True, "build_provenance"),
    SecurityControl("WEB-SIGN-062", "supply_chain", "Public production artifacts use trusted signing where applicable", True, False, "trusted_signing"),
    SecurityControl("WEB-VULN-063", "supply_chain", "Vulnerability triage/remediation process is defined", True, True, "vulnerability_process"),
)


class CyberWebSecurityStandard:
    """Read-only policy/evidence evaluator for web and API cybersecurity."""

    def manifest(self) -> dict[str, Any]:
        return {
            "contract": CYBER_WEB_STANDARD_CONTRACT,
            "version": CYBER_WEB_STANDARD_VERSION,
            "owner": "CyberWebSecurityStandard",
            "scope": [
                "web_application_security",
                "api_security",
                "browser_security_headers",
                "authentication_and_session_security",
                "tls_and_certificates",
                "security_logging",
                "software_supply_chain",
            ],
            "references": [asdict(item) for item in REFERENCES],
            "target": {
                "owasp_asvs": "5.0.0 Level 2 baseline",
                "owasp_asvs_sensitive_controls": "selected Level 3",
                "owasp_top10": "2025 risk coverage",
                "nist_ssdf": "SP 800-218 v1.1 Final",
                "nist_tls": "SP 800-52 Rev.2",
            },
            "boundary": self.ownership_boundary(),
            "control_count": len(CONTROLS),
            "controls": [asdict(item) for item in CONTROLS],
            "automatic_remediation": False,
            "permission_grant_authority": False,
        }

    @staticmethod
    def ownership_boundary() -> dict[str, Any]:
        return {
            "separate_from_file_owner_system": True,
            "file_owner_read_authority": False,
            "file_owner_write_authority": False,
            "file_acl_grant_authority": False,
            "filesystem_authorization_source": False,
            "document_ownership_source": False,
            "cyber_policy_may_override_file_owner": False,
            "file_owner_system_may_override_cyber_policy": False,
            "integration_mode": "explicit_contract_only",
        }

    def assess(
        self,
        evidence: Mapping[str, Any],
        *,
        deployment_mode: str = "public",
    ) -> dict[str, Any]:
        mode = deployment_mode.strip().casefold()
        if mode not in {"public", "local_loopback"}:
            raise ValueError("deployment_mode must be public or local_loopback")

        results: list[dict[str, Any]] = []
        for control in CONTROLS:
            required = control.required_public if mode == "public" else control.required_local_loopback
            observed = evidence.get(control.evidence_key)
            passed = observed is True if required else observed is not False
            status = "pass" if passed else "fail"
            if not required and observed is None:
                status = "not_applicable"
                passed = True
            results.append(
                {
                    "control_id": control.control_id,
                    "category": control.category,
                    "title": control.title,
                    "required": required,
                    "evidence_key": control.evidence_key,
                    "observed": bool(observed) if observed is not None else None,
                    "status": status,
                }
            )

        required_results = [item for item in results if item["required"]]
        failures = [item for item in required_results if item["status"] == "fail"]
        return {
            "contract": CYBER_WEB_STANDARD_CONTRACT,
            "deployment_mode": mode,
            "ready": not failures,
            "required_controls": len(required_results),
            "passed_required_controls": len(required_results) - len(failures),
            "failed_required_controls": len(failures),
            "failed_control_ids": [item["control_id"] for item in failures],
            "results": results,
            "boundary": self.ownership_boundary(),
            "changes_file_ownership": False,
            "grants_permissions": False,
        }


CYBER_WEB_STANDARD = CyberWebSecurityStandard()


__all__ = [
    "CYBER_WEB_STANDARD",
    "CYBER_WEB_STANDARD_CONTRACT",
    "CYBER_WEB_STANDARD_VERSION",
    "CyberWebSecurityStandard",
]
