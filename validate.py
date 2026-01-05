#!/usr/bin/env python3

import subprocess
import tomllib
from pathlib import Path
from typing import Final
import sys
from colorama import Fore, Style


main_project: Final = Path(__file__).parent.absolute().parent
config_file:  Final = main_project / "project_paths.toml"


def load_config():
    if not config_file.exists():
        print(f"{Fore.RED}Could not find {str(config_file)}{Style.RESET_ALL}\nRerun {Fore.GREEN}just setup{Style.RESET_ALL}")
        sys.exit(1)
    print(f"Found {Fore.LIGHTBLUE_EX}{str(config_file)}{Style.RESET_ALL}")
    return tomllib.loads(config_file.read_text())


def get_verified_path(global_config, section):
    config = global_config.get(section)
    if not config:
        print(f"No path to {section} in {config_file}. {Fore.YELLOW}Skipping {section}{Style.RESET_ALL}")
        return None
    path = Path(config.get("path", section)).resolve()
    if not path.exists():
        print(f"{Fore.RED}{section} path does not exist: {Style.RESET_ALL}{path}")
        print(f"Make sure your {config_file} specifies existing directory for {section}")
        sys.exit(1)
    return path


def main():
    config = load_config()
    test_script = get_verified_path(config, "test")
    subprocess.run(["python3", str(test_script)], check=True, cwd=main_project)


if __name__ == "__main__":
    main()
