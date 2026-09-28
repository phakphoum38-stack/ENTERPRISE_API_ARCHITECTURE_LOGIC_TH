# Research OS — iPhone over Tailscale

## Purpose

The Windows Research OS API remains bound to:

`http://127.0.0.1:8787`

The iPhone can reach it privately through Tailscale Serve without changing the API process to `0.0.0.0`.

Tailscale Serve terminates HTTPS and reverse-proxies requests from the tailnet to the local loopback service. This keeps the Research OS API itself on loopback while allowing the iPhone to use a stable HTTPS MagicDNS endpoint.

## Windows setup

Run an elevated PowerShell session on the Research OS Windows machine:

```powershell
& "C:\Program Files\Research OS\scripts\configure-research-os-tailscale.ps1"
```

The helper:

1. verifies `http://127.0.0.1:8787/health`;
2. reads the Windows device's Tailscale MagicDNS name;
3. configures `tailscale serve` for port 8787;
4. prints the private HTTPS API base URL;
5. prints the exact Google Identity and Google Workspace callback URLs.

To also place the HTTPS callback URLs into the Research OS Windows Service environment:

```powershell
& "C:\Program Files\Research OS\scripts\configure-research-os-tailscale.ps1" -ConfigureGoogleRedirects
```

The two callback URLs must also be registered in the Google OAuth client configuration before Google sign-in can complete through the Tailscale endpoint.

## iPhone connectivity

The iPhone must remain connected to the same Tailscale tailnet.

Verify the API from Safari using the HTTPS URL printed by the helper, followed by:

`/health`

Expected response is the normal Research OS health JSON.

## iOS IPA

The iOS workflow supports a manual API endpoint override.

In GitHub Actions, run **Research OS iOS IPA** with:

`api_base_url=https://<windows-device>.<tailnet>.ts.net`

The resulting IPA embeds that endpoint through:

`RESEARCH_OS_API_BASE_URL`

The default remains the public Render endpoint, so existing release behavior is unchanged when no input is supplied.

## Security model

Do **not** change the Windows Research OS API service to bind directly to `0.0.0.0` just to support the iPhone.

The intended private path is:

`iPhone → Tailscale HTTPS → Tailscale Serve → 127.0.0.1:8787 → Research OS API`

Tailscale documents Serve as a private tailnet service and specifically recommends keeping the backend on localhost when using Serve identity headers.

## Operational checks

On Windows:

```powershell
Get-NetTCPConnection -LocalPort 8787 -State Listen
tailscale serve status
```

The Research OS process should still show:

`127.0.0.1:8787`

On the iPhone, Tailscale must be connected before accessing the private HTTPS URL.

