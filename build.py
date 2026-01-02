#!/usr/bin/env python3

import argparse
#from random import choices
from typing import Final
from pathlib import Path
from colorama import Fore, Style
import sys
import tomllib
import shutil
import subprocess

main_project: Final = Path(__file__).parent.absolute().parent
config_file:  Final = main_project / "project_paths.toml"
last_used:    Final = main_project / ".tools" / "last_built_config.txt"

def check_presence(tool):
    if shutil.which(tool) is None:
        print(f"{Fore.RED}Failed to find {tool}. Can not proceed{Style.RESET_ALL}")
        sys.exit(1)

def load_config():
    if not config_file.exists():
        print(f"{Fore.RED}Could not find {str(config_file)}{Style.RESET_ALL}\nRerun {Fore.GREEN}just setup{Style.RESET_ALL}")
        sys.exit(1)
    print(f"Found {Fore.LIGHTBLUE_EX}{str(config_file)}{Style.RESET_ALL}")
    return tomllib.loads(config_file.read_text())

def get_conanfile(cpp_directory):
    result = cpp_directory / "conanfile.txt"
    if result.exists():
        return result
    result = cpp_directory / "conanfile.py"
    return result if result.exists() else None


def generate_cpp(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"C++ build directory:\t{build_dir}")

    check_presence("cmake")
    check_presence("ninja")

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        print("Conan support is in progress")

        profiles_directory = main_project / "tooling" / "conan_profiles"
        conan_profile = profiles_directory / ("windows_ninja_clang" if sys.platform == "win32" else "linux_ninja_clang") # TODO: macOS
        if not conan_profile.exists():
            print(f"Could not find {Fore.RED}{conan_profile}{Style.RESET_ALL}\nCheck the tooling submodule integrity")
            sys.exit(1)
        else:
            print(f"Using {conan_profile}")

        check_presence("conan")
        subprocess.run(["conan", "install", ".", "--build=missing",
            "--profile", str(conan_profile),
            "--settings", f"build_type={build_type}"],
            cwd=cpp_directory, check=True)
    else:
        subprocess.run(["cmake", "-S", ".", "-B", str(build_dir), "-G", "Ninja",
            f"-DCMAKE_BUILD_TYPE={build_type}", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"],
            cwd=cpp_directory, check=True)


def build_cpp(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"C++ build directory:\t{build_dir}")

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        cmake_preset = "conan-debug" if build_type == "Debug" else "conan-release"
        subprocess.run(["cmake", "--preset", cmake_preset], cwd=cpp_directory, check=True)
        subprocess.run(["cmake", "--build", "--preset", cmake_preset], cwd=cpp_directory, check=True)
    else:
        subprocess.run(["cmake", "--build", str(build_dir)], cwd=cpp_directory, check=True)

    set_last_used_config(build_type)
    # TODO: consider parsing config for C++ and Rust targets
    #targets = cpp_config.get("targets", ["all"])
    #print(f"Targets: {targets}")


def build_rust(rust_directory, build_type):
    print(f"Building {build_type} rust in {rust_directory}")

    check_presence("cargo")

    if build_type == "Release":
        subprocess.run(["cargo", "build", "--release"], cwd=rust_directory, check=True)
    else:
        subprocess.run(["cargo", "build"], cwd=rust_directory, check=True)

    set_last_used_config(build_type)


def get_last_used_config():
    if not last_used.exists():
        return None
    config = last_used.read_text()
    if config != "Debug" and config != "Release":
        print(f"{Fore.RED}Broken {str(config)}{Style.RESET_ALL}\nRemoving it and building from scratch")
        last_used.unlink()
        return None
    return config

def set_last_used_config(build_type):
    last_used.write_text(build_type)

def main():
    config = load_config()
    cpp_config = config.get("cpp")
    cpp_directory = Path(cpp_config.get("path", "cpp")).resolve() if cpp_config else None
    print(f"C++  directory: {cpp_directory}")
    rust_config = config.get("rust")
    rust_directory = Path(rust_config.get("path", "rust")).resolve() if rust_config else None
    print(f"Rust directory: {rust_directory}")

    arguments = argparse.ArgumentParser()
    arguments.add_argument("--config", choices=["Debug", "Release"])
    arguments.add_argument("--clean", action="store_true")
    specified_arguments = arguments.parse_args()

    if len(sys.argv) == 1:
        # if there was last used, rebuild it, and bail; otherwise, fallback to the initial dual build later on
        build_type = get_last_used_config()
        if build_type:
            print(f"Rebuilding the last build: {build_type}")
            if cpp_config:
                build_cpp(cpp_directory, build_type)
            if rust_config:
                build_rust(rust_directory, build_type)
            sys.exit(0)

    if specified_arguments.clean:
        print("Deleting the following paths:")
        if cpp_directory:
            cpp_build_dir = cpp_directory / "build"
            if cpp_build_dir.exists():
                print(f"C++:  {cpp_build_dir}")
                shutil.rmtree(cpp_build_dir)
            disposable_presets = cpp_directory / "CMakeUserPresets.json"
            if disposable_presets.exists():
                print(f"      {disposable_presets}")
                disposable_presets.unlink()
        if rust_directory:
            rust_build_dir = rust_directory / "target"
            if rust_build_dir.exists():
                print(f"Rust: {rust_build_dir}")
                shutil.rmtree(rust_build_dir)
        if last_used.exists():
            print(f"Meta: {last_used}")
            last_used.unlink()
        sys.exit(0)

    build_configs = [specified_arguments.config] if specified_arguments.config else ["Release", "Debug"]
    print(f"Build configs: {build_configs}")
    if cpp_config:
        for build_type in build_configs:
            generate_cpp(cpp_directory, build_type)
            build_cpp(cpp_directory, build_type)

    if rust_config:
        for build_type in build_configs:
            build_rust(rust_directory, build_type)


if __name__ == "__main__":
    main()
