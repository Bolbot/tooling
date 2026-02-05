# Tooling

**Tooling** is a set of scripts that facilitate workflow on C/C++/Rust projects.\
It's intended to be a submodule of a project.

## Prerequisites

* **Python 3.11**¹ is required
* **just** 1.23+ is optional but highly recommended²
* C/C++ or Rust environment is already implied

1. Can support Python 3.5, see the Old Python section
2. Easy to install with `cargo install just`

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

[cpp]
path = "cpp"
# compiler can be set to: gcc, clang, msvc, clang-cl
compiler = "clang"
use_ninja = true

[rust]
path = "rust"

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


## Troubleshooting

Read the messages, they usually contain
* $${\color{red}errors \space printed \space in \space red}$$
* $${\color{yellow}warnings \space printed \space in \space yellow}$$
* $${\color{green}actionable \space suggestions \space printed \space in \space green}$$

If integrity of your tooling submodule is compromised, you can always remove and restore it:
```bash
rm -rf tooling
git checkout @ -- tooling
```

The shell you use for running just commands is expected to be sh-aware. If it isn't, you have two options:
* Add a directory with sh to your environment PATH (for instance, `C:\Program Files\Git\bin` comes with git)
* Modify .justfile according to [just documentation](https://github.com/casey/just?tab=readme-ov-file#shell)

## Old Python

If your python is dated, such as 3.8, you will need an extra script: `prebootstrap.py`

Run it with your python, activate the .venv-temporary environment, then proceed as usual.

> [!TIP]
> Don't forget to delete `.venv-temporary` after you activate main `.venv`

That extra run of `prebootstrap.py` is only required once, then you can activate the usual .venv as needed.

> [!WARNING]
> Python 3.5 is the oldest supported version
