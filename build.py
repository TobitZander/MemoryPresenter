"""Build the native Memory Presenter executable for the current operating system."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import copytree


ROOT = Path(__file__).resolve().parent
NAME = "MemoryPresenter"


def main() -> int:
    if sys.platform.startswith("win"):
        data_separator = ";"
        output_name = f"{NAME}.exe"
    elif sys.platform.startswith("linux"):
        data_separator = ":"
        output_name = NAME
    else:
        print(f"Nicht unterstütztes Betriebssystem: {sys.platform}", file=sys.stderr)
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        NAME,
        "--add-data",
        f"templates{data_separator}templates",
        "--add-data",
        f"static{data_separator}static",
        "--hidden-import",
        "engineio.async_drivers.threading",
        "--collect-submodules",
        "pystray",
        "app.py",
    ]
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as error:
        print(f"Build fehlgeschlagen (Exit-Code {error.returncode}).", file=sys.stderr)
        return error.returncode
    except ModuleNotFoundError:
        print(
            "PyInstaller fehlt. Installiere es mit "
            f"'{sys.executable} -m pip install pyinstaller'.",
            file=sys.stderr,
        )
        return 1

    executable = ROOT / "dist" / output_name
    source_resources = ROOT / "resources"
    output_resources = ROOT / "dist" / "resources"
    if not source_resources.is_dir():
        print(
            f"Resource folder not found: {source_resources}. "
            "The executable needs a resources folder next to it.",
            file=sys.stderr,
        )
        return 1
    copytree(source_resources, output_resources, dirs_exist_ok=True)
    print(f"Created: {executable}")
    print(f"Resources copied to: {output_resources}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
