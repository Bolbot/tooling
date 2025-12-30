# Preliminary setting
set windows-shell := ["cmd.exe", "/C"]

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



# Building part

[doc("Runs build.py --config=Debug to build the Debug configuration for C++ and Rust")]
debug:
    python tooling/build.py --config=Debug || python3 tooling/build.py --config=Debug

[doc("Runs build.py --config=Release to build the Release configuration for C++ and Rust")]
release:
    python tooling/build.py --config=Release || python3 tooling/build.py --config=Release

[doc("Runs build.py --all-configs to build both Debug and Release configurations for C++ and Rust")]
both:
    python tooling/build.py --all-configs || python3 tooling/build.py --all-configs

[doc("Rebuilds the configuration that was built last (Debug or Release)")]
rebuild:
    echo "Work In Progress"

[doc("Runs build.py --clean to clean the temporary build artifacts C++ and Rust")]
clean:
    python tooling/build.py --clean || python3 tooling/build.py --clean
