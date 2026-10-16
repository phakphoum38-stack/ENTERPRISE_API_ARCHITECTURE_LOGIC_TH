# Research OS local ephemeral GitHub Actions runner

This is an opt-in, one-job Windows runner for collecting reproducible validation evidence. It does not change the existing runner configuration or disable any repository gate.

## Prerequisites

- Windows x64.
- GitHub CLI (gh) installed and authenticated with `gh auth login`.
- Account permissions to manage repository Actions runners in `phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH`.
- Python 3.10+ available on PATH; Tkinter is included with the standard Windows Python installer.
- Outbound HTTPS access to GitHub and GitHub Actions endpoints.

The runner executes repository code on your computer. Only dispatch it against branches and commits you trust. Do not use this runner for untrusted fork pull requests, and do not expose machine credentials or secrets to workflow code.

## Python account/repository manager (recommended)

From a trusted checkout of this repository, run:

```powershell
python .\tools\local-runner\ResearchOSLocalRunnerManager.py
```

The GUI provides:
- a GitHub account selector populated from authenticated GitHub CLI accounts;
- a repository selector populated from repositories visible to the selected account, with manual `owner/name` entry supported;
- a save-selection button and persistent settings under `%LOCALAPPDATA%\ResearchOS\LocalRunnerManager\settings.json`;
- a start button that calls the existing PowerShell installer with the selected repository;
- a trust confirmation before any runner starts.

The app does not store GitHub tokens. It reads the selected account's credential from GitHub CLI into memory and passes it as `GH_TOKEN` only to the repository-query or installer process. It does not change the globally active GitHub CLI account, avoiding races with other terminals and tools. The installer verifies the credential's account through the GitHub API before registering a runner. 

Settings store preferences only; they do not store access tokens, registration tokens, or repository secrets. The account/repository selectors are not proof of permissions; GitHub remains authoritative when the installer requests a short-lived runner registration token.

Run the standard-library regression tests from the repository root with:

```powershell
python -m unittest discover -s tools/local-runner -p 'test_local_runner_manager.py' -v
```

The dedicated workflow runs these tests on a GitHub-hosted Windows runner as well as checking the selected source SHA on the local runner.

## Manual install fallback

Open PowerShell in a trusted checkout and inspect `tools/local-runner/Install-ResearchOSLocalRunner.ps1` first:

```powershell
gh auth status --hostname github.com
Set-ExecutionPolicy -Scope Process Bypass
.\tools\local-runner\Install-ResearchOSLocalRunner.ps1 -Repository owner/name
```

The default installation directory is `D:\ResearchOS-LocalRunner` to avoid consuming space on a nearly-full C: drive. If that directory exists and is not empty, the script stops without overwriting or deleting its contents. Use `-InstallRoot` to choose another empty directory.

The script downloads the official latest Windows x64 runner release from `actions/runner`, compares the downloaded archive's SHA-256 against the digest published in GitHub release metadata, requests a short-lived registration token through `gh`, configures the runner as `--ephemeral`, and starts it in the foreground. The token is not written to a file or printed. Keep the PowerShell window open while the job runs.

## Evidence workflow

`.github/workflows/local-runner-evidence.yml` targets only the labels `self-hosted`, `Windows`, `X64`, and `research-os-local`. Once the local runner connects, it checks out the requested source and uploads `local-runner-evidence-<run-id>-<attempt>` as a GitHub Actions artifact.

For manual dispatch, set the requested commit SHA in the input; the workflow checks out that exact SHA rather than assuming the branch tip.

The workflow records:
- repository, event, ref, run ID, runner identity, and checked-out source SHA;
- exact expected-SHA comparison;
- Python and dependency-install output;
- each validator's output and exit code;
- a final summary when all validators pass.

The artifact is retained for 14 days. Failed validation remains failed; uploading evidence does not turn a failed job green.

After the setup PR is merged, use Actions → Local Runner Evidence → Run workflow and enter the exact target commit SHA. Select the branch containing that SHA. The workflow must report `SHA_CHECK=PASS`; do not treat an artifact alone as proof of correctness.

## Lifecycle and cleanup

The runner is ephemeral and is intended to accept one job. GitHub removes the runner registration after its job. The local runner files and logs are deliberately retained for inspection; the installer does not delete them automatically. After reviewing the evidence and confirming no process is using the directory, you may remove that specific runner directory yourself.

If a job is queued, confirm the runner is online in Settings → Actions → Runners, confirm the custom label is `research-os-local`, and check the local runner console logs. A queued job is not evidence of a successful run.
