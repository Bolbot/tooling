#!/usr/bin/env python3

from pathlib import Path
from typing import Final
import sys
import subprocess
import urllib.request
import os
import shutil


RED    : Final = "\033[31m"
YELLOW : Final = "\033[33m"
GREEN  : Final = "\033[32m"
RESET  : Final = "\033[0m"

main_project: Final = Path(__file__).parent.absolute().parent
tooling_path: Final = main_project / ".tools"
venv_path   : Final = main_project / ".venv"
venv_python : Final = venv_path / "Scripts/python.exe" if sys.platform == "win32" else venv_path / "bin/python"


def propagate_justfile():
    justfile_source = Path(__file__).resolve().parent / ".justfile"

    main_justfile = main_project / ".justfile"
    if not main_justfile.exists():
        print(f"Adding {GREEN}.justfile{RESET} to {main_project}\n"\
            f"Don't forget to add it to your VCS (e. g. {GREEN}git add .justfile{RESET})\n"\
            "Usage:\n\tjust --list\n")
        shutil.copyfile(str(justfile_source), str(main_justfile))
    else:
        print(f"{YELLOW}Found .justfile in {main_project}{RESET}\nExamine tooling/.justfile to verify yours is relevant")


def running_in_native_venv() -> bool:
    if sys.prefix == sys.base_prefix:
        print(f"{YELLOW}Not running in virtual environment{RESET}")
        return False
    if Path(sys.executable).absolute() != venv_python.absolute():
        print(f"{RED}Running in unrelated virtual environment{RESET}\n\texpected:  {venv_python}\n\tactual:    {str(sys.executable)}")
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


def prime_requirements():
    fallback_requirements = Path(__file__).resolve().parent / "requirements.txt"

    requirements_path = main_project / "requirements.txt"
    if not requirements_path.exists():
        print(f"{YELLOW}No requirements.txt found in {str(main_project)}{RESET}\n"\
            f"Default {GREEN}requirements.txt{RESET} is provided by bootstrap script.\n"\
            f"Don't forget to add it to your project VCS (e. g. {GREEN}git add requirements.txt{RESET})\n")
        shutil.copyfile(str(fallback_requirements), str(requirements_path))

    return requirements_path


def main():
    print(f"Running bootstrap script {__file__}")

    propagate_justfile()

    local_uv = prime_uv()
    requires_activation = not running_in_native_venv()
    if requires_activation:
        if not venv_python.exists():
            subprocess.run([local_uv, "venv", "--python", "3.13"], check=True, cwd=main_project)
            subprocess.run([local_uv, "pip", "install", "--upgrade", "pip"], check=True, cwd=main_project)

    requirements_path = prime_requirements()
    print(f"Adding the requirements from {str(requirements_path)}")
    subprocess.run([local_uv, "pip", "install", "-r", str(requirements_path)], check=True, cwd=main_project)

    if requires_activation:
        print(f"\n\nDon't forget to activate your virtual environment:{GREEN}\n{get_activation_hint()}{RESET}")

if __name__ == "__main__":
    main()
