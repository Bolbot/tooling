#!/usr/bin/env python3

from pathlib import Path
from typing import Final
import sys
import subprocess
import urllib.request
import os

RED   : Final = "\033[31m"
GREEN : Final = "\033[32m"
RESET : Final = "\033[0m"

tooling_path: Final = Path(__file__).parent.absolute() / ".tools"
venv_path   : Final = Path(__file__).parent.absolute() / ".venv"
venv_python : Final = venv_path / "Scripts/python.exe" if sys.platform == "win32" else venv_path / "bin/python"

def running_in_native_venv() -> bool:
    if sys.prefix == sys.base_prefix:
        print(f"Not running in virtual environment")
        return False
    if Path(sys.executable).absolute() != venv_python.absolute():
        return False
    return True

def prime_uv():
    uv_path = tooling_path / "uv" / ("uv.exe" if sys.platform == "win32" else "uv")

    if not uv_path.exists():
        print("Obtaining local copy of uv...")
        tooling_path.mkdir(exist_ok=True)

        platform = sys.platform

        try:
            archive_name = {
                "win32" : "uv-x86_64-pc-windows-msvc.zip",
                "darwin": "uv-aarch64-apple-darwin.tar.gz",
                "linux" : "uv-x86_64-unknown-linux-gnu.tar.gz"
            }[platform]
        except KeyError:
            print("Unexpected platform. We support Windows (x64), MacOS (arm), and Linux (x64)")
            sys.exit(1)
        uv_url = "https://github.com/astral-sh/uv/releases/download/0.9.18/" + archive_name

        temp_archive = tooling_path / archive_name
        #subprocess.run(["curl", "-L", uv_url, "-o", str(temp_archive)], check=True)
        urllib.request.urlretrieve(uv_url, str(temp_archive)) # we don't need curl actually

        unpack_destination = tooling_path # Path
        if sys.platform == "win32":
            unpack_destination = unpack_destination / "uv"
            unpack_destination.mkdir(exist_ok=True)
        subprocess.run(["tar", "-xvf", str(temp_archive), "-C", str(unpack_destination)], check=True)
        if platform == "linux" or platform == "darwin": # TODO: check MacOS
            dir_path = str(temp_archive).rsplit('.', 2)[0] # remove .tar.gz
            dir_path = Path(dir_path).absolute()
            dir_path.rename(dir_path.parent / "uv")
        print("Downloaded and unpacked uv")
        temp_archive.unlink()

    uv_cache_path = uv_path.resolve().parent / ".cache"
    uv_cache_path.mkdir(exist_ok=True)
    os.environ["UV_CACHE_DIR"] = str(uv_cache_path)

    return uv_path

def get_activation_hint():
    if sys.platform == "win32":
        return "cmd:\t\t.venv\\Scripts\\activate\n"\
            "git-bash:\tsource .venv/Scripts/activate\n"\
            "powershell:\t.\\.venv\\Scripts\\activate.ps1"
    else:
        return "source .venv/bin/activate"

def main():
    print(f"Running bootstrap script {__file__}")

    local_uv = prime_uv()
    requires_activation = not running_in_native_venv()
    if requires_activation:
        if venv_python.exists():
            print(f"{RED}Not running in native virtual environment{RESET}\n  expected:  {venv_python}\n  actual:    {str(sys.executable)}")
        else:
            subprocess.run([local_uv, "venv"], check=True)
            subprocess.run([local_uv, "pip", "install", "--upgrade", "pip"], check=True)
        print(f"Activate your shell with the appropriate command\n{get_activation_hint()}")
        if sys.platform == "win32":
            print(f"\n! Always execute this script as {GREEN}python3 bootstrap.py\n{RESET}")

    requirements_path = Path(__file__).parent.resolve() / "requirements.txt"
    if requirements_path.exists():
        print(f"Adding the requirements from {str(requirements_path)}")
        subprocess.run([local_uv, "pip", "install", "-r", str(requirements_path)], check=True)

    if requires_activation:
        print(f"\n\nDon't forget to activate your virtual environment:{GREEN}\n{get_activation_hint()}{RESET}")

if __name__ == "__main__":
    main()
