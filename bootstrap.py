#!/usr/bin/env python3

from pathlib import Path
from typing import Final
import sys
import subprocess
import os
import shutil

venv_path   : Final = Path(__file__).parent.absolute() / ".venv"
venv_python : Final = venv_path / "Scripts/python.exe" if sys.platform == "win32" else venv_path / "bin/python"

def running_in_native_venv() -> bool:
    current_venv = os.environ.get("VIRTUAL_ENV")
    if not current_venv:
        return False
    current_venv = Path(current_venv).absolute()
    current_python = Path(sys.executable).absolute()

    return current_venv.resolve() == venv_python.resolve() and current_python.resolve() == venv_python.resolve()

def prime_venv():

    # first of all, ensure python3 is available and bail otherwise
    try:
        subprocess.run(["python3", "--version"], check=True, capture_output=True)
    except Exception as some_fail:
        print(f"python3 was not available: {some_fail}")
        sys.exit(1)

    # now we need to set up an environment if we're not in one yet
    if venv_path.exists() and not venv_python.exists():
        print("Removing broken .venv without python executable")
        shutil.rmtree(venv_path)
    if not venv_path.exists():
        print("Creating a virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        # we can't restart ourselves in venv

    # now upgrade pip and install dependencies
    print("Upgrading pip and installing dependencies")
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    if not running_in_native_venv():
        print("You're not running this script in a native environment.\n"
              "Good news that such an environment was successfully prepared\n"
              f"To source it use your OS-specific python approach and source {venv_path}")
        sys.exit(1)


def main():
    print("Bootstrap script")
    prime_venv()


if __name__ == "__main__":
    main()
