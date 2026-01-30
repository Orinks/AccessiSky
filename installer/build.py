#!/usr/bin/env python3
"""
Build script for AccessiSky using PyInstaller.

This script handles the complete build process:
- Builds the application with PyInstaller
- Creates portable ZIP archives

Usage:
    python installer/build.py                    # Full build for current platform
    python installer/build.py --skip-zip         # Build but skip ZIP creation
    python installer/build.py --clean            # Clean build artifacts
    python installer/build.py --dev              # Run app in development mode
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
INSTALLER_DIR = ROOT / "installer"
SRC_DIR = ROOT / "src"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"
RESOURCES_DIR = SRC_DIR / "accessisky" / "resources"

# Platform detection
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command and handle errors."""
    print(f"$ {' '.join(cmd)}")
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=check,
            capture_output=capture,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        raise


def get_version() -> str:
    """Read version from pyproject.toml."""
    pyproject = ROOT / "pyproject.toml"
    try:
        import tomllib

        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
        return data.get("project", {}).get("version", "0.0.0")
    except Exception:
        # Fallback: parse manually
        text = pyproject.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.strip().startswith("version") and '"' in line:
                return line.split('"')[1]
        return "0.0.0"


def install_dependencies() -> None:
    """Ensure build dependencies are installed."""
    print("Checking build dependencies...")

    # Check for PyInstaller
    try:
        import PyInstaller

        print(f"[OK] PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("Installing PyInstaller...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_pyinstaller() -> bool:
    """Build the application with PyInstaller."""
    print("\n" + "=" * 60)
    print("Building with PyInstaller...")
    print("=" * 60 + "\n")

    spec_file = INSTALLER_DIR / "accessisky.spec"

    if not spec_file.exists():
        print(f"Error: Spec file not found: {spec_file}")
        return False

    # Clean previous build
    for dir_path in [BUILD_DIR, DIST_DIR]:
        if dir_path.exists():
            print(f"Cleaning {dir_path}...")
            shutil.rmtree(dir_path, ignore_errors=True)

    # Run PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    try:
        run_command(cmd, cwd=ROOT)
        print("\n[OK] PyInstaller build completed")
        return True
    except Exception as e:
        print(f"\n[FAIL] PyInstaller build failed: {e}")
        return False


def create_macos_dmg() -> bool:
    """Create macOS DMG installer."""
    print("\n" + "=" * 60)
    print("Creating macOS DMG...")
    print("=" * 60 + "\n")

    app_path = DIST_DIR / "AccessiSky.app"
    if not app_path.exists():
        print(f"Error: App bundle not found: {app_path}")
        return False

    version = get_version()
    dmg_name = f"AccessiSky_v{version}.dmg"
    dmg_path = DIST_DIR / dmg_name

    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()

    # Try create-dmg first (better looking DMGs)
    if shutil.which("create-dmg"):
        try:
            icon_path = RESOURCES_DIR / "app.icns"
            cmd = [
                "create-dmg",
                "--volname",
                "AccessiSky",
                "--window-pos",
                "200",
                "120",
                "--window-size",
                "600",
                "400",
                "--icon-size",
                "100",
                "--icon",
                "AccessiSky.app",
                "175",
                "190",
                "--hide-extension",
                "AccessiSky.app",
                "--app-drop-link",
                "425",
                "190",
            ]
            if icon_path.exists():
                cmd.extend(["--volicon", str(icon_path)])
            cmd.extend([str(dmg_path), str(DIST_DIR)])

            run_command(cmd, cwd=ROOT)
            print(f"\n[OK] DMG created: {dmg_path}")
            return True
        except Exception as e:
            print(f"create-dmg failed: {e}, falling back to hdiutil")

    # Fallback to hdiutil
    try:
        # Create a temporary directory for the DMG contents
        dmg_temp = DIST_DIR / "dmg_temp"
        if dmg_temp.exists():
            shutil.rmtree(dmg_temp)
        dmg_temp.mkdir()

        # Copy app to temp directory
        shutil.copytree(app_path, dmg_temp / "AccessiSky.app")

        # Create Applications symlink
        (dmg_temp / "Applications").symlink_to("/Applications")

        # Create DMG with hdiutil
        run_command(
            [
                "hdiutil",
                "create",
                "-volname",
                "AccessiSky",
                "-srcfolder",
                str(dmg_temp),
                "-ov",
                "-format",
                "UDZO",
                str(dmg_path),
            ]
        )

        # Cleanup
        shutil.rmtree(dmg_temp)

        print(f"\n[OK] DMG created: {dmg_path}")
        return True
    except Exception as e:
        print(f"\n[FAIL] DMG creation failed: {e}")
        return False


def create_portable_zip() -> bool:
    """Create a portable ZIP archive."""
    print("\n" + "=" * 60)
    print("Creating portable ZIP...")
    print("=" * 60 + "\n")

    version = get_version()

    if IS_WINDOWS:
        # Look for directory distribution first, then single exe
        source_dir = DIST_DIR / "AccessiSky_dir"
        if not source_dir.exists():
            # Single exe - create a directory for it
            exe_path = DIST_DIR / "AccessiSky.exe"
            if exe_path.exists():
                source_dir = DIST_DIR / "AccessiSky_portable"
                source_dir.mkdir(exist_ok=True)
                shutil.copy2(exe_path, source_dir / "AccessiSky.exe")
            else:
                print("Error: No build output found")
                return False

        zip_name = f"AccessiSky_Portable_v{version}_Windows"
    elif IS_MACOS:
        source_dir = DIST_DIR / "AccessiSky.app"
        if not source_dir.exists():
            print("Error: App bundle not found")
            return False
        zip_name = f"AccessiSky_v{version}_macOS"
    else:
        source_dir = DIST_DIR / "AccessiSky"
        if not source_dir.exists():
            print("Error: Build output not found")
            return False
        zip_name = f"AccessiSky_v{version}_Linux"

    zip_path = DIST_DIR / zip_name

    # Remove existing zip
    if Path(f"{zip_path}.zip").exists():
        Path(f"{zip_path}.zip").unlink()

    # Create zip
    shutil.make_archive(str(zip_path), "zip", source_dir.parent, source_dir.name)

    print(f"\n[OK] Portable ZIP created: {zip_path}.zip")
    return True


def clean_build() -> None:
    """Clean all build artifacts."""
    print("Cleaning build artifacts...")

    dirs_to_clean = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"  Removing {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)

    # Clean PyInstaller cache
    pycache_dirs = list(ROOT.rglob("__pycache__"))
    for pycache in pycache_dirs:
        if "site-packages" not in str(pycache):
            shutil.rmtree(pycache, ignore_errors=True)

    # Clean .pyc files
    for pyc in ROOT.rglob("*.pyc"):
        if "site-packages" not in str(pyc):
            pyc.unlink(missing_ok=True)

    print("[OK] Clean complete")


def run_dev() -> int:
    """Run the application in development mode."""
    print("Running in development mode...")
    return run_command(
        [sys.executable, "-m", "accessisky"],
        cwd=ROOT,
        check=False,
    ).returncode


def main() -> int:
    """Run the build process."""
    parser = argparse.ArgumentParser(
        description="Build AccessiSky application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-zip",
        action="store_true",
        help="Skip portable ZIP creation",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode",
    )
    parser.add_argument(
        "--dmg",
        action="store_true",
        help="Create DMG on macOS (in addition to ZIP)",
    )

    args = parser.parse_args()

    # Print banner
    print("\n" + "=" * 60)
    print("AccessiSky Build Script")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Version: {get_version()}")
    print("=" * 60 + "\n")

    # Handle special commands
    if args.clean:
        clean_build()
        return 0

    if args.dev:
        return run_dev()

    # Install dependencies
    install_dependencies()

    # Build with PyInstaller
    if not build_pyinstaller():
        return 1

    # Create DMG on macOS if requested
    if IS_MACOS and args.dmg:
        create_macos_dmg()

    # Create portable ZIP
    if not args.skip_zip:
        create_portable_zip()

    # Print summary
    print("\n" + "=" * 60)
    print("Build Summary")
    print("=" * 60)

    if DIST_DIR.exists():
        print("\nCreated files:")
        for f in sorted(DIST_DIR.iterdir()):
            if f.is_file():
                size_mb = f.stat().st_size / (1024 * 1024)
                print(f"  {f.name} ({size_mb:.1f} MB)")

    print("\n[OK] Build complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
