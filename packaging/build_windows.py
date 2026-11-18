"""Run on Windows: uv run python packaging/build_windows.py."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit(
            "Windows packaging must run on Windows; cross-build is unsupported"
        )
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        ["uv", "sync", "--locked", "--group", "packaging"], cwd=root, check=True
    )
    subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "--group",
            "packaging",
            "pyinstaller",
            "--onedir",
            "--windowed",
            "--noupx",
            "--name",
            "XayDungSo",
            "--paths",
            "src",
            "--collect-data",
            "qfluentwidgets",
            "--collect-data",
            "qframelesswindow",
            "--collect-data",
            "tzdata",
            "--hidden-import",
            "xaydungso.worker",
            "--add-data",
            "docs/modules/excel/templates/so_theo_doi.xlsx:templates",
            "--add-data",
            "src/xaydungso/presentation/icons:xaydungso/presentation/icons",
            "--specpath",
            "build",
            "--distpath",
            "dist",
            "--workpath",
            "build/pyinstaller",
            "src/xaydungso/__main__.py",
        ],
        cwd=root,
        check=True,
    )


if __name__ == "__main__":
    main()
