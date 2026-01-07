#!/usr/bin/env python3

import argparse
from typing import Final
from pathlib import Path
from _text_colors import RED, YELLOW, BLUE, RESET
import sys
import tomllib
import shutil
import subprocess
from _platform_specific import get_lldb_hint
from _resource_manager import get_conanfile, get_conan_profile, check_presence, get_verified_path
from _resource_manager import load_config, get_last_used_config, set_last_used_config


def generate_cpp(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"C++ build directory:\t{build_dir}")

    check_presence("cmake")
    check_presence("ninja")
    if not check_presence("lldb", False):
        print(f"{YELLOW}Could not find lldb{RESET}\nInstall it if you need to debug:\n{get_lldb_hint()}")
    check_presence("clang")

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        conan_profile = get_conan_profile()
        if not conan_profile.exists():
            print(f"Could not find {RED}{conan_profile}{RESET}\nCheck the tooling submodule integrity")
            sys.exit(1)

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


def main():
    config = load_config()
    cpp_directory = get_verified_path(config, "cpp")
    rust_directory = get_verified_path(config, "rust")

    arguments = argparse.ArgumentParser()
    arguments.add_argument("--config", choices=["Debug", "Release"])
    arguments.add_argument("--clean", action="store_true")
    specified_arguments = arguments.parse_args()

    if len(sys.argv) == 1:
        # if there was last used, rebuild it, and bail; otherwise, fallback to the initial dual build later on
        build_type = get_last_used_config()
        if build_type:
            print(f"{BLUE}Rebuilding {build_type}{RESET}")
            if cpp_directory:
                build_cpp(cpp_directory, build_type)
            if rust_directory:
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
        set_last_used_config(None)
        sys.exit(0)

    build_configs = [specified_arguments.config] if specified_arguments.config else ["Release", "Debug"]
    print(f"Build configs: {build_configs}")
    if cpp_directory:
        for build_type in build_configs:
            generate_cpp(cpp_directory, build_type)
            build_cpp(cpp_directory, build_type)

    if rust_directory:
        for build_type in build_configs:
            build_rust(rust_directory, build_type)


if __name__ == "__main__":
    main()
