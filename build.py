#!/usr/bin/env python3

import argparse
#from random import choices
from typing import Final
from pathlib import Path
from colorama import Fore, Back, Style, init as colorama_init
import sys
import tomllib

main_project: Final = Path(__file__).parent.absolute().parent
config_file:  Final = main_project / "project_paths.toml"

def load_config():
    if not config_file.exists():
        print(f"{Fore.RED}Could not find {str(config_file)}{Style.RESET_ALL}")
        sys.exit(1)
    print(f"Found {Fore.LIGHTBLUE_EX}{str(config_file)}{Style.RESET_ALL}")
    return tomllib.loads(config_file)

def main():
    arguments = argparse.ArgumentParser()
    arguments.add_argument("--config", choices=["Debug", "Release"], default="Release")
    arguments.add_argument("--all-configs", action="store_true")
    arguments.add_argument("--clean", action="store_true")

    specified_arguments = arguments.parse_args()

    config = load_config()
    """    TODO:
            verify cmake and ninja presence
            parse config for C++ and Rust directories and targets
            check C++ directory for conanfile.py or conanfile.txt
            verify conan presence if it's required
            based on conanfile, use either conan or cmake to generate with ninja
            build C++ uniformely for conan/no-conan
            build Rust
    """



if __name__ == "__main__":
    main()
