#!/usr/bin/env python3

import filecmp
from pathlib import Path
from typing import Final
import sys
import subprocess
import shutil
from _platform_specific import python_in_venv, prime_uv, get_activation_hint

RED    : Final = "\033[31m"
YELLOW : Final = "\033[33m"
GREEN  : Final = "\033[32m"
RESET  : Final = "\033[0m"

main_project: Final = Path(__file__).parent.absolute().parent
venv_path   : Final = main_project / ".venv"
venv_python : Final = venv_path / python_in_venv()


def propagate_justfile():
    justfile_source = Path(__file__).resolve().parent / ".justfile"

    main_justfile = main_project / ".justfile"
    if not main_justfile.exists():
        print(f"Adding {GREEN}.justfile{RESET} to {main_project}\n"\
            f"Don't forget to add it to your VCS (e. g. {GREEN}git add .justfile{RESET})\n"\
            "Usage:\n\tjust --list\n")
        shutil.copyfile(str(justfile_source), str(main_justfile))
    elif not filecmp.cmp(justfile_source, main_justfile):
        print(f"Found {YELLOW}{main_justfile}{RESET}\nExamine {justfile_source} to verify yours is relevant")

    if not shutil.which("just"):
        print(f"{YELLOW}just is missing. Install just 1.27 or later to use just commands{RESET}")


def propagate_paths():
    config_source = Path(__file__).resolve().parent / "project_paths.toml"

    main_config = main_project / "project_paths.toml"
    if not main_config.exists():
        print(f"Adding {GREEN}project_path.toml{RESET} to {main_project}\n"\
            f"{YELLOW}Fill it with relative paths to your C++ and Rust directories!{RESET}\n"\
            f"Don't forget to add it to your VCS (e. g. {GREEN}git add project_paths.toml{RESET})")
        shutil.copyfile(str(config_source), str(main_config))
    else:
        print(f"Found {YELLOW} {main_config}{RESET}\nMake sure it has relevant paths")


def running_in_native_venv() -> bool:
    if sys.prefix == sys.base_prefix:
        print(f"{YELLOW}Not running in virtual environment{RESET}")
        return False
    if Path(sys.executable).absolute() != venv_python.absolute():
        print(f"{RED}Running in unrelated virtual environment{RESET}\n\texpected:  {venv_python}\n\tactual:    {str(sys.executable)}")
        return False
    return True


def prime_requirements():
    fallback_requirements = Path(__file__).resolve().parent / "requirements.txt"

    requirements_path = main_project / "requirements.txt"
    if not requirements_path.exists():
        print(f"{YELLOW}No requirements.txt found in {str(main_project)}{RESET}\n"\
            f"Default {GREEN}requirements.txt{RESET} is provided by bootstrap script.\n"\
            f"Don't forget to add it to your project VCS (e. g. {GREEN}git add requirements.txt{RESET})\n")
        shutil.copyfile(str(fallback_requirements), str(requirements_path))

    return requirements_path


def check_ide():
    if not shutil.which("code"):
        print(f"{YELLOW}Visual Studio Code can not be found.{RESET} Install it to use `just vscode` command (optional)")
    if not shutil.which("zed"):
        print("Zed can not be found. Install it to use `just zed` command (optional)")


def main():
    print(f"Running bootstrap script {__file__}")

    propagate_justfile()

    propagate_paths()

    local_uv = prime_uv()
    requires_activation = not running_in_native_venv()
    if requires_activation:
        if not venv_python.exists():
            subprocess.run([local_uv, "venv", "--python", "3.13"], check=True, cwd=main_project)
            subprocess.run([local_uv, "pip", "install", "--upgrade", "pip"], check=True, cwd=main_project)

    requirements_path = prime_requirements()
    print(f"Adding the requirements from {str(requirements_path)}")
    subprocess.run([local_uv, "pip", "install", "-r", str(requirements_path)], check=True, cwd=main_project)

    check_ide()

    if requires_activation:
        print(f"\n\nDon't forget to activate your virtual environment:{GREEN}\n{get_activation_hint()}{RESET}")

if __name__ == "__main__":
    main()
