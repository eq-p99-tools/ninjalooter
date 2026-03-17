"""Build a custom PyInstaller bootloader from source.

The stock PyInstaller bootloader binary is identical across all installations,
so AV vendors flag its signature (it matches known malware samples that also
used PyInstaller). Compiling from source produces a unique binary.

Requirements: a C compiler (MSVC via Visual Studio Build Tools on Windows).
"""
import os
import subprocess
import sys
import shutil
import tempfile

PYINSTALLER_REPO = "https://github.com/pyinstaller/pyinstaller.git"
MARKER_PREFIX = ".custom_bootloader_"


def get_pyinstaller_version():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "pyinstaller"],
        capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("PyInstaller is not installed")


def _bootloader_dir():
    import PyInstaller
    return os.path.join(os.path.dirname(PyInstaller.__file__), "bootloader")


def _marker_path(version):
    return os.path.join(_bootloader_dir(), f"{MARKER_PREFIX}{version}")


def is_custom_bootloader(version):
    return os.path.isfile(_marker_path(version))


def build_bootloader(force=False):
    version = get_pyinstaller_version()

    if not force and is_custom_bootloader(version):
        print(f"Custom bootloader for PyInstaller {version} already installed, skipping build. "
              f"Use --force to rebuild.")
        return

    tag = f"v{version}"
    print(f"Building custom bootloader for PyInstaller {version} ({tag})")

    work_dir = tempfile.mkdtemp(prefix="pyinstaller_bootloader_")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", tag,
             PYINSTALLER_REPO, work_dir],
            check=True)

        bootloader_src_dir = os.path.join(work_dir, "bootloader")
        subprocess.run(
            [sys.executable, "./waf", "all"],
            cwd=bootloader_src_dir, check=True)

        src = os.path.join(work_dir, "PyInstaller", "bootloader")
        dst = _bootloader_dir()

        print(f"Copying custom bootloader to {dst}")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

        with open(_marker_path(version), "w") as f:
            f.write(version)

        print("Custom bootloader installed successfully.")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    force = "--force" in sys.argv
    build_bootloader(force=force)
