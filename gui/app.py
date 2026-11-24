#!/usr/bin/env python3
"""
Tool-X GUI backend.

Serves the web dashboard and exposes a small API that reads core/data.json
and core/cat.json (the same files the terminal version of Tool-X uses) and
installs tools with no root / sudo / password prompt required.

Every tool is cloned (or, for package-manager entries, checked) inside
./installed/ next to this file -- never in a system directory -- so the
whole thing works for a normal, non-root user out of the box.
"""

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request

GUI_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GUI_DIR.parent
CORE_DIR = PROJECT_DIR / "core"
INSTALL_DIR = GUI_DIR / "installed"
INSTALL_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

# in-memory job state: { tool_name: {"state": ..., "log": [...]} }
JOBS = {}
JOBS_LOCK = threading.Lock()


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_data():
    data = load_json(CORE_DIR / "data.json")
    categories = load_json(CORE_DIR / "cat.json")
    return data, categories


def which(binary):
    return shutil.which(binary) is not None


def tool_state(name, info):
    """Figure out the current on-disk state of a tool without running anything."""
    pm = info["package_manager"]
    package_name = info["package_name"]

    with JOBS_LOCK:
        job = JOBS.get(name)
    if job and job["state"] == "installing":
        return "installing"

    if pm == "package_manager":
        if which(package_name):
            return "installed"
        return "not_installed"

    # git / curl / wget style tools live under INSTALL_DIR/<package_name>
    target = INSTALL_DIR / package_name
    if target.exists() and any(target.iterdir()):
        return "installed"
    return "not_installed"


def append_log(name, line):
    with JOBS_LOCK:
        JOBS[name]["log"].append(line)


def run_install(name, info):
    pm = info["package_manager"]
    package_name = info["package_name"]
    url = info.get("url")

    with JOBS_LOCK:
        JOBS[name] = {"state": "installing", "log": []}

    append_log(name, f"Starting install of {name} ({pm})")

    try:
        if pm == "package_manager":
            # Needs the system package manager. We never call sudo (no
            # password prompts), so we only proceed if we are already
            # root, or the package manager allows unprivileged installs
            # (e.g. Termux's pkg).
            pac = detect_package_manager()
            if pac is None:
                append_log(
                    name,
                    "No supported package manager found (this entry needs apt/pkg/yum/"
                    "brew/apk, which Windows doesn't have). Try the git-based tools instead.",
                )
                finish(name, "failed")
                return
            is_termux = "com.termux" in str(Path.home())
            is_root = hasattr(os, "geteuid") and os.geteuid() == 0
            if not is_root and not is_termux:
                append_log(
                    name,
                    f"This package needs root. Run manually: sudo {pac} install {package_name} -y",
                )
                finish(name, "needs_root")
                return
            cmd = [pac, "install", package_name, "-y"]
            run_cmd(name, cmd)
            if which(package_name):
                finish(name, "installed")
            else:
                finish(name, "failed")

        elif pm == "git":
            target = INSTALL_DIR / package_name
            if target.exists():
                finish(name, "installed")
                return
            run_cmd(name, ["git", "clone", url, str(target)])
            finish(name, "installed" if target.exists() else "failed")

        elif pm in ("curl", "wget"):
            target = INSTALL_DIR / package_name
            target.parent.mkdir(parents=True, exist_ok=True)
            cmd = [pm, url, "-o", str(target)] if pm == "curl" else [pm, url, "-O", str(target)]
            run_cmd(name, cmd)
            finish(name, "installed" if target.exists() else "failed")

        else:
            append_log(name, f"Unknown package manager '{pm}', skipping.")
            finish(name, "failed")

    except Exception as exc:  # noqa: BLE001
        append_log(name, f"Error: {exc}")
        finish(name, "failed")


def detect_package_manager():
    for pac in ("apt-get", "apt", "pkg", "yum", "brew", "apk"):
        if which(pac):
            return pac
    return None


def run_cmd(name, cmd, timeout=300):
    append_log(name, "$ " + " ".join(cmd))

    env = os.environ.copy()
    # Never let git (or anything else) block waiting for a username/password
    # on a hidden prompt -- if credentials would be needed, fail fast instead.
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        stdin=subprocess.DEVNULL,
        env=env,
    )
    try:
        for line in iter_with_timeout(proc, timeout):
            append_log(name, line.rstrip())
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        append_log(
            name,
            f"Timed out after {timeout}s (often a proxy/network issue "
            "rather than this tool itself -- check 'git config --global "
            "--get http.proxy').",
        )


def iter_with_timeout(proc, timeout):
    """Yield lines from proc.stdout, but give up if the whole command
    takes longer than `timeout` seconds (protects against a hang)."""
    start = time.time()
    for line in proc.stdout:
        yield line
        if time.time() - start > timeout:
            raise subprocess.TimeoutExpired(proc.args, timeout)


def finish(name, state):
    with JOBS_LOCK:
        JOBS[name]["state"] = state


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def api_data():
    data, categories = get_data()
    tools = []
    for name, info in data.items():
        tools.append(
            {
                "name": name,
                "package_name": info["package_name"],
                "category": [c for c in info["category"] if c],
                "package_manager": info["package_manager"],
                "url": info.get("url"),
                "state": tool_state(name, info),
            }
        )
    tools.sort(key=lambda t: t["name"].lower())
    return jsonify({"tools": tools, "categories": categories})


@app.route("/api/install/<name>", methods=["POST"])
def api_install(name):
    data, _ = get_data()
    if name not in data:
        return jsonify({"error": "unknown tool"}), 404

    current = tool_state(name, data[name])
    if current == "installing":
        return jsonify({"state": "installing"})
    if current == "installed":
        return jsonify({"state": "installed"})

    thread = threading.Thread(target=run_install, args=(name, data[name]), daemon=True)
    thread.start()
    return jsonify({"state": "installing"})


@app.route("/api/status/<name>")
def api_status(name):
    with JOBS_LOCK:
        job = JOBS.get(name)
    if not job:
        data, _ = get_data()
        info = data.get(name)
        state = tool_state(name, info) if info else "unknown"
        return jsonify({"state": state, "log": []})
    return jsonify({"state": job["state"], "log": job["log"][-200:]})


if __name__ == "__main__":
    print("Tool-X GUI running -> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
