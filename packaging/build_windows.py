"""Run on Windows: uv run python packaging/build_windows.py."""

import subprocess
from pathlib import Path


def main() -> None:
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
            "--add-data",
            "src/xaydungso/presentation/logo.svg:xaydungso/presentation",
            "--icon",
            str(root / "packaging" / "xaydungso.ico"),
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
