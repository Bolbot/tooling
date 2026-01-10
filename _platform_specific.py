import sys
from pathlib import Path
import urllib.request
import os
import subprocess


optional_environment = None


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
        print("Successfully downloaded and unpacked uv")
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

# TODO: generalize and reuse
def get_lldb_hint():
    if sys.platform == "win32":
        return "Download and install `MSYS2-x86_64`, launch and run:"\
            "\n\tpacman -Syu\n\tpacman -S --needed base-devel mingw-w64-clang-x86_64-toolchain"\
            "\nAdd the path to clang64/bin to your PATH"
    elif sys.platform == "linux":
       return "\twget https://apt.llvm.org/llvm.sh\n\tchmod +x llvm.sh\n\tsudo ./llvm.sh 21\n\tsudo apt install clang-21 lldb-21"
    elif sys.platform == "darwin":
        return "\tbrew install llvm@21\n\texport PATH=\"/opt/homebrew/opt/llvm@21/bin:$PATH\""
    else:
        print("Unexpected platform. We support Windows (x64), MacOS (arm), and Linux (x64)")
        sys.exit(1)


def prime_environment():
    if sys.platform != "win32":
        return None

    vswhere = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.exists():
        return None

    vs_path = subprocess.run([str(vswhere), "-property", "installationPath"], capture_output=True, text=True)
    activator_path = Path(vs_path.stdout.strip()).resolve() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not activator_path.exists():
        return None

    msv_updates = subprocess.run(["cmd.exe", "/c", str(activator_path), "&&", "set"], capture_output=True, text=True)
    for line in msv_updates.stdout.split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value.strip()


def get_profile_path(profiles_dir, profile_name):
    if sys.platform == "win32":
        profiles_dir /= "windows"
    elif sys.platform == "linux":
        profiles_dir /= "linux"
    elif sys.platform == "darwin":
        profiles_dir /= "macos"
    else:
        print("Unexpected platform. We support Windows (x64), MacOS (arm), and Linux (x64)")
        sys.exit(1)

    profile_path = profiles_dir / profile_name
    return profile_path


def windows_proof_cmake_preset(build_type, use_ninja):
    if sys.platform == "win32" and not use_ninja:
        return "conan-default"
    else:
        return "conan-debug" if build_type == "Debug" else "conan-release"


def try_build(build_command, cpp_directory, attempts):
    if attempts == 1 or sys.platform != "win32":
        result = subprocess.run(build_command, cwd=cpp_directory)
        return result.returncode == 0

    while True:
        result = subprocess.run(build_command, cwd=cpp_directory, stdout=subprocess.PIPE, text=True)
        attempts -= 1

        if "ninja: error: failed recompaction: Permission denied" in result.stdout and attempts > 0:
            print(f"Ninja spuriously fails the Windows build. Retrying {attempts} more time{ "s" if attempts > 1 else "" }...")
        else:
            attempts = 0

        if attempts == 0:
            print(f"{result.stdout}")
            return result.returncode == 0
