from pathlib import Path
import sys

script_dir   = Path(__file__).parent.absolute()
main_project = script_dir.parent
tooling_path = main_project / ".tools"
venv_path    = main_project / ".venv"
venv_python  = venv_path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
requirements = main_project / "requirements.txt"
config_file  = main_project / "project_config.toml"
profiles_dir = main_project / "tooling" / "conan_profiles"
last_used    = main_project / ".tools" / "last_built_config.txt"
