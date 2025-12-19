# Preliminary setting
set windows-shell := ["cmd.exe", "/C"]

# Bootstrapping part

alias s := setup
alias t := teardown

# fresh ubuntu might miss python, but not python3, so we try both
[doc("Runs bootstrap.py script to set up all necessary tooling")]
setup:
    python bootstrap.py || python3 bootstrap.py

[doc("Removes the entire tooling; last resort for troubleshooting")]
teardown:
    rm -rf .venv .tools
