#!/usr/bin/env python3

from pathlib import Path
import sys
import subprocess
import shutil
from _platform_specific import prime_uv, get_activation_hint
from _resource_manager import resolve_resource, get_venv_python_path, get_requirements_path, get_main_project_path
from _text_colors import RED, YELLOW, GREEN, RESET


def running_in_native_venv() -> bool:
    if sys.prefix == sys.base_prefix:
        print(f"{YELLOW}Not running in virtual environment{RESET}")
        return False
    if Path(sys.executable).absolute() != get_venv_python_path():
        print(f"{RED}Running in unrelated virtual environment{RESET}\n\texpected:  {get_venv_python_path()}\n\tactual:    {str(sys.executable)}")
        return False
    return True


def check_optional_utils():
    if not shutil.which("code"):
        print(f"{YELLOW}Visual Studio Code can not be found.{RESET} Install it to use `just vscode` command (optional)")
    if not shutil.which("zed"):
        print("Zed can not be found. Install it to use `just zed` command (optional)")
    if not shutil.which("just"):
        print(f"{YELLOW}just is missing.{RESET} Install just 1.27 or later to use just commands (recommended)")


def main():
    resolve_resource(".justfile", "For usage tips see:\n\tjust --list\n")
    resolve_resource("project_paths.toml", "Make sure it contains valid paths to your C++, Rust, and test script")
    resolve_resource("requirements.txt", "Update it with actual requirements of your project")
    check_optional_utils()

    local_uv = prime_uv()
    requires_activation = not running_in_native_venv()
    if requires_activation:
        if not get_venv_python_path().exists():
            subprocess.run([local_uv, "venv", "--python", "3.13"], check=True, cwd=get_main_project_path())
            subprocess.run([local_uv, "pip", "install", "--upgrade", "pip"], check=True, cwd=get_main_project_path())

    print(f"Adding the requirements from {str(get_requirements_path())}")
    subprocess.run([local_uv, "pip", "install", "-r", str(get_requirements_path())], check=True, cwd=get_main_project_path())

    if requires_activation:
        print(f"\n\nDon't forget to activate your virtual environment:{GREEN}\n{get_activation_hint()}{RESET}")


if __name__ == "__main__":
    main()
