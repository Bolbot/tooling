#!/usr/bin/env python3

import argparse
import subprocess
import shutil
import sys
import os

from bootstrap import check_optional_utils, running_in_native_venv
from _platform_specific import prime_environment, get_activation_hint
from _resource_manager import get_compiler, update_project_config
from _text_colors import green_text, red_text, yellow_text
from _paths import main_project, venv_python


def start_in_background(program):
    runner = shutil.which("sh")
    if runner:
        subprocess.Popen([str(runner), "-c", program, "."], start_new_session=True, cwd=str(main_project), env=os.environ,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        if sys.platform == "win32":
            print(yellow_text("Your system does not have sh in PATH"))
            print("Note: git-bash usually comes with it, check for " + green_text("sh.exe") + " in C:\\Program Files\\Git\\usr\\bin\\")
            print("      if that is the case, add it that path to your PATH and restart the terminal")

            subprocess.Popen(["cmd", "/c", program, "."], start_new_session=True, cwd=str(main_project),
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print(red_text("No sh found in the system") + " make sure your system is not broken")
            sys.exit(1)


def main():
    check_optional_utils()
    update_project_config()
    prime_environment(get_compiler())

    arguments = argparse.ArgumentParser()
    arguments.add_argument("--vscode", action="store_true")
    arguments.add_argument("--zed", action="store_true")
    specified_arguments = arguments.parse_args()

    if specified_arguments.vscode:
        print("Starting Visual Studio Code...")
        start_in_background("code")

    if specified_arguments.zed:
        print("Starting Zed...")
        subprocess.Popen(["zed", "."], start_new_session=True, cwd=str(main_project),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not running_in_native_venv():
        if venv_python.exists():
            print("\nDon't forget to activate your virtual environment:\n" + green_text(get_activation_hint()))
        else:
            print("Run " + green_text("just setup") + " and follow instructions to activate your shell")


if __name__ == "__main__":
    main()
