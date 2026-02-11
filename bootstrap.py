#!/usr/bin/env python3

from pathlib import Path
import sys
import subprocess
import shutil

from prebootstrap import prime_uv
from _platform_specific import prime_python, get_activation_hint
from _resource_manager import resolve_resource
from _text_colors import blue_text, red_text, yellow_text, green_text
from _paths import main_project, venv_python, requirements, venv_path, tooling_path


def running_in_native_venv() -> bool:
    if sys.prefix == sys.base_prefix:
        print(yellow_text("Not running in virtual environment"))
        return False
    if Path(sys.executable).absolute() != venv_python:
        if venv_python.exists():
            print(red_text("Running in unrelated virtual environment")
                + f"\n\texpected:  {venv_python}\n\tactual:    {str(sys.executable)}")
        return False
    return True


def check_optional_utils():
    if not shutil.which("code"):
        print(yellow_text("Visual Studio Code can not be found.") +" Install it to use `just vscode` command (optional)")
    if not shutil.which("zed"):
        print("Zed can not be found. Install it to use `just zed` command (optional)")
    if not shutil.which("just"):
        print(yellow_text("just is missing.") + " Install just 1.27 or later to use just commands (recommended)")


def clean_tooling_artifacts(proper_venv):
    if venv_path.exists() or tooling_path.exists():
        print("Removing the following paths:")

    if venv_path.exists():
        print("\t" + str(main_project.name) + "/" + blue_text(str(venv_path.name)))
        shutil.rmtree(venv_path)
    if tooling_path.exists():
        print("\t" + str(main_project.name) + "/" + blue_text(str(tooling_path.name)))
        shutil.rmtree(tooling_path)

    if proper_venv:
        print("Run " + green_text("deactivate") + " to restore your shell environment or "
                + green_text("just setup") + " to restore the venv")
    sys.exit(0)


def main():
    proper_venv = running_in_native_venv()
    if "--clean" in sys.argv:
        clean_tooling_artifacts(proper_venv)

    resolve_resource(".justfile", "for usage tips see:\n\tjust --list\n")
    resolve_resource("project_config.toml", "verify that its values suit your project")
    resolve_resource("requirements.txt", "update it with actual requirements of your project")
    check_optional_utils()

    local_uv = prime_uv()
    if not proper_venv:
        if not venv_python.exists():
            subprocess.run([local_uv, "venv", "--python", "3.13"], check=True, cwd=str(main_project))
            subprocess.run([local_uv, "pip", "install", "--upgrade", "pip"], check=True, cwd=str(main_project))
    prime_python(venv_python)

    print(f"Adding the requirements from {str(requirements)}")
    subprocess.run([local_uv, "pip", "install", "-r", str(requirements)], check=True, cwd=str(main_project))

    if not proper_venv:
        print("\n\nDon't forget to activate your virtual environment:\n" + green_text(get_activation_hint()))


if __name__ == "__main__":
    main()
