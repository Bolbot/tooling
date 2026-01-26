from pathlib import Path
from typing import Final
import shutil
import sys
import tomllib
from _platform_specific import python_in_venv, get_profile_path, windows_proof_cmake_preset, try_build, print_compiler_warning
from _text_colors import RED, YELLOW, GREEN, BLUE, RESET


main_project: Final = Path(__file__).parent.absolute().parent
venv_path   : Final = main_project / ".venv"
venv_python : Final = venv_path / python_in_venv()
requirements: Final = main_project / "requirements.txt"
config_file:  Final = main_project / "project_config.toml"
profiles_dir: Final = main_project / "tooling" / "conan_profiles"
last_used:    Final = main_project / ".tools" / "last_built_config.txt"


config_contents = None
compiler = ""
use_ninja = False


def get_main_project_path():
    return main_project


def get_venv_python_path():
    return venv_python


def get_requirements_path():
    return requirements


def get_compiler():
    return compiler


def get_conan_profile():
    profile_name = compiler + ("_ninja" if use_ninja else "_default")
    profile_path = get_profile_path(profiles_dir, profile_name)

    if profile_path.resolve().exists():
        print(f"Conan profile:\t\t{profile_path}")
        return str(profile_path.resolve())
    else:
        print(f"{RED}Conan profile does not exist: {RESET}{profile_path}")
        print(f"Make sure {config_file} contains valid compiler value in cpp section")
        sys.exit(1)


def resolve_resource(file_name, additional_text=""):
    expected = main_project / file_name
    fallback = Path(__file__).resolve().parent / file_name

    if not expected.exists():
        print(f"{YELLOW}Haven't found {file_name}{RESET} in {main_project}")
        print(f"Adding a fallback {file_name}: {additional_text}")
        print(f"Don't forget to add it to your VCS: {GREEN}git add {file_name}{RESET}")
        shutil.copyfile(str(fallback), str(expected))


def check_presence(tool, required=True):
    if shutil.which(tool) is None and required:
        print(f"{RED}Failed to find {tool}. Can not proceed{RESET}")
        print(f"Make sure to run {GREEN}just setup{RESET} and properly activate your shell")
        sys.exit(1)
    return shutil.which(tool) is not None


def get_verified_path(section):
    config = load_config(section)
    if not config:
        return None

    path = Path(config.get("path", ".")).resolve()
    if not path.exists():
        print(f"{RED}Not found: {RESET}{path}")
        print(f"Make sure your {YELLOW}{config_file.name}{RESET} specifies proper relative paths")
        sys.exit(1)

    if section == "cpp" and not (path / "CMakeLists.txt").exists():
        print(f"{RED}No CMakeLists.txt{RESET} in {path}\nCheck the path in {section} section of your {config_file.name}")
        sys.exit(1)
    if section == "rust" and not (path / "Cargo.toml").exists():
        print(f"{RED}No Cargo.toml{RESET} in {path}\nCheck the path in {section} section of your {config_file.name}")
        sys.exit(1)

    return path


def load_config(section):
    global config_contents
    if not config_contents:
        if not config_file.exists():
            print(f"{RED}Could not find {str(config_file)}{RESET}\nRerun {GREEN}just setup{RESET}")
            sys.exit(1)
        print(f"Reading configuration from {BLUE}{str(config_file.parent.name)}/{str(config_file.name)}{RESET}")
        config_contents = tomllib.loads(config_file.read_text())

    section_config = config_contents.get(section)
    if not section_config:
        print(f"{YELLOW}Skipping {section}{RESET}, because it was missing in {config_file.name}")
        return None
    return section_config


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


def get_generate_command(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"C++ build directory:\t{build_dir}")

    result = []

    c_compiler = compiler if compiler != "msvc" else "cl"
    cpp_compiler = compiler
    match compiler:
        case "gcc": cpp_compiler = "g++"
        case "clang": cpp_compiler = "clang++"
        case _: cpp_compiler = c_compiler

    check_presence(c_compiler)
    check_presence(cpp_compiler)
    if use_ninja:
        check_presence("ninja")

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        check_presence("conan")
        conan_profile = get_conan_profile()
        result += ["conan", "install", ".", "--build=missing", "--profile", conan_profile, "--settings", f"build_type={build_type}"]
    else:
        result += ["cmake", "-S", ".", "-B", str(build_dir), f"-DCMAKE_BUILD_TYPE={build_type}", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
        if use_ninja:
            result += ["-G", "Ninja"]
        else:
            if compiler == "clang-cl":
                result += ["-T", "ClangCL"]
        result += [f"-DCMAKE_C_COMPILER={c_compiler}", f"-DCMAKE_CXX_COMPILER={cpp_compiler}"]
        print_compiler_warning(compiler, not use_ninja)

    return result


def update_cpp_config():
    config = load_config("cpp")
    global compiler, use_ninja
    compiler = config.get("compiler", "")
    if not compiler:
        print(f"{YELLOW}compiler value was missing from {config_file.name}{RESET}")
        print("Trying to use clang as a fallback")
        compiler = "clang"
    use_ninja = config.get("use_ninja", False)


def get_cmake_preset_name(build_type):
    return windows_proof_cmake_preset(build_type, use_ninja)


def build_and_verify(build_command, cpp_directory):
    max_attempts = 7 if use_ninja else 1
    if try_build(build_command, cpp_directory, max_attempts):
        print(f"{GREEN}Successful C++ build{RESET} with {" ".join(build_command)}\n")
        return True
    else:
        print(f"{RED}Failed to build C++{RESET} with {" ".join(build_command)}\n")
        return False
