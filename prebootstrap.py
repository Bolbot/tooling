#!/usr/bin/env python3

import sys
from pathlib import Path
import urllib.request
import os
import subprocess
import shutil
from typing import Final

RED    : Final = "\033[31m"
YELLOW : Final = "\033[33m"
GREEN  : Final = "\033[32m"
BLUE   : Final = "\033[34m"
RESET  : Final = "\033[0m"

main_project: Final = Path(__file__).parent.absolute().parent
temp_venv: Final = ".venv-temporary"


def prime_uv():
    platform = sys.platform
    tooling_path = main_project / ".tools"
    uv_path = tooling_path / "uv" / ("uv.exe" if platform == "win32" else "uv")

    if not uv_path.exists():
        print("Obtaining local copy of uv...")
        tooling_path.mkdir(exist_ok=True)

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
        urllib.request.urlretrieve(uv_url, str(temp_archive)) # we don't need curl actually

        unpack_destination = tooling_path # Path
        if platform == "win32":
            unpack_destination = unpack_destination / "uv"
            unpack_destination.mkdir(exist_ok=True)
        subprocess.run(["tar", "-xvf", str(temp_archive), "-C", str(unpack_destination)], check=True)
        if platform == "linux" or platform == "darwin": # TODO: check MacOS
            dir_path = str(temp_archive).rsplit('.', 2)[0] # remove .tar.gz
            dir_path = Path(dir_path).absolute()
            dir_path.rename(dir_path.parent / "uv")
        print("Successfully downloaded and unpacked uv")
        temp_archive.unlink()

    uv_cache_path = uv_path.resolve().parent / ".cache"
    uv_cache_path.mkdir(exist_ok=True)
    os.environ["UV_CACHE_DIR"] = str(uv_cache_path)

    return uv_path


def main():
    if sys.version_info >= (3, 11):
        print(f"Your python version is {BLUE}{sys.version_info.major}.{sys.version_info.minor}{RESET}")
        print(f"No need for prebootstrap.py, you can run {GREEN}bootstrap.py{RESET} directly")
        sys.exit(0)

    local_uv = prime_uv()
    subprocess.run([local_uv, "venv", temp_venv, "--python", "3.13"], check=True, cwd=main_project)

    justfile = main_project / ".justfile"
    bootstrap = main_project / "tooling" / "bootstrap.py"
    if shutil.which("just") and justfile.exists():
        print(f"Run {GREEN}just setup{RESET}\n{YELLOW}Afterward, you can delete {RED}{temp_venv}{RESET}")
    else:
        if not bootstrap.exists():
            print(f"{YELLOW}Check your tooling submodule integrity:{RESET} make sure bootstrap.py is there")
        print(f"Run {GREEN}python tooling/bootstrap.py{RESET}\n{YELLOW}Afterward, you can delete {RED}{temp_venv}{RESET}")


if __name__ == "__main__":
    main()
