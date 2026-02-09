# Building part

alias b := build
alias c := clean
alias d := debug
alias r := release

[doc("Builds the last used configuration. For the fresh run, builds both Debug and Release")]
build:
    python tooling/build.py || python3 tooling/build.py

[doc("Cleans the temporary build artifacts for CMake and Rust")]
clean:
    python tooling/build.py --clean || python3 tooling/build.py --clean

[doc("Builds Debug configuration for CMake and Rust")]
debug:
    python tooling/build.py --config=Debug || python3 tooling/build.py --config=Debug

[doc("Builds Release configuration for CMake and Rust")]
release:
    python tooling/build.py --config=Release || python3 tooling/build.py --config=Release


# Bootstrapping part

alias s := setup
alias t := teardown

# fresh ubuntu might miss python, but not python3, so we try both
[doc("Runs bootstrap.py script to set up all necessary tooling")]
setup:
    python tooling/bootstrap.py || python3 tooling/bootstrap.py

[doc("Removes the entire tooling; last resort for troubleshooting")]
teardown:
    rm -rf .venv .tools


# Validation part

[doc("Runs the specified testing script provided via project_config.toml")]
validate:
    python tooling/validate.py || python3 tooling/validate.py


# IDE part

alias v := vscode
alias z := zed

[doc("Launches Visual Studio Code from the project's root directory")]
vscode:
    python tooling/launchIDE.py --vscode || python3 tooling/launchIDE.py --vscode

[doc("Launches Zed from the project's root directory")]
zed:
    python tooling/launchIDE.py --zed || python3 tooling/launchIDE.py --zed
