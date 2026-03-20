#!/usr/bin/env python3
"""
Per-Task Sandbox Manager for Project Evolution-Reproduce.
Implements Conda-based isolation (Plan B from reproduce_readme.md §4.3.3).

Each reproduction task gets:
1. An independent Conda environment
2. An isolated working directory
3. Clean teardown after task completion
"""

import subprocess
import os
import shutil
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List


WORKSPACE_BASE = "/data/yjh/openhands_workspace"
ARCHIVE_BASE = "/data/yjh/openhands_archive"
CONDA_BASE = "/home/yjh/.conda/envs"


@dataclass
class SandboxConfig:
    """Configuration for an isolated task sandbox."""
    task_id: str
    conda_env: str
    workspace: str
    python_bin: str
    python_version: str
    created_at: str
    status: str  # "active" | "archived" | "destroyed"


def setup_task_sandbox(
    task_id: str,
    python_version: str = "3.10",
    extra_packages: Optional[List[str]] = None
) -> SandboxConfig:
    """
    Create an isolated Conda environment and workspace for a task.

    Args:
        task_id: Unique task identifier
        python_version: Python version for the Conda env
        extra_packages: Optional list of pip packages to pre-install

    Returns:
        SandboxConfig with environment details
    """
    env_name = f"task_{task_id}"
    workspace = os.path.join(WORKSPACE_BASE, f"task_{task_id}")
    python_bin = os.path.join(CONDA_BASE, env_name, "bin", "python")

    print(f"[Sandbox] Creating environment: {env_name}")

    # 1. Create independent Conda environment
    result = subprocess.run(
        ["conda", "create", "-n", env_name, f"python={python_version}", "-y", "--quiet"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to create Conda env: {result.stderr}")

    # 2. Create independent working directory
    os.makedirs(workspace, exist_ok=True)

    # 3. Pre-install common packages if specified
    if extra_packages:
        pip_bin = os.path.join(CONDA_BASE, env_name, "bin", "pip")
        for pkg in extra_packages:
            subprocess.run(
                [pip_bin, "install", pkg, "--quiet"],
                capture_output=True, text=True, timeout=120
            )

    config = SandboxConfig(
        task_id=task_id,
        conda_env=env_name,
        workspace=workspace,
        python_bin=python_bin,
        python_version=python_version,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
        status="active"
    )

    # Save sandbox config
    config_path = os.path.join(workspace, ".sandbox_config.json")
    with open(config_path, "w") as f:
        json.dump(asdict(config), f, indent=2)

    print(f"[Sandbox] Environment ready: {env_name}")
    print(f"[Sandbox] Workspace: {workspace}")
    print(f"[Sandbox] Python: {python_bin}")

    return config


def teardown_task_sandbox(task_id: str, archive: bool = True):
    """
    Clean up a task's isolated environment.

    Args:
        task_id: Unique task identifier
        archive: If True, move workspace to archive; if False, delete it
    """
    env_name = f"task_{task_id}"
    workspace = os.path.join(WORKSPACE_BASE, f"task_{task_id}")

    print(f"[Sandbox] Tearing down: {env_name}")

    # 1. Delete Conda environment
    try:
        subprocess.run(
            ["conda", "env", "remove", "-n", env_name, "-y"],
            capture_output=True, text=True, timeout=60
        )
        print(f"[Sandbox] Removed Conda env: {env_name}")
    except Exception as e:
        print(f"[Sandbox] Warning: Could not remove env {env_name}: {e}")

    # 2. Archive or delete workspace
    if os.path.exists(workspace):
        if archive:
            os.makedirs(ARCHIVE_BASE, exist_ok=True)
            archive_path = os.path.join(ARCHIVE_BASE, f"task_{task_id}")
            if os.path.exists(archive_path):
                # Add timestamp to avoid conflicts
                archive_path = f"{archive_path}_{int(time.time())}"
            shutil.move(workspace, archive_path)
            print(f"[Sandbox] Archived workspace to: {archive_path}")
        else:
            shutil.rmtree(workspace)
            print(f"[Sandbox] Deleted workspace: {workspace}")


def list_active_sandboxes() -> List[SandboxConfig]:
    """List all currently active task sandboxes."""
    active = []
    if not os.path.exists(WORKSPACE_BASE):
        return active

    for item in os.listdir(WORKSPACE_BASE):
        if item.startswith("task_"):
            config_path = os.path.join(WORKSPACE_BASE, item, ".sandbox_config.json")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    data = json.load(f)
                active.append(SandboxConfig(**data))

    return active


def run_in_sandbox(task_id: str, command: str, timeout: int = 600) -> dict:
    """
    Execute a command inside a task's sandbox environment.

    Args:
        task_id: Task identifier
        command: Shell command to execute
        timeout: Execution timeout in seconds

    Returns:
        dict with 'returncode', 'stdout', 'stderr'
    """
    env_name = f"task_{task_id}"
    workspace = os.path.join(WORKSPACE_BASE, f"task_{task_id}")

    # Activate the conda env and run the command
    full_command = f"conda run -n {env_name} --cwd {workspace} bash -c '{command}'"

    try:
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s"
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage per-task sandboxes")
    sub = parser.add_subparsers(dest="action")

    create_p = sub.add_parser("create", help="Create a new sandbox")
    create_p.add_argument("task_id", help="Unique task ID")
    create_p.add_argument("--python", default="3.10", help="Python version")

    destroy_p = sub.add_parser("destroy", help="Destroy a sandbox")
    destroy_p.add_argument("task_id", help="Task ID to destroy")
    destroy_p.add_argument("--no-archive", action="store_true")

    list_p = sub.add_parser("list", help="List active sandboxes")

    args = parser.parse_args()

    if args.action == "create":
        config = setup_task_sandbox(args.task_id, args.python)
        print(json.dumps(asdict(config), indent=2))
    elif args.action == "destroy":
        teardown_task_sandbox(args.task_id, archive=not args.no_archive)
    elif args.action == "list":
        sandboxes = list_active_sandboxes()
        if sandboxes:
            for sb in sandboxes:
                print(f"  {sb.task_id} | env={sb.conda_env} | status={sb.status} | created={sb.created_at}")
        else:
            print("No active sandboxes found.")
    else:
        parser.print_help()
