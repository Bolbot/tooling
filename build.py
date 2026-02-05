#!/usr/bin/env python3

import argparse
from _text_colors import blue_text
import sys
import shutil
import subprocess
from _platform_specific import prime_environment
from _resource_manager import update_project_config, check_presence, get_verified_path
from _resource_manager import get_compiler, get_generate_command, get_build_command
from _resource_manager import get_cargo_target, get_cargo_features
from _resource_manager import build_and_verify, get_last_used_config, set_last_used_config


success = True
cmake_directory = None
rust_directory = None


def generate_cmake(build_type):
    check_presence("cmake")
    generate_command = get_generate_command(cmake_directory, build_type)
    print("Generating CMake project: " + ' '.join(generate_command))
    subprocess.run(generate_command, cwd=str(cmake_directory), check=True)


def build_cmake(build_type):
    build_command = get_build_command(cmake_directory, build_type)
    print("Building CMake project: " + ' '.join(build_command))

    if not build_and_verify(build_command, cmake_directory):
        global success
        success = False


def build_rust(build_type):
    print("Building " + build_type + " rust in " + str(rust_directory))
    check_presence("cargo")

    build_command = ["cargo", "build"]
    if build_type == "Release":
        build_command.append("--release")

    target = get_cargo_target(rust_directory)
    if target:
        build_command += ["--target", target]

    features = get_cargo_features(rust_directory)
    if features:
        build_command += ["--features", ','.join(features)]

    print("Building Rust project: " + ' '.join(build_command))
    subprocess.run(build_command, cwd=str(rust_directory), check=True)


def clean_build_artifacts():
    print("Deleting the following paths:")
    if cmake_directory:
        cmake_build_dir = cmake_directory / "build"
        if cmake_build_dir.exists():
            print("CMake:  " + str(cmake_build_dir))
            shutil.rmtree(cmake_build_dir)
        disposable_presets = cmake_directory / "CMakeUserPresets.json"
        if disposable_presets.exists():
            print("      " + str(disposable_presets))
            disposable_presets.unlink()

    if rust_directory:
        rust_build_dir = rust_directory / "target"
        if rust_build_dir.exists():
            print("Rust:   " + str(rust_build_dir))
            shutil.rmtree(rust_build_dir)

    set_last_used_config(None)


def main():
    global cmake_directory, rust_directory
    cmake_directory = get_verified_path("cmake")
    rust_directory = get_verified_path("rust")

    arguments = argparse.ArgumentParser()
    arguments.add_argument("--clean", action="store_true")
    arguments.add_argument("--config", choices=["Debug", "Release"])
    specified_arguments = arguments.parse_args()

    if specified_arguments.clean:
        clean_build_artifacts()
        return

    update_project_config()
    prime_environment(get_compiler())

    if len(sys.argv) == 1:
        # no explicit argument - building the last successful config or fall back to both Release and Debug
        build_type = get_last_used_config()
        if build_type:
            print(blue_text("Rebuilding " + build_type))
            if cmake_directory:
                build_cmake(build_type)
            if rust_directory:
                build_rust(build_type)
            if success:
                set_last_used_config(build_type)
                return
        else:
            print("No prior successful build found - " + blue_text("building Release and Debug"))

    build_configs = [specified_arguments.config] if specified_arguments.config else ["Release", "Debug"]
    for build_type in build_configs:
        if cmake_directory:
            generate_cmake(build_type)
            build_cmake(build_type)

        if rust_directory:
            build_rust(build_type)

        if success:
            set_last_used_config(build_type)


if __name__ == "__main__":
    main()
    sys.exit(0 if success else 1)
