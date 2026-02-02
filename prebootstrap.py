#!/usr/bin/env python3

import sys
import os
import platform
from pathlib import Path
import subprocess
import shutil

from _paths import main_project
from _text_colors import red_text, green_text, blue_text, yellow_text

temp_venv = ".venv-temporary"


def prime_uv():
    current_os = sys.platform
    tooling_path = main_project / ".tools"
    uv_path = tooling_path / "uv" / ("uv.exe" if current_os == "win32" else "uv")

    if not uv_path.exists():
        tooling_path.mkdir(exist_ok=True)

        try:
            archive_name = {
                "win32" : "uv-x86_64-pc-windows-msvc.zip",
                "darwin": "uv-x86_64-apple-darwin.tar.gz" if platform.machine() == "x86_64"
                     else "uv-aarch64-apple-darwin.tar.gz",
                "linux" : "uv-x86_64-unknown-linux-gnu.tar.gz"
            }[current_os]
        except KeyError:
            print(red_text("Unexpected OS!") + " We support Windows (x64), MacOS (arm or x64), and Linux (x64)")
            sys.exit(1)
        uv_url = "https://github.com/astral-sh/uv/releases/download/0.9.28/" + archive_name
        temp_archive = tooling_path / archive_name
        print("Downloading " + archive_name.split('.')[0] + " for " + platform.machine())

        try:
            import urllib.request
            urllib.request.urlretrieve(uv_url, str(temp_archive))
        except Exception as download_error:
            if shutil.which("curl"):
                print(yellow_text("urllib failed: {}, ".format(download_error)) + "trying curl...")
                res = subprocess.run(["curl", "-fL", uv_url, "-o", str(temp_archive)])
                if res.returncode != 0:
                    print(red_text("curl also failed: {}".format(res.stderr)))
                    sys.exit(1)
            else:
                print(red_text("urllib failed: {}; no curl. Terminating. ".format(download_error)))
                sys.exit(1)

        unpack_destination = tooling_path
        if current_os == "win32":
            unpack_destination = unpack_destination / "uv"
            unpack_destination.mkdir(exist_ok=True)
        subprocess.run(["tar", "-xvf", str(temp_archive), "-C", str(unpack_destination)], check=True)
        if current_os == "linux" or current_os == "darwin":
            dir_path = str(temp_archive).rsplit('.', 2)[0] # remove .tar.gz
            dir_path = Path(dir_path).absolute()
            dir_path.rename(dir_path.parent / "uv")
        print("Successfully downloaded and unpacked uv")
        temp_archive.unlink()

    uv_cache_path = uv_path.resolve().parent / ".cache"
    uv_cache_path.mkdir(exist_ok=True)
    os.environ["UV_CACHE_DIR"] = str(uv_cache_path)

    return uv_path


def print_run_suggestion():
    justfile = main_project / ".justfile"
    bootstrap = main_project / "tooling" / "bootstrap.py"
    run_suggestion = "python tooling/bootstrap.py"

    if shutil.which("just") and justfile.exists():
        run_suggestion = "just setup"
    elif not bootstrap.exists():
        print(yellow_text("Check your tooling submodule integrity:") + " make sure bootstrap.py is there")

    print("Run " + green_text(run_suggestion))


def main():
    if sys.version_info >= (3, 11):
        print("Your python " + blue_text(str(sys.version_info.major) + '.' + str(sys.version_info.minor))
            + " is modern enough, prebootstrap.py is not required")
        print_run_suggestion()
        sys.exit(0)

    local_uv = prime_uv()
    subprocess.run([local_uv, "venv", temp_venv, "--python", "3.13"], check=True, cwd=str(main_project))

    print_run_suggestion()
    print(yellow_text("Afterward, you can delete ") + red_text(temp_venv))


if __name__ == "__main__":
    main()
