#!/usr/bin/env python3

import subprocess
from _paths import main_project
from _resource_manager import get_verified_path


def main():
    test_script = get_verified_path("test")
    subprocess.run(["python3", str(test_script)], check=True, cwd=str(main_project))


if __name__ == "__main__":
    main()
