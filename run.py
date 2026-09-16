"""One-command launcher for the ICC Tournaments Analytics project.

Run from the project root:
    python run.py

Starts the FastAPI backend and Vite frontend. The ONLY URL printed to the
terminal is the website URL, so Ctrl+Click opens the dashboard directly.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = ROOT / ".venv"
LOGS = ROOT / "logs"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd, cwd=None):
    print("$", " ".join(map(str, cmd)))
    return subprocess.run(cmd, cwd=cwd, check=True)


def ensure_python_deps():
    py = venv_python()
    if not py.exists():
        print("Creating Python virtual environment...")
        run([sys.executable, "-m", "venv", str(VENV)], cwd=ROOT)

    marker = VENV / ".icc_requirements_installed"
    if not marker.exists():
        print("Installing backend dependencies...")
        run(
            [str(py), "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt")],
            cwd=ROOT,
        )
        marker.touch()
    return py


def ensure_node_deps():
    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("Node.js/npm is required. Install Node.js and run this file again.")
    if not (FRONTEND / "node_modules").exists():
        print("Installing frontend dependencies...")
        run([npm, "install"], cwd=FRONTEND)
    return npm


def wait_for_port(host: str, port: int, timeout: int = 30) -> bool:
    """Wait until a TCP port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def main():
    py = ensure_python_deps()
    npm = ensure_node_deps()
    LOGS.mkdir(exist_ok=True)

    backend_log = open(LOGS / "backend.log", "a", encoding="utf-8")
    frontend_log = open(LOGS / "frontend.log", "a", encoding="utf-8")

    backend = subprocess.Popen(
        [
            str(py), "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", "8000",
        ],
        cwd=BACKEND,
        stdout=backend_log,
        stderr=subprocess.STDOUT,
    )

    frontend = subprocess.Popen(
        [
            npm, "run", "dev", "--",
            "--host", "127.0.0.1", "--port", "5173",
        ],
        cwd=FRONTEND,
        stdout=frontend_log,
        stderr=subprocess.STDOUT,
    )

    website_url = "http://localhost:5173"

    try:
        # Wait until both services are ready before showing the URL.
        if not wait_for_port("127.0.0.1", 8000):
            raise SystemExit("Backend did not start. Check logs/backend.log")
        if not wait_for_port("127.0.0.1", 5173):
            raise SystemExit("Website did not start. Check logs/frontend.log")

        # Keep this as the first/only URL in the launcher output.
        print("\n" + "=" * 60)
        print("  ICC TOURNAMENTS ANALYTICS IS READY")
        print("=" * 60)
        print(f"\n  WEBSITE: {website_url}\n")
        print("  Ctrl + Click the WEBSITE URL above to open the dashboard.")
        print("  Keep this window open while using the website.")
        print("\n" + "=" * 60 + "\n")

        while True:
            if backend.poll() is not None:
                raise SystemExit("Backend stopped. Check logs/backend.log")
            if frontend.poll() is not None:
                raise SystemExit("Frontend stopped. Check logs/frontend.log")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping ICC Tournaments Analytics...")
    finally:
        for proc in (frontend, backend):
            if proc.poll() is None:
                proc.terminate()
        for proc in (frontend, backend):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        backend_log.close()
        frontend_log.close()


if __name__ == "__main__":
    main()
