from pathlib import Path
import shutil
import sys
import tomllib
import subprocess
from _platform_specific import get_profile_path, windows_proof_cmake_preset, windows_proof_cargo_target
from _platform_specific import try_build, print_compiler_warning
from _text_colors import blue_text, green_text, red_text, yellow_text
from _paths import script_dir, profiles_dir, main_project, config_file, last_used


config_contents = None

# C/C++
compiler = ""
use_ninja = False
shared_libs = False

# Rust
targets = None
features = None

# Interop
legacy_build = False


def get_compiler():
    return compiler


def get_conan_profile():
    profile_name = compiler + ("_ninja" if use_ninja else "_default")
    profile_path = get_profile_path(profiles_dir, profile_name)

    if profile_path.resolve().exists():
        print(f"Conan profile:\t\t{profile_path}")
        return str(profile_path.resolve())
    else:
        print(red_text("Conan profile does not exist: ") + str(profile_path))
        print("Make sure {} contains valid compiler value in cpp section".format(str(config_file)))
        sys.exit(1)


def resolve_resource(file_name, additional_text=""):
    expected = main_project / file_name
    fallback = script_dir / file_name

    if not expected.exists():
        print(yellow_text("Haven't found {}".format(file_name)) + " in " + str(main_project))
        print("Adding a fallback {}: {}".format(file_name, additional_text))
        print("Don't forget to add it to your VCS: " + green_text("git add {}".format(str(file_name))))
        shutil.copyfile(str(fallback), str(expected))


def check_presence(tool, required=True):
    if shutil.which(tool) is None and required:
        print(red_text("Failed to find {}. Can not proceed".format(tool)))
        print("Make sure to run " + green_text("just setup") + " and properly activate your shell")
        sys.exit(1)
    return shutil.which(tool) is not None


def get_verified_path(section):
    config = load_config(section)
    if not config:
        return None

    path = Path(config.get("path", ".")).resolve()
    if not path.exists():
        print(red_text("Not found: ") + str(path))
        print("Make sure your " + yellow_text(config_file.name) + " specifies proper relative paths")
        sys.exit(1)

    if section == "cpp" and not (path / "CMakeLists.txt").exists():
        print(red_text("No CMakeLists.txt") + " in " + str(path))
        print("Check the path in {} section of your {}".format(section, config_file.name))
        sys.exit(1)
    if section == "rust" and not (path / "Cargo.toml").exists():
        print(red_text("No Cargo.toml") + " in " + str(path))
        print("Check the path in {} section of your {}".format(section, config_file.name))
        sys.exit(1)

    return path


def load_config(section, warn=False):
    global config_contents
    if not config_contents:
        if not config_file.exists():
            print(red_text("Could not find {}".format(str(config_file))) + "\nRerun " + green_text("just setup"))
            sys.exit(1)
        print("Reading configuration from " + blue_text(str(config_file.parent.name) + '/' + str(config_file.name)))
        config_contents = tomllib.loads(config_file.read_text())

    section_config = config_contents.get(section)
    if not section_config and warn:
        print(yellow_text("Skipping {}".format(section)) + " because it was missing in " + config_file.name)

    return section_config


def get_last_used_config():
    if not last_used.exists():
        return None
    config = last_used.read_text()
    if config != "Debug" and config != "Release":
        print(red_text("Broken {}".format(str(config))) + "\nRemoving it and building from scratch")
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
        result += ["cmake", f"-DCMAKE_BUILD_TYPE:STRING={build_type}", "-DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=TRUE",
            "--no-warn-unused-cli", "-S", ".", "-B", str(build_dir)]
        if use_ninja:
            result += ["-G", "Ninja"]
        else:
            if compiler == "clang-cl":
                result += ["-T", "ClangCL"]

        if legacy_build:
            result += ["-DLEGACY_BUILD=ON"]

        if shared_libs:
            result += ["-DBUILD_SHARED_LIBS=ON"]
        result += [f"-DCMAKE_C_COMPILER={c_compiler}", f"-DCMAKE_CXX_COMPILER={cpp_compiler}"]
        print_compiler_warning(compiler, not use_ninja)

    return result


def get_build_command(cpp_directory, build_type):
    build_dir = cpp_directory / "build" / build_type
    print(f"Building {build_type} C++ in {build_dir}")

    build_command = ["cmake", "--build"]

    conanfile = get_conanfile(cpp_directory)
    if conanfile:
        cmake_preset = get_cmake_preset_name(build_type)
        subprocess.run(["cmake", "--preset", cmake_preset], cwd=str(cpp_directory), check=True)
        build_command += ["--preset", "conan-debug" if build_type == "Debug" else "conan-release"]
    else:
        build_command += [str(build_dir), "--config", build_type]

    if targets:
        build_command.append("--target")
        build_command += targets

    return build_command


def update_project_config():
    global compiler, use_ninja, shared_libs, targets, features, legacy_build
    migration_config = load_config("migration")
    if not migration_config:
        print(yellow_text("No [migration] section in project_config.toml") +
            "\n(Optional) Delete project_config.toml and rerun " + green_text("just setup") + " for the updated fallback")
    else:
        legacy_build = migration_config.get("legacy_build", False)

    cpp_config = load_config("cpp", True)
    if cpp_config:
        compiler = cpp_config.get("compiler", "")
        if not compiler:
            print(yellow_text("compiler value was missing from {}".format(config_file.name)))
            print("Trying to use clang as a fallback")
            compiler = "clang"
        use_ninja   = cpp_config.get("use_ninja", False)
        shared_libs = cpp_config.get("shared_libs", False)
        targets     = cpp_config.get("targets", ["all"])

    rust_config = load_config("rust", True)
    if rust_config:
        features = rust_config.get("features")
        if legacy_build:
            features.append("legacy_build")


def get_cmake_preset_name(build_type):
    return windows_proof_cmake_preset(build_type, use_ninja)


def build_and_verify(build_command, cpp_directory):
    max_attempts = 7 if use_ninja else 1
    if try_build(build_command, cpp_directory, max_attempts):
        print(green_text("Successful C++ build") + " with {}".format(' '.join(build_command)) + '\n')
        return True
    else:
        print(red_text("Failed to build C++") + " with {}".format(' '.join(build_command)) + '\n')
        return False


def get_cargo_target(rust_directory):
    target = windows_proof_cargo_target(rust_directory, compiler, use_ninja)
    if target:
        relative_path = Path(rust_directory.resolve() / "target" / target).relative_to(main_project.resolve())
        print("Using a non-default target for building rust. See the build in " + blue_text(str(relative_path)))
    return target


def get_cargo_features(rust_directory):
    return features
