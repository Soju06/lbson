import os
import subprocess
import sys
from os import PathLike
from pathlib import Path

ENVIRONMENTS = {
    "lbson": {
        "name": "lbson_env",
        "packages": ["pyperf", "orjson"],
        "local_package": True,
    },
    "pymongo": {
        "name": "pymongo_env",
        "packages": ["pyperf", "orjson", "pymongo>=4.13,<5.0"],
        "local_package": False,
    },
    "bson": {
        "name": "bson_env",
        "packages": ["pyperf", "orjson", "bson>=0.5,<0.6"],
        "local_package": False,
    },
}

ENVIRONMENT_PATH = Path(__file__).parent / "environments"


def _run_command(cmd: list[str], cwd: PathLike | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    return result


def _create_virtualenv(env_name: str) -> None:
    print(f"Creating virtual environment {env_name}...")
    _run_command([sys.executable, "-m", "venv", str(ENVIRONMENT_PATH / env_name)])


def get_python_executable(env_name: str) -> Path:
    env_path = ENVIRONMENT_PATH / env_name

    if not env_path.exists():
        raise FileNotFoundError(f"Virtual environment {env_name} not found")

    if os.name == "nt":
        python = env_path / "Scripts" / "python.exe"
    else:
        python = env_path / "bin" / "python"

    if not python.exists():
        raise FileNotFoundError(f"Python executable not found in {python}")

    return python


def _install_packages(env_name: str, packages: list[str]) -> None:
    python = get_python_executable(env_name)
    _run_command([str(python), "-m", "pip", "install", "--upgrade", "pip"])

    for package in packages:
        print(f"Installing {package}...")
        _run_command([str(python), "-m", "pip", "install", package])


def _install_local_lbson(env_name: str) -> None:
    python = get_python_executable(env_name)
    project_root = Path(__file__).parent.parent

    if not (project_root / "pyproject.toml").exists():
        raise FileNotFoundError("pyproject.toml not found in project root")

    _run_command([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    _run_command([str(python), "-m", "pip", "install", "-e", str(project_root)], cwd=project_root)


def setup_environment(env_name: str) -> None:
    if (config := ENVIRONMENTS[env_name]) is None:
        raise ValueError(f"Invalid environment name: {env_name}")

    env_path = ENVIRONMENT_PATH / env_name
    env_path.mkdir(parents=True, exist_ok=True)

    _create_virtualenv(env_name)

    if packages := config["packages"]:
        _install_packages(env_name, packages)

    if config["local_package"]:
        _install_local_lbson(env_name)

    if config["local_package"]:
        _install_local_lbson(env_name)

    print(f"'{env_name}' environment setup complete!")
