#!/usr/bin/env python3
"""Research OS Local Runner Manager.

Uses the installed GitHub CLI for authentication. No GitHub token is written to
this application's settings file. Account switching is temporary and restored
when repository discovery finishes or the runner process exits.
"""
from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

APP_NAME = "ResearchOS Local Runner Manager"
REPOSITORY_DEFAULT = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"
INSTALLER_RELATIVE = Path("tools") / "local-runner" / "Install-ResearchOSLocalRunner.ps1"
GITHUB_HOST = "github.com"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def settings_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    return base / "ResearchOS" / "LocalRunnerManager" / "settings.json"


def load_settings() -> dict[str, Any]:
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(data: dict[str, Any]) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def run_command(
    args: list[str], timeout: int = 30, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
        check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        env=env,
    )


def require_gh() -> None:
    result = run_command(["gh", "--version"])
    if result.returncode != 0:
        raise RuntimeError("GitHub CLI (gh) was not found. Install it and run gh auth login first.")


def github_accounts() -> list[dict[str, Any]]:
    result = run_command(["gh", "auth", "status", "--json", "hosts"])
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Could not read GitHub CLI account status. Run gh auth status in PowerShell "
            "and confirm a github.com account is logged in.\n\n" + result.stdout.strip()
        ) from exc
    hosts = payload.get("hosts", {})
    entries = hosts.get(GITHUB_HOST, []) if isinstance(hosts, dict) else []
    accounts = []
    for item in entries:
        login = item.get("login")
        if login and item.get("state", "success") == "success":
            accounts.append({"login": str(login), "active": bool(item.get("active", False))})
    if not accounts:
        raise RuntimeError("No authenticated github.com account found. Run gh auth login first.")
    return accounts


def active_login() -> str | None:
    accounts = github_accounts()
    active = [a["login"] for a in accounts if a["active"]]
    return active[0] if active else (accounts[0]["login"] if len(accounts) == 1 else None)


def account_token(login: str) -> str:
    """Read a selected account token into memory only; never log or persist it."""
    result = run_command([
        "gh", "auth", "token", "--hostname", GITHUB_HOST, "--user", login
    ])
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not obtain a credential for GitHub account {login}. "
            "Run gh auth status and re-authenticate that account if needed."
        )
    token = result.stdout.strip()
    if not token or "\\n" in token or "\\r" in token:
        raise RuntimeError(f"GitHub CLI returned an invalid credential for {login}.")
    return token


def repositories_for(login: str) -> list[str]:
    # GH_TOKEN scopes this child process to the chosen account without changing
    # the user's global active gh account (which could race other tools).
    token = account_token(login)
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    try:
        result = run_command(
            ["gh", "api", "user/repos", "--paginate", "--jq", ".[].full_name"],
            timeout=90, env=env,
        )
    finally:
        token = ""
        env.pop("GH_TOKEN", None)
    if result.returncode != 0:
        raise RuntimeError(
            f"Could not list repositories for {login}:\\n{result.stdout.strip()}"
        )
    return sorted(
        {line.strip() for line in result.stdout.splitlines()
         if REPO_PATTERN.fullmatch(line.strip())},
        key=str.casefold,
    )


class RunnerManager:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.settings = load_settings()
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.runner_process: subprocess.Popen[str] | None = None
        self.running = False
        self.accounts: list[str] = []
        self.repositories: list[str] = []

        root.title(APP_NAME)
        root.geometry("780x610")
        root.minsize(700, 540)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(7, weight=1)

        ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            frame,
            text="Choose a GitHub account and repository. Credentials stay in GitHub CLI.",
            wraplength=710,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(frame, text="GitHub account").grid(row=2, column=0, sticky="w", pady=5)
        self.account_var = tk.StringVar(value=self.settings.get("account", ""))
        self.account_combo = ttk.Combobox(frame, textvariable=self.account_var, state="readonly")
        self.account_combo.grid(row=2, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(frame, text="Refresh accounts", command=self.refresh_accounts).grid(
            row=2, column=2, sticky="ew", pady=5
        )

        ttk.Label(frame, text="Repository (owner/name)").grid(row=3, column=0, sticky="w", pady=5)
        self.repo_var = tk.StringVar(value=self.settings.get("repository", REPOSITORY_DEFAULT))
        self.repo_combo = ttk.Combobox(frame, textvariable=self.repo_var, state="normal")
        self.repo_combo.grid(row=3, column=1, sticky="ew", padx=8, pady=5)
        ttk.Button(frame, text="Refresh repositories", command=self.refresh_repositories).grid(
            row=3, column=2, sticky="ew", pady=5
        )

        ttk.Label(frame, text="Installer path").grid(row=4, column=0, sticky="w", pady=5)
        self.installer_var = tk.StringVar(value=self.settings.get("installer_path", ""))
        ttk.Entry(frame, textvariable=self.installer_var).grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=8, pady=5
        )
        ttk.Button(frame, text="Use installer in this checkout", command=self.locate_installer).grid(
            row=5, column=1, columnspan=2, sticky="e", padx=8, pady=5
        )

        self.trust_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, variable=self.trust_var,
            text="I trust this repository and the workflow code that may execute on this computer.",
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 8))

        self.output = tk.Text(frame, height=12, wrap="word", state="disabled")
        self.output.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(4, 8))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.output.yview)
        scrollbar.grid(row=7, column=3, sticky="ns", pady=(4, 8))
        self.output.configure(yscrollcommand=scrollbar.set)

        buttons = ttk.Frame(frame)
        buttons.grid(row=8, column=0, columnspan=3, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        self.save_button = ttk.Button(buttons, text="Save selection", command=self.save_selection)
        self.save_button.grid(row=0, column=0, sticky="w")
        self.run_button = ttk.Button(buttons, text="Start ephemeral runner", command=self.start_runner)
        self.run_button.grid(row=0, column=1, sticky="e", padx=(8, 0))

        self.log("No token is stored by this app. GitHub CLI handles authentication.")
        self.root.after(150, self.drain_output)
        self.root.after(250, self.refresh_accounts)

    def log(self, message: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", message.rstrip() + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def post_log(self, message: str) -> None:
        self.output_queue.put(message)

    def drain_output(self) -> None:
        while True:
            try:
                message = self.output_queue.get_nowait()
            except queue.Empty:
                break
            self.log(message)
        self.root.after(150, self.drain_output)

    def refresh_accounts(self) -> None:
        self.log("Reading authenticated GitHub CLI accounts…")

        def work() -> None:
            try:
                require_gh()
                accounts = github_accounts()
                active = active_login()
                self.root.after(0, lambda: self.accounts_loaded(accounts, active))
            except Exception as exc:
                message = str(exc)
                self.root.after(0, lambda: self.show_error(message))

        threading.Thread(target=work, daemon=True).start()

    def accounts_loaded(self, accounts: list[dict[str, Any]], active: str | None) -> None:
        self.accounts = [a["login"] for a in accounts]
        self.account_combo["values"] = self.accounts
        wanted = self.settings.get("account") or self.account_var.get() or active or ""
        self.account_var.set(wanted if wanted in self.accounts else (active or self.accounts[0]))
        self.log("Accounts: " + ", ".join(
            a["login"] + (" (active)" if a["active"] else "") for a in accounts
        ))

    def refresh_repositories(self) -> None:
        login = self.account_var.get().strip()
        if not login:
            self.show_error("Choose a GitHub account first.")
            return
        self.log(f"Listing repositories available to {login}…")

        def work() -> None:
            try:
                repos = repositories_for(login)
                self.root.after(0, lambda: self.repositories_loaded(repos))
            except Exception as exc:
                message = str(exc)
                self.root.after(0, lambda: self.show_error(message))

        threading.Thread(target=work, daemon=True).start()

    def repositories_loaded(self, repos: list[str]) -> None:
        current = self.repo_var.get().strip()
        if current and REPO_PATTERN.fullmatch(current) and current not in repos:
            repos = sorted(set(repos + [current]), key=str.casefold)
        self.repositories = repos
        self.repo_combo["values"] = repos
        self.log(f"Repository discovery complete: {len(repos)} accessible repositories.")
        if not repos:
            self.log("No repositories returned. You may enter owner/name manually if you have access.")

    def locate_installer(self) -> None:
        candidate = Path.cwd() / INSTALLER_RELATIVE
        if candidate.is_file():
            self.installer_var.set(str(candidate.resolve()))
            self.log(f"Installer selected: {candidate.resolve()}")
        else:
            messagebox.showwarning(
                APP_NAME,
                "Could not find tools/local-runner/Install-ResearchOSLocalRunner.ps1 "
                "under the current directory. Start the app from a trusted repository checkout.",
            )

    def selected_values(self) -> tuple[str, str, Path]:
        login = self.account_var.get().strip()
        repository = self.repo_var.get().strip()
        installer_text = self.installer_var.get().strip()
        if not login:
            raise ValueError("Select a GitHub account.")
        if not REPO_PATTERN.fullmatch(repository):
            raise ValueError("Repository must use owner/name format.")
        if not installer_text:
            raise ValueError("Select the existing PowerShell installer.")
        installer = Path(installer_text).expanduser().resolve()
        if not installer.is_file():
            raise ValueError(f"Installer does not exist: {installer}")
        raw = installer.read_bytes()
        if not raw or not any(raw):
            raise ValueError("Installer is empty or contains only zero bytes. Restore and verify it first.")
        if installer.name.casefold() != "install-researchoslocalrunner.ps1":
            raise ValueError("The selected file is not Install-ResearchOSLocalRunner.ps1.")
        return login, repository, installer

    def save_selection(self) -> None:
        try:
            login, repository, installer = self.selected_values()
            self.settings.update({
                "account": login, "repository": repository, "installer_path": str(installer),
                "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            save_settings(self.settings)
            self.log(f"Saved account={login}, repository={repository}.")
            self.log(f"Settings file: {settings_path()}")
        except Exception as exc:
            self.show_error(str(exc))

    def start_runner(self) -> None:
        if self.running:
            return
        try:
            login, repository, installer = self.selected_values()
        except Exception as exc:
            self.show_error(str(exc))
            return
        if not self.trust_var.get():
            self.show_error("Confirm that you trust the repository and workflow code before starting the runner.")
            return
        if not messagebox.askyesno(
            APP_NAME,
            f"Start the ephemeral runner for {repository} using GitHub account {login}?\n\n"
            "This computer will execute a queued workflow from that repository. "
            "Do not continue for untrusted branches or fork pull requests.",
            icon="warning",
        ):
            return

        self.settings.update({
            "account": login, "repository": repository, "installer_path": str(installer),
            "updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        save_settings(self.settings)
        self.running = True
        self.run_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.account_combo.configure(state="disabled")
        self.repo_combo.configure(state="disabled")
        self.log(f"Starting runner for {repository} with account {login}…")
        threading.Thread(target=self.runner_worker, args=(login, repository, installer), daemon=True).start()

    def runner_worker(self, login: str, repository: str, installer: Path) -> None:
        exit_code = 1
        token = ""
        env: dict[str, str] | None = None
        try:
            token = account_token(login)
            env = os.environ.copy()
            env["GH_TOKEN"] = token
            command = [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(installer), "-Repository", repository,
                "-GitHubAccount", login,
            ]
            self.post_log(
                f"Launching the existing installer for {repository} with an isolated "
                f"credential for {login}; the global gh account will not be switched."
            )
            self.runner_process = subprocess.Popen(
                command, cwd=str(installer.parent.parent.parent), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace", bufsize=1,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            assert self.runner_process.stdout is not None
            for line in self.runner_process.stdout:
                self.post_log(line.rstrip())
            exit_code = self.runner_process.wait()
            self.post_log(f"Runner installer/process exited with code {exit_code}.")
        except Exception as exc:
            self.post_log(f"ERROR: {exc}")
        finally:
            # Remove references as soon as the child exits. The credential is
            # never written to settings or emitted to the log.
            if env is not None:
                env.pop("GH_TOKEN", None)
            token = ""
            env = None
            self.root.after(0, self.runner_finished, exit_code)

    def runner_finished(self, exit_code: int) -> None:
        self.running = False
        self.run_button.configure(state="normal")
        self.save_button.configure(state="normal")
        self.account_combo.configure(state="readonly")
        self.repo_combo.configure(state="normal")
        self.log("Process exit code is not proof of workflow success; inspect Actions checks and the evidence artifact.")

    def show_error(self, message: str) -> None:
        self.log("ERROR: " + message)
        messagebox.showerror(APP_NAME, message)

    def on_close(self) -> None:
        if self.running:
            messagebox.showwarning(
                APP_NAME,
                "The runner is active. Keep this window open so the original GitHub account can be restored safely.",
            )
            return
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    try:
        RunnerManager(root)
    except Exception as exc:
        messagebox.showerror(APP_NAME, str(exc))
        return 1
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
