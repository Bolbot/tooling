#!/usr/bin/env python3

import argparse
from _text_colors import RED, YELLOW, GREEN, BLUE, RESET
import sys
import shutil
import subprocess
from _platform_specific import prime_environment
from _resource_manager import get_conanfile, check_presence, get_verified_path, update_cpp_config
from _resource_manager import build_and_verify, get_last_used_config, set_last_used_config
from _resource_manager import get_cmake_preset_name, get_generate_command, get_compiler


success = True


def generate_cpp(cpp_directory, build_type):
    check_presence("cmake")
    generate_command = get_generate_command(cpp_directory, build_type)
    print(f"Generating C++ project: {' '.join(generate_command)}")
    subprocess.run(generate_command, cwd=cpp_directory, check=True)


def build_cpp(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"Building {build_type} C++ in {build_dir}")

    build_command = ["cmake", "--build"]

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        cmake_preset = get_cmake_preset_name(build_type)
        subprocess.run(["cmake", "--preset", cmake_preset], cwd=cpp_directory, check=True)
        build_command += ["--preset", "conan-debug" if build_type == "Debug" else "conan-release"]
    else:
        build_command += [str(build_dir), "--config", build_type]

    if not build_and_verify(build_command, cpp_directory):
        global success
        success = False

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


def main():
    cpp_directory = get_verified_path("cpp")
    rust_directory = get_verified_path("rust")
    update_cpp_config()
    prime_environment(get_compiler())

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
            if success:
                set_last_used_config(build_type)
                return

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
        return

    build_configs = [specified_arguments.config] if specified_arguments.config else ["Release", "Debug"]
    for build_type in build_configs:
        if cpp_directory:
            generate_cpp(cpp_directory, build_type)
            build_cpp(cpp_directory, build_type)

        if rust_directory:
            build_rust(rust_directory, build_type)

        if success:
            set_last_used_config(build_type)


if __name__ == "__main__":
    main()
    sys.exit(0 if success else 1)
