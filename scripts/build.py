"""AME Compression build script for creating standalone executables with PyInstaller.

Usage:
    uv run scripts/build.py                     # Build directory mode (default, no FFmpeg)
    uv run scripts/build.py --onefile           # Build single-file mode
    uv run scripts/build.py --with-ffmpeg       # Bundle FFmpeg from bin/ directory (bundled build)
    uv run scripts/build.py --no-ffmpeg         # Explicitly build without FFmpeg (non-bundled build)

The ``--with-ffmpeg`` flag produces a *bundled* build where ffmpeg/ffprobe
binaries from ``bin/`` are embedded in the distribution.  Without this flag
the resulting build will attempt to discover ffmpeg on the target system at
runtime (via PATH).

When ``--with-ffmpeg`` is used the script also copies the FFmpeg license
document (``LICENSE_FFMPEG.txt``) into the output directory.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SPEC_FILE = PROJECT_ROOT / "AmeCompression.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
BIN_DIR = PROJECT_ROOT / "bin"
LICENSE_FFMPEG = PROJECT_ROOT / "LICENSE_FFMPEG.txt"


def clean() -> None:
    """Remove previous build artifacts."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    print("Cleaned previous build artifacts.")


def _add_ffmpeg_binaries(cmd: list[str]) -> bool:
    """Append FFmpeg binaries to the PyInstaller command if available.

    Returns:
        ``True`` if binaries were added, ``False`` otherwise.
    """
    ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
    ffmpeg_exe = BIN_DIR / ffmpeg_name
    ffprobe_exe = BIN_DIR / ffprobe_name

    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        cmd.extend(["--add-binary", f"{ffmpeg_exe}{os.pathsep}bin"])
        cmd.extend(["--add-binary", f"{ffprobe_exe}{os.pathsep}bin"])
        print(f"Bundling FFmpeg from {BIN_DIR}")
        return True

    print(
        f"Warning: --with-ffmpeg specified but {ffmpeg_name} and/or "
        f"{ffprobe_name} not found in {BIN_DIR}. Building without FFmpeg."
    )
    return False


def _post_build_copy(onefile: bool, with_ffmpeg: bool) -> None:
    """Perform post-build file copy operations."""
    if not onefile and with_ffmpeg:
        target_bin = DIST_DIR / "ame-compression-backend" / "bin"
        if target_bin.exists():
            print(f"FFmpeg bundled at: {target_bin}")

    if with_ffmpeg and LICENSE_FFMPEG.exists():
        out_dir = DIST_DIR / "ame-compression-backend"
        if onefile:
            out_dir = DIST_DIR
        if out_dir.exists():
            shutil.copy2(LICENSE_FFMPEG, out_dir / "LICENSE_FFMPEG.txt")
            print(f"FFmpeg license copied to: {out_dir}")


def build(onefile: bool = False, with_ffmpeg: bool = False) -> None:
    """Build the AmeCompression executable.

    Args:
        onefile: If ``True``, produce a single-file executable.
        with_ffmpeg: If ``True``, bundle ffmpeg/ffprobe from ``bin/``.
    """
    clean()

    main_script = PROJECT_ROOT / "run.py"
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm"]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    cmd.extend(["--name", "ame-compression-backend"])

    for hidden in ["backend", "flask", "flask_cors"]:
        cmd.extend(["--hidden-import", hidden])

    for exclude in ["customtkinter", "tkinter", "windnd"]:
        cmd.extend(["--exclude-module", exclude])

    icon_path = PROJECT_ROOT / "assets" / "icon.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    if with_ffmpeg:
        with_ffmpeg = _add_ffmpeg_binaries(cmd)

    cmd.append(str(main_script))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), check=False)

    if result.returncode != 0:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    _post_build_copy(onefile, with_ffmpeg)

    build_type = "bundled (with FFmpeg)" if with_ffmpeg else "non-bundled (system FFmpeg)"
    print(f"\nBuild completed successfully! ({build_type})")
    print(f"Output directory: {DIST_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AME Compression executable")
    parser.add_argument("--onefile", action="store_true", help="Build as single .exe file")
    parser.add_argument(
        "--with-ffmpeg",
        action="store_true",
        help="Bundle FFmpeg from bin/ directory (bundled build)",
    )
    parser.add_argument(
        "--no-ffmpeg",
        action="store_true",
        help="Explicitly build without FFmpeg (non-bundled build, default)",
    )
    args = parser.parse_args()

    if not SPEC_FILE.exists():
        print(f"Error: Spec file not found: {SPEC_FILE}")
        sys.exit(1)

    build(onefile=args.onefile, with_ffmpeg=args.with_ffmpeg)


if __name__ == "__main__":
    main()
