from pathlib import Path
from typing import Final
import shutil
import sys
import tomllib
from _platform_specific import python_in_venv
from _text_colors import RED, YELLOW, GREEN, BLUE, RESET

main_project: Final = Path(__file__).parent.absolute().parent
venv_path   : Final = main_project / ".venv"
venv_python : Final = venv_path / python_in_venv()
requirements: Final = main_project / "requirements.txt"
config_file:  Final = main_project / "project_paths.toml"
profiles_dir: Final = main_project / "tooling" / "conan_profiles"
last_used:    Final = main_project / ".tools" / "last_built_config.txt"

def get_main_project_path():
    return main_project


def get_venv_python_path():
    return venv_python


def get_requirements_path():
    return requirements


def get_profile_directory():
    return profiles_dir


def resolve_resource(file_name, additional_text=""):
    expected = main_project / file_name
    fallback = Path(__file__).resolve().parent / file_name

    if not expected.exists():
        print(f"{YELLOW}Haven't found {file_name}{RESET} in {main_project}. Adding a fallback {file_name}")
        print(f"Don't forget to add it to your VCS: {GREEN}git add {file_name}{RESET}")
        print(additional_text)
        shutil.copyfile(str(fallback), str(expected))


def check_presence(tool, required=True):
    if shutil.which(tool) is None and required:
        print(f"{RED}Failed to find {tool}. Can not proceed{RESET}")
        print(f"Make sure to run {GREEN}just setup{RESET} and properly activate your shell")
        sys.exit(1)
    return shutil.which(tool) is not None


def get_verified_path(global_config, section):
    config = global_config.get(section)
    if not config:
        print(f"{YELLOW}Skipping {section}{RESET}, because it was missing in {config_file}")
        return None
    path = Path(config.get("path", section)).resolve()
    if not path.exists():
        print(f"{RED}{section} path does not exist: {RESET}{path}")
        print(f"Make sure your {config_file} specifies existing directory for {section}")
        sys.exit(1)
    return path


def load_config():
    if not config_file.exists():
        print(f"{RED}Could not find {str(config_file)}{RESET}\nRerun {GREEN}just setup{RESET}")
        sys.exit(1)
    print(f"Reading paths from {BLUE}{str(config_file)}{RESET}")
    return tomllib.loads(config_file.read_text())


def get_last_used_config():
    if not last_used.exists():
        return None
    config = last_used.read_text()
    if config != "Debug" and config != "Release":
        print(f"{RED}Broken {str(config)}{RESET}\nRemoving it and building from scratch")
        last_used.unlink()
        return None
    return config


def set_last_used_config(build_type):
    if build_type is not None:
        last_used.write_text(build_type)
    elif last_used.exists():
        print("Wiping the last used build configuration")
        last_used.unlink()


def get_conanfile(cpp_directory):
    result = cpp_directory / "conanfile.txt"
    if result.exists():
        return result
    result = cpp_directory / "conanfile.py"
    return result if result.exists() else None
