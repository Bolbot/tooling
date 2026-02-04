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
cpp_directory = None
rust_directory = None


def generate_cpp(build_type):
    check_presence("cmake")
    generate_command = get_generate_command(cpp_directory, build_type)
    print("Generating C++ project: " + ' '.join(generate_command))
    subprocess.run(generate_command, cwd=str(cpp_directory), check=True)


def build_cpp(build_type):
    build_command = get_build_command(cpp_directory, build_type)
    print("Building C++ project: " + ' '.join(build_command))

    if not build_and_verify(build_command, cpp_directory):
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
    if cpp_directory:
        cpp_build_dir = cpp_directory / "build"
        if cpp_build_dir.exists():
            print("C++:  " + str(cpp_build_dir))
            shutil.rmtree(cpp_build_dir)
        disposable_presets = cpp_directory / "CMakeUserPresets.json"
        if disposable_presets.exists():
            print("      " + str(disposable_presets))
            disposable_presets.unlink()

    if rust_directory:
        rust_build_dir = rust_directory / "target"
        if rust_build_dir.exists():
            print("Rust: " + str(rust_build_dir))
            shutil.rmtree(rust_build_dir)

    set_last_used_config(None)


def main():
    global cpp_directory, rust_directory
    cpp_directory = get_verified_path("cpp")
    rust_directory = get_verified_path("rust")
    update_project_config()
    prime_environment(get_compiler())

    arguments = argparse.ArgumentParser()
    arguments.add_argument("--clean", action="store_true")
    arguments.add_argument("--config", choices=["Debug", "Release"])
    specified_arguments = arguments.parse_args()

    if specified_arguments.clean:
        clean_build_artifacts()
        return

    if len(sys.argv) == 1:
        # no explicit argument - building the last successful config or fall back to both Release and Debug
        build_type = get_last_used_config()
        if build_type:
            print(blue_text("Rebuilding " + build_type))
            if cpp_directory:
                build_cpp(build_type)
            if rust_directory:
                build_rust(build_type)
            if success:
                set_last_used_config(build_type)
                return
        else:
            print("No prior successful build found - " + blue_text("building Release and Debug"))

    build_configs = [specified_arguments.config] if specified_arguments.config else ["Release", "Debug"]
    for build_type in build_configs:
        if cpp_directory:
            generate_cpp(build_type)
            build_cpp(build_type)

        if rust_directory:
            build_rust(build_type)

        if success:
            set_last_used_config(build_type)


if __name__ == "__main__":
    main()
    sys.exit(0 if success else 1)
