# Tooling

[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](LICENSE)

## Overview

**Tooling** is a set of scripts that facilitate workflow on C/C++/Rust projects.\
It's intended to be a submodule of a project.

## Prerequisites

 [![python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/downloads/release/python-3110/)
 [![just](https://img.shields.io/badge/just-1.23-green.svg)](https://github.com/casey/just) 

* Fairly modern **Python** is required but we can support Python 3.5. See the [Old Python](#old-python) section
* **Just** 1.23+ is optional but highly recommended. It's easy to install with `cargo install just`
* Shell aware of **sh** to run *just* commands. If `sh --version` fails, see [Shell without sh](#shell-without-sh) section
* C/C++ or Rust environment is already implied


## How to add

```bash
git submodule add https://github.com/Bolbot/tooling.git
git add tooling .gitmodules
git commit -m 'add tooling submodule'
python tooling/bootstrap.py
```

Initial run via python provides necessary config files. From there on, you can use simpler commands with *just*.

## How to configure

The settings are stored in `project_config.toml`:
```toml
# all paths are relative to the project root directory
# rust section can be removed for cmake-only project and vice-versa

[cmake]
path = "cpp"
# compiler can be set to: gcc, clang, msvc, clang-cl
compiler = "clang"
use_ninja = true
shared_libs = false
# targets per the first argument of add_library or add_executable
targets = [ "all" ]

[rust]
path = "rust"
features = [ "" ]

[migration]
legacy_build = false

[test]
path = "your_test_script.py"
```

It expects the following layout:
```
├── cpp
│   ├── CMakeLists.txt
│   └── hello_world.cpp, etc.
├── project_paths.toml
├── requirements.txt
├── rust
│   ├── Cargo.toml
│   └── target, etc.
├── tests
│   └── your_test_script.py
└── tooling
```

> [!NOTE]
> Make sure *path* variables are valid.\
> If you set *use_ninja*, make sure it was in `requirements.txt`.\
> The *compiler* is supposed to be installed (msvc and clang-cl are Windows-only).


## How to use

Most of the workflow is handled by *just* command runner. Commands work from any directory within your project.

> [!TIP]
> Run ```just --list``` to see the list of available commands with a short memo.

Typical scenarios involve:

`just setup` to deploy/update the virtual environment per your `requirements.txt`\
Make sure you activate your terminal per the green hint

`just vscode` or `just zed` to launch your IDE (if it's available)

`just build` to build last built config (or both Release and Debug if run afresh)

`just validate` to run your test scripts

`just release` and `just debug` to explicitly switch configs

`just clean` to remove the build artifacts

`just teardown` to remove the virtual environment, last resort if something breaks.\
Don't forget to run `deactivate` if that venv was active.

`.justfile`, `project_config.toml`, and `requirements.txt` are your project-specific files. Feel free to edit and commit them.

> [!NOTE]
> If you set `legacy_build` to true, your Rust project is expected to have (at least a dummy) `legacy-build` feature.


## Troubleshooting

Read the messages, they usually contain
* $${\color{red}errors \space printed \space in \space red}$$
* $${\color{yellow}warnings \space printed \space in \space yellow}$$
* $${\color{green}actionable \space suggestions \space printed \space in \space green}$$

### Submodule integrity

If integrity of your tooling submodule is compromised, you can always remove and restore it:
1. Delete tooling directory
2. ```git checkout @ -- tooling```

### Shell without sh

The shell you use for running just commands is expected to be sh-aware. Linux and MacOS usually have it by default.\
For Windows, you have two options:
* Add a directory with `sh.exe` to your environment PATH (`C:\Program Files\Git\bin` is provided with git installation) **(recommended)**
* Modify .justfile according to [just documentation](https://github.com/casey/just?tab=readme-ov-file#shell) if you prefer powershell or cmd

### Old Python

If your python is dated, such as [![python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/downloads/release/python-380/), you will need an extra script: `prebootstrap.py`

Run it with your python, activate the .venv-temporary environment, then proceed as usual.

> [!TIP]
> Don't forget to delete `.venv-temporary` after you activate main `.venv`

That extra run of `prebootstrap.py` is only required once, then you can activate the usual .venv as needed.

> [!WARNING]
> [![python](https://img.shields.io/badge/python-3.5-orange.svg)](https://www.python.org/downloads/release/python-350/) is the oldest supported version


## License

This project is licensed under the *BSD 3-Clause License*.

**Copyright © 2026 Bohdan Bolbot**

See the [LICENSE](LICENSE) file for the complete terms, or learn more about this license at [opensource.org](https://opensource.org/licenses/BSD-3-Clause).
