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
    source_images = ROOT / "images"
    output_images = ROOT / "dist" / "images"
    if not source_images.is_dir():
        print(
            f"Image folder not found: {source_images}. "
            "The executable needs an images folder next to it.",
            file=sys.stderr,
        )
        return 1
    copytree(source_images, output_images, dirs_exist_ok=True)
    print(f"Created: {executable}")
    print(f"Images copied to: {output_images}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
