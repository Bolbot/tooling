# Bootstrapping part

alias s := setup
alias t := teardown

[doc("Runs bootstrap.py script to set up all necessary tooling")]
setup:
    python3 bootstrap.py

[doc("Removes the entire tooling; last resort for troubleshooting")]
teardown:
    rm -rf .venv .tools
