#!/usr/bin/env python3
#!/usr/bin/env python

from pathlib import Path
from typing import Final
import sys
import subprocess
import urllib.request
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

tooling_path: Final = Path(__file__).parent.absolute() / ".tools"
venv_path   : Final = Path(__file__).parent.absolute() / ".venv"
venv_python : Final = venv_path / "Scripts/python.exe" if sys.platform == "win32" else venv_path / "bin/python"

def running_in_native_venv() -> bool:
    if Path(sys.executable).resolve() != venv_python.resolve():
        print(f"Wrong python:\n  expected:  {venv_python}\n  actual:    {str(sys.executable)}")
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
                "darwin" : "uv-aarch64-apple-darwin.tar.gz",
                "linux" : "uv-x86_64-unknown-linux-gnu.tar.gz"
                }[platform]
        except KeyError:
            print("Unexpected platform. We support Windows (x64), MacOS (arm), and Linux (x64)")
            sys.exit(1)
        uv_url = "https://github.com/astral-sh/uv/releases/download/0.9.18/" + archive_name

        temp_archive = tooling_path / archive_name
        #subprocess.run(["curl", "-L", uv_url, "-o", str(temp_archive)], check=True)
        urllib.request.urlretrieve(uv_url, str(temp_archive)) # we don't need curl actually

        uv_dest = tooling_path / "uv"
        if platform == "win32":
            subprocess.run(["unzip", str(temp_archive), "-d", str(uv_dest)], check=True)
        elif platform == "linux":
            subprocess.run(["tar", "-xvf", str(temp_archive), "-C", str(tooling_path)])
            dir_path = str(temp_archive).rsplit('.', 2)[0] # remove .tar.gz
            dir_path = Path(dir_path).absolute()
            dir_path.rename(dir_path.parent / "uv")
        print("Downloaded and unpacked uv")
        temp_archive.unlink()

    return uv_path

def main():
    colorama_init()
    print("Bootstrap script")

    local_uv = prime_uv()
    correct_venv = running_in_native_venv()
    if not correct_venv:
        if venv_python.exists():
            print(f"{Fore.RED}Not running in native virtual environment{Style.RESET_ALL}")
            print(f"Run {Fore.GREEN}.venv\\Scripts\\activate" if sys.platform == "win32" else f"Run {Fore.GREEN} source .venv/bin/activate")
            if (sys.platform == "win32"):
                print(f"{Style.RESET_ALL}\n! Always execute this script as {Fore.GREEN}python bootstrap.py\n")
            #sys.exit(1)
        else:
            subprocess.run([local_uv, "venv"], check=True)
            subprocess.run([local_uv, "pip", "install", "--upgrade", "pip"], check=True)

    requirements_path = Path(__file__).parent.resolve() / "requirements.txt"
    if requirements_path.exists():
        print(f"Adding the requirements from {str(requirements_path)}")
        subprocess.run([local_uv, "pip", "install", "-r", str(requirements_path)], check=True)

    if not correct_venv:
        print(f"\n\nDon't forget to activate your environment:{Fore.GREEN}")
        print("Run .venv\\Scripts\\activate" if sys.platform == "win32" else "Run source .venv/bin/activate")

if __name__ == "__main__":
    main()
