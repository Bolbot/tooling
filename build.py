#!/usr/bin/env python3

import argparse
#from random import choices
from typing import Final
from pathlib import Path
from colorama import Fore, Back, Style, init as colorama_init
import sys
import tomllib
import shutil
import subprocess

main_project: Final = Path(__file__).parent.absolute().parent
config_file:  Final = main_project / "project_paths.toml"

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


def build_cpp(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"C++ build directory:\t{build_dir}")

    check_presence("cmake")
    check_presence("ninja")

    toolchain_arguments = []

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        print("Conan detected but it's not yet supported...")
        #sys.exit(0)
        ## TODO: incorporate conan when basic ninja works
        ##
        #check_presence("conan")
        #subprocess.run(["conan", "install", ".", "--build=missing",
        #    "--profile", "ninja_clang",
        #    "--output-folder", str(build_dir), "--settings", f"build_type={build_type}"],
        #    cwd=cpp_directory, check=True)
        #toolchain = build_dir / "build" / "generators" / "conan_toolchain.cmake"
        #print(f"Toolchain directory:\t{str(toolchain.parent)}")
        #toolchain_arguments.append(f"-DCMAKE_TOOLCHAIN_FILE={toolchain}")

    #subprocess.run(["cmake", "-S", ".", "-B", str(build_dir), "-G", "Ninja", f"-DCMAKE_BUILD_TYPE={build_type}", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", *toolchain_arguments], cwd=cpp_directory, check=True)

    #targets = cpp_config.get("targets", ["all"])
    #print(f"Targets: {targets}")


def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--config", choices=["Debug", "Release"], default="Release")
    arguments.add_argument("--all-configs", action="store_true")
    arguments.add_argument("--clean", action="store_true")

    specified_arguments = arguments.parse_args()

    config = load_config()

    cpp_config = config.get("cpp")
    cpp_directory = Path(cpp_config.get("path", "cpp")).resolve() if cpp_config else None

    if cpp_config:
        build_configs = ["Debug", "Release"] if specified_arguments.all_configs else [specified_arguments.config]
        for requested_config in build_configs:
            build_cpp(cpp_directory, requested_config)

    """    TODO:
            parse config for C++ and Rust targets
            check C++ directory for conanfile.py or conanfile.txt
            verify conan presence if it's required
            based on conanfile, use either conan or cmake to generate with ninja
            build C++ uniformely for conan/no-conan
            build Rust
    """

    rust_config = config.get("rust")
    rust_directory = Path(rust_config.get("path", "rust")).resolve() if rust_config else None
    print(f"Rust directory: {rust_directory}")

    if specified_arguments.clean:
        print(f"Going to delete the following paths:")
        if cpp_directory:
            cpp_build_dir = cpp_directory / "build"
            if cpp_build_dir.exists():
                print(f"C++:  {cpp_build_dir}")
                shutil.rmtree(cpp_build_dir)
            # TODO: add temp conan presets
        if rust_directory:
            rust_build_dir = rust_directory / "target"
            if rust_build_dir.exists():
                print(f"Rust: {rust_build_dir}")
                shutil.rmtree(rust_build_dir)


if __name__ == "__main__":
    main()
