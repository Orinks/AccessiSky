"""
PyInstaller spec file for AccessiSky.

This spec file configures PyInstaller to build AccessiSky as a standalone
application for Windows and macOS.

Usage:
    pyinstaller installer/accessisky.spec
"""

import platform
import sys
from pathlib import Path

# Ensure installer/ directory is on Python path so spec_utils can be imported
sys.path.insert(0, SPECPATH)
from spec_utils import filter_platform_binaries, filter_sound_lib_entries

# Determine paths
SPEC_DIR = Path(SPECPATH).resolve()
PROJECT_ROOT = SPEC_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
RESOURCES_DIR = SRC_DIR / "accessisky" / "resources"

# Platform-specific settings
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"

# App metadata
APP_NAME = "AccessiSky"
APP_VERSION = "0.1.0"
APP_BUNDLE_ID = "net.orinks.accessisky"

# Read version from pyproject.toml if available
try:
    import tomllib
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
        APP_VERSION = pyproject.get("project", {}).get("version", APP_VERSION)
except Exception:
    pass

# Determine icon path
if IS_WINDOWS:
    ICON_PATH = RESOURCES_DIR / "app.ico"
    if not ICON_PATH.exists():
        ICON_PATH = SPEC_DIR / "app.ico"
else:
    ICON_PATH = RESOURCES_DIR / "app.icns"

ICON_PATH = str(ICON_PATH) if ICON_PATH.exists() else None

# Data files to bundle
datas = []

# Add resources if they exist
if RESOURCES_DIR.exists():
    datas.append((str(RESOURCES_DIR), "accessisky/resources"))

# Hidden imports for wxPython and other dynamic imports
hiddenimports = [
    "wx",
    "wx.adv",
    "wx.html",
    "wx.lib.agw",
    "wx.lib.agw.aui",
    "wx.lib.mixins",
    "wx.lib.mixins.inspection",
    "httpx",
    "httpx._transports",
    "httpx._transports.default",
    "h11",
    "h2",
    "hpack",
    "attrs",
    "dateutil",
    "dateutil.parser",
]

# Platform-specific hidden imports
if IS_WINDOWS:
    hiddenimports.extend([
        "win32api",
        "win32con",
        "win32gui",
        "winsound",
    ])

# Excludes to reduce size
excludes = [
    "tkinter",
    "_tkinter",
    "tcl",
    "tk",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "PIL.ImageTk",
    "test",
    "tests",
    "unittest",
    "pytest",
]

# Analysis
a = Analysis(
    [str(SRC_DIR / "accessisky" / "__main__.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(SPEC_DIR / "hooks")] if (SPEC_DIR / "hooks").exists() else [],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# Remove unnecessary files from analysis
a.binaries = [b for b in a.binaries if not b[0].startswith("tcl")]
a.binaries = [b for b in a.binaries if not b[0].startswith("tk")]
a.binaries = [b for b in a.binaries if "_tkinter" not in b[0]]

# Remove cross-platform binary artifacts and limit sound_lib to platform-friendly bits
a.binaries = filter_platform_binaries(a.binaries, platform.system())
a.binaries = filter_sound_lib_entries(a.binaries, platform.system())
a.datas = filter_sound_lib_entries(a.datas, platform.system())

pyz = PYZ(a.pure)

if IS_MACOS:
    # macOS: Create .app bundle
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON_PATH,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=ICON_PATH,
        bundle_identifier=APP_BUNDLE_ID,
        version=APP_VERSION,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleVersion": APP_VERSION,
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleIdentifier": APP_BUNDLE_ID,
            "NSHighResolutionCapable": True,
            "NSRequiresAquaSystemAppearance": False,
            "LSMinimumSystemVersion": "10.13.0",
        },
    )
else:
    # Windows/Linux: Create executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON_PATH,
        version_file=None,
    )

    # Also create a directory-based distribution
    coll = COLLECT(
        EXE(
            pyz,
            a.scripts,
            [],
            exclude_binaries=True,
            name=APP_NAME,
            debug=False,
            bootloader_ignore_signals=False,
            strip=False,
            upx=True,
            console=False,
            disable_windowed_traceback=False,
            argv_emulation=False,
            target_arch=None,
            codesign_identity=None,
            entitlements_file=None,
            icon=ICON_PATH,
        ),
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=f"{APP_NAME}_dir",
    )
