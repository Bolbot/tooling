import sys
from pathlib import Path
import os
import subprocess
import shutil

from _text_colors import red_text, yellow_text, green_text


def prime_python(venv_python_path):
    if sys.platform == "win32":
        python3_in_venv = venv_python_path.parent / "python3.exe"
        if not python3_in_venv.exists():
            shutil.copyfile(venv_python_path, python3_in_venv)
    elif sys.platform == "linux":
        if not shutil.which("python"):
            print("python → python3 not configured, consider installing it this way:")
            print("\tsudo apt update\n\tsudo apt install python-is-python3")


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


def prime_environment(compiler):
    windows_specific_compiler = compiler == "msvc" or compiler == "clang-cl"
    if sys.platform != "win32":
        if windows_specific_compiler:
            print(red_text(compiler) + " is Windows only. Consider using " + green_text("clang") + " instead")
            sys.exit(1)
        else:
            return None

    if not windows_specific_compiler:
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
        print(red_text("Unexpected platform.") + " We support Windows (x64), MacOS (arm), and Linux (x64)")
        sys.exit(1)

    profile_path = profiles_dir / profile_name
    return profile_path


def windows_proof_cmake_preset(build_type, use_ninja):
    if sys.platform == "win32" and not use_ninja:
        return "conan-default"
    else:
        return "conan-debug" if build_type == "Debug" else "conan-release"


def windows_proof_cargo_target(rust_directory, compiler, use_ninja):
    if sys.platform != "win32":
        return None
    if compiler == "msvc" or compiler == "clang-cl" or not use_ninja:
        return None

    target = "x86_64-pc-windows-gnu"
    result = subprocess.run(["rustup", "target", "list", "--installed"], cwd=str(rust_directory), stdout=subprocess.PIPE, text=True)
    if target not in result.stdout:
        print(yellow_text(target + " is not installed, using default target, possible ABI incompatibility"))
        print("To enable " + target + " run " + green_text("rustup target add " + target) + " from " + str(rust_directory))
        return None
    return target



def try_build(build_command, cmake_directory, attempts):
    if attempts == 1 or sys.platform != "win32":
        result = subprocess.run(build_command, cwd=str(cmake_directory))
        return result.returncode == 0

    while True:
        result = subprocess.run(build_command, cwd=str(cmake_directory), stdout=subprocess.PIPE, text=True)
        attempts -= 1

        if "ninja: error: failed recompaction: Permission denied" in result.stdout and attempts > 0:
            print(f"Ninja spuriously fails the Windows build. Retrying {attempts} more time{ 's' if attempts > 1 else '' }...")
        else:
            attempts = 0

        if attempts == 0:
            print(f"{result.stdout}")
            return result.returncode == 0


def print_compiler_warning(compiler, windows_generator):
    if sys.platform != "win32" or not windows_generator:
        return
    if compiler != "clang-cl" and compiler != "msvc":
        print(yellow_text("MSVC Generator ignores {}".format(compiler)) + "\nCompatible compilers: msvc or clang-cl")
        print("If you need {}, try to use ".format(compiler) + green_text("ninja") + " instead\n")
