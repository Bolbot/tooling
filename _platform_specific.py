import sys
from pathlib import Path
import urllib.request
import os
import subprocess

def python_in_venv():
    return "Scripts/python.exe" if sys.platform == "win32" else "bin/python"


def prime_uv():
    platform = sys.platform
    tooling_path = Path(__file__).parent.absolute().parent / ".tools"
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
        #subprocess.run(["curl", "-L", uv_url, "-o", str(temp_archive)], check=True)
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


def ninja_profile_name():
    if sys.platform == "win32":
        return "windows_ninja_clang"
    elif sys.platform == "linux":
       return "linux_ninja_clang"
    elif sys.platform == "darwin":              # TODO: macOS
        print("MacOS is not supported yet!")
        return None
    else:
        print("Unexpected platform. We support Windows (x64), MacOS (arm), and Linux (x64)")
        sys.exit(1)
