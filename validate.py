#!/usr/bin/env python3

import subprocess
from _resource_manager import load_config, get_verified_path, get_main_project_path


def main():
    config = load_config()
    test_script = get_verified_path(config, "test")
    subprocess.run(["python3", str(test_script)], check=True, cwd=get_main_project_path())


if __name__ == "__main__":
    main()
