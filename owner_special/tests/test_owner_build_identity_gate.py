from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "verify-owner-build-identity.ps1"


def test_build_identity_gate_exists():
    assert GATE.is_file()


def test_build_identity_gate_requires_owner_identity():
    text = GATE.read_text(encoding="utf-8")
    required = [
        "ExpectedFileName",
        "ExpectedProductName",
        "ExpectedInternalName",
        "ExpectedCompanyName",
        "OriginalFilename",
        "OWNER_MANIFEST.json",
        "owner-special",
        "owner_only",
        "Get-FileHash",
        "BUILD_IDENTITY_GATE=PASS",
    ]
    for token in required:
        assert token in text, f"missing identity-gate contract token: {token}"


def test_owner_identity_is_explicit_and_unique():
    text = GATE.read_text(encoding="utf-8")
    assert "research_os_owner_special.exe" in text
    assert "research_os_owner_special" in text
    assert "owner-special" in text
    assert "owner_only" in text
