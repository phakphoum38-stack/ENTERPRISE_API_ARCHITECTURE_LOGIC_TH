# Research OS local ephemeral GitHub Actions runner

This is an opt-in, one-job Windows runner for collecting reproducible validation evidence. It does not change the existing runner configuration or disable any repository gate.

## Prerequisites

- Windows x64.
- GitHub CLI (gh) installed and authenticated with gh auth login.
- Account permissions to manage repository Actions runners in phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH.
- Python available on PATH for the repository validators.
- Outbound HTTPS access to GitHub and GitHub Actions endpoints.

The runner executes repository code on your computer. Only dispatch it against branches and commits you trust. Do not use this runner for untrusted fork pull requests, and do not expose machine credentials or secrets to workflow code.

## Install and start

Open PowerShell in a trusted checkout of this repository and inspect tools/local-runner/Install-ResearchOSLocalRunner.ps1 first. Then run:

```powershell
gh auth status --hostname github.com
Set-ExecutionPolicy -Scope Process Bypass
.\tools\local-runner\Install-ResearchOSLocalRunner.ps1
```

The default installation directory is D:\ResearchOS-LocalRunner to avoid consuming space on a nearly-full C: drive. If that directory exists and is not empty, the script stops without overwriting or deleting its contents. Use -InstallRoot to choose another empty directory.

The script downloads the official latest Windows x64 runner release from actions/runner, records the downloaded archive's SHA-256, requests a short-lived registration token through gh, configures the runner as --ephemeral, and starts it in the foreground. The token is not written to a file or printed. Keep the PowerShell window open while the job runs.

## Evidence workflow

.github/workflows/local-runner-evidence.yml targets only the labels self-hosted, Windows, X64, and research-os-local. The first push on the setup branch should queue a job; once the local runner connects, it checks out that branch and uploads local-runner-evidence-<run-id>-<attempt> as a GitHub Actions artifact.

The workflow records:
- repository, event, ref, run ID, runner identity, and checked-out source SHA;
- exact expected-SHA comparison;
- Python and dependency-install output;
- each validator's output and exit code;
- a final summary when all validators pass.

The artifact is retained for 14 days. Failed validation remains failed; uploading evidence does not turn a failed job green.

After this setup PR is merged, use Actions → Local Runner Evidence → Run workflow and enter the exact target commit SHA. Select the branch containing that SHA. The workflow must report SHA_CHECK=PASS; do not treat an artifact alone as proof of correctness.

## Lifecycle and cleanup

The runner is ephemeral and is intended to accept one job. GitHub removes the runner registration after its job. The local runner files and logs are deliberately retained for inspection; the installer does not delete them automatically. After reviewing the evidence and confirming no process is using the directory, you may remove that specific runner directory yourself.

If a job is queued, confirm the runner is online in Settings → Actions → Runners, confirm the custom label is research-os-local, and check the local runner console logs. A queued job is not evidence of a successful run.
