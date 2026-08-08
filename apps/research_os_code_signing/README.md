# Research OS Code Signing Utility

Standalone Windows code-signing helper for Research OS.

This folder is intentionally separate from `apps/research_os_flutter` so test certificates, signing scripts, and CI preparation do not become part of the application runtime.

## What it does

- Creates a self-signed RSA 3072 / SHA-256 code-signing certificate for internal testing.
- Exports a password-protected `.pfx` locally.
- Signs a Windows `.exe` or installer with `signtool.exe`.
- Verifies Authenticode signatures.
- Converts a local `.pfx` to Base64 for storing in GitHub Actions Secrets.

## Security rules

- Never commit `.pfx`, `.p12`, `.cer` private-key exports, passwords, or Base64 certificate values.
- Self-signed certificates are for internal testing only. Other Windows machines will not trust the publisher until the certificate is explicitly trusted there.
- For public distribution, use a certificate issued by a trusted code-signing CA.

## Files

- `scripts/New-TestCodeSigningCertificate.ps1` — create/export a self-signed test certificate.
- `scripts/Sign-WindowsArtifact.ps1` — sign an EXE/MSI/installer.
- `scripts/Verify-WindowsSignature.ps1` — verify the resulting signature.
- `scripts/Convert-PfxToGitHubSecret.ps1` — convert `.pfx` bytes to Base64 without printing a password.
- `.gitignore` — prevents local certificate material from being committed.

## Create a self-signed certificate

```powershell
cd apps/research_os_code_signing
.\scripts\New-TestCodeSigningCertificate.ps1
```

The script securely prompts for the PFX password instead of hard-coding it.

## Sign an installer

```powershell
.\scripts\Sign-WindowsArtifact.ps1 `
  -PfxPath .\private\research-os-code-signing.pfx `
  -ArtifactPath ..\..\installer\output\Research-OS-Setup-0.6.0-x64.exe
```

## Verify

```powershell
.\scripts\Verify-WindowsSignature.ps1 `
  -ArtifactPath ..\..\installer\output\Research-OS-Setup-0.6.0-x64.exe
```

## GitHub Actions Secrets

Create the Base64 value locally:

```powershell
.\scripts\Convert-PfxToGitHubSecret.ps1 `
  -PfxPath .\private\research-os-code-signing.pfx
```

Store the returned value in GitHub Actions Secret:

- `WINDOWS_SIGNING_CERT_BASE64`
- `WINDOWS_SIGNING_CERT_PASSWORD`

Do not place either value in workflow YAML or repository files.
