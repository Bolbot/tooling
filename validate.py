#!/usr/bin/env python3

import subprocess
from _resource_manager import get_verified_path, get_main_project_path


def main():
    test_script = get_verified_path("test")
    subprocess.run(["python3", str(test_script)], check=True, cwd=get_main_project_path())


if __name__ == "__main__":
    main()
