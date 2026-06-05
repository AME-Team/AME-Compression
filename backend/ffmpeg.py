"""FFmpeg executable detection and path management."""

import contextlib
import json
import logging
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


def _get_executable_names() -> tuple[str, str]:
    """Return platform-appropriate ffmpeg and ffprobe executable names."""
    is_windows = platform.system() == "Windows"
    ffmpeg_name = "ffmpeg.exe" if is_windows else "ffmpeg"
    ffprobe_name = "ffprobe.exe" if is_windows else "ffprobe"
    return ffmpeg_name, ffprobe_name


def _get_bundled_dir() -> Path:
    """Return the directory where bundled ffmpeg binaries are expected."""
    return Path(__file__).parent.parent.resolve() / "bin"


def find_ffmpeg() -> str:
    """Locate the ffmpeg executable with the following priority:

    1. Bundled ffmpeg at ``<project_root>/bin/ffmpeg(.exe)``
    2. System ffmpeg discoverable via ``PATH`` (``shutil.which``)
    3. Raise ``FileNotFoundError`` if neither is found

    Returns:
        Absolute path to the ffmpeg executable as a string.

    Raises:
        FileNotFoundError: ffmpeg cannot be located.
    """
    ffmpeg_name, _ = _get_executable_names()
    bundled_dir = _get_bundled_dir()

    bundled = bundled_dir / ffmpeg_name
    if bundled.exists():
        logger.info("Using bundled FFmpeg: %s", bundled)
        return str(bundled)

    system = shutil.which("ffmpeg")
    if system is not None:
        logger.info("Using system FFmpeg: %s", system)
        return system

    raise FileNotFoundError(
        "ffmpeg が見つかりません。FFmpeg をインストールするか、"
        "bin/ ディレクトリに配置してください。"
        " / FFmpeg not found. Install FFmpeg or place it in the bin/ directory."
    )


def find_ffprobe() -> str:
    """Locate the ffprobe executable with the following priority:

    1. Bundled ffprobe at ``<project_root>/bin/ffprobe(.exe)``
    2. System ffprobe discoverable via ``PATH`` (``shutil.which``)
    3. Raise ``FileNotFoundError`` if neither is found

    Returns:
        Absolute path to the ffprobe executable as a string.

    Raises:
        FileNotFoundError: ffprobe cannot be located.
    """
    _, ffprobe_name = _get_executable_names()
    bundled_dir = _get_bundled_dir()

    bundled = bundled_dir / ffprobe_name
    if bundled.exists():
        logger.info("Using bundled ffprobe: %s", bundled)
        return str(bundled)

    system = shutil.which("ffprobe")
    if system is not None:
        logger.info("Using system ffprobe: %s", system)
        return system

    raise FileNotFoundError(
        "ffprobe が見つかりません。FFmpeg をインストールするか、"
        "bin/ ディレクトリに配置してください。"
        " / ffprobe not found. Install FFmpeg or place it in the bin/ directory."
    )


def get_ffmpeg_executables() -> tuple[str, str]:
    """Detect OS and return appropriate FFmpeg executable paths.

    Checks for bundled FFmpeg executables in the ``bin/`` directory first,
    then falls back to the system PATH.  If neither can be found the
    function returns ``("ffmpeg", "ffprobe")`` so that callers that already
    handle ``FileNotFoundError`` from subprocess can degrade gracefully.

    Returns:
        tuple: (ffmpeg_path, ffprobe_path)
    """
    try:
        return find_ffmpeg(), find_ffprobe()
    except FileNotFoundError:
        return "ffmpeg", "ffprobe"


def get_video_info(video_path: str | Path, ffprobe_path: str = "ffprobe") -> dict[str, Any] | None:
    """Get video information using ffprobe.

    Args:
        video_path (str): Path to video file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Video width, height, duration, fps
    """
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration",
        "-of",
        "csv=s=x:p=0",
        str(video_path),
    ]

    width = None
    height = None
    fps = None
    duration = None

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        output = result.stdout.strip()
        if output:
            parts = output.split("x")
            if len(parts) >= 2:
                width = int(parts[0])
                remaining = parts[1].split(",")
                height = int(remaining[0])

                # Parse FPS (format: 30/1 or 29.97)
                if len(remaining) > 1:
                    fps_str = remaining[1]
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        if float(den) != 0:
                            fps = float(num) / float(den)
                    else:
                        with contextlib.suppress(ValueError):
                            fps = float(fps_str)

                if len(remaining) > 2:
                    with contextlib.suppress(ValueError):
                        duration = float(remaining[2])
    except subprocess.CalledProcessError as e:
        print(f"Error getting video info: {e.stderr}")
        return None

    # If duration not found in stream, try format-level duration
    if duration is None:
        format_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video_path),
        ]
        try:
            format_result = subprocess.run(
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    duration = float(format_output)
        except subprocess.CalledProcessError:
            pass  # Ignore errors, duration will remain None

    if width is not None and height is not None:
        return {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
        }

    return None


def get_detailed_media_info(
    media_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Get detailed media information using ffprobe.

    Args:
        media_path (str): Path to media file (video or audio)
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Detailed media information including codecs, bitrate, etc.
    """
    cmd = [
        ffprobe_path,
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(media_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        data = cast(dict[str, Any], json.loads(result.stdout))
        return data
    except subprocess.CalledProcessError:
        return None
    except json.JSONDecodeError:
        return None


def _parse_audio_csv_output(output: str) -> dict[str, Any]:
    """Parse ffprobe CSV output for audio info."""
    duration = None
    bitrate = None
    sample_rate = None
    channels = None

    lines = output.strip().split("\n")
    for line in lines:
        parts = line.split(",")
        if len(parts) >= 4:
            # Stream info: bit_rate, sample_rate, channels, duration
            with contextlib.suppress(ValueError):
                if parts[0]:
                    bitrate = int(parts[0])
                if parts[1]:
                    sample_rate = int(parts[1])
                if parts[2]:
                    channels = int(parts[2])
                if parts[3]:
                    duration = float(parts[3])
        elif len(parts) == 1 and parts[0]:
            # Format duration (fallback)
            with contextlib.suppress(ValueError):
                duration = float(parts[0])

    return {
        "duration": duration,
        "bitrate": bitrate,
        "sample_rate": sample_rate,
        "channels": channels,
    }


def get_audio_info(audio_path: str | Path, ffprobe_path: str = "ffprobe") -> dict[str, Any]:
    """Get audio information using ffprobe.

    Args:
        audio_path (str): Path to audio file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Audio duration, bitrate, sample_rate, channels
    """
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate,sample_rate,channels,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(audio_path),
    ]

    info: dict[str, Any] = {
        "duration": None,
        "bitrate": None,
        "sample_rate": None,
        "channels": None,
    }

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        info = _parse_audio_csv_output(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting audio info: {e}")

    # If duration not found, try format-level duration
    if info["duration"] is None:
        format_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(audio_path),
        ]
        try:
            format_result = subprocess.run(
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    info["duration"] = float(format_output)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return info


def _parse_video_csv_output(output: str) -> dict[str, Any]:
    """Parse ffprobe CSV output for video info."""
    width = None
    height = None
    fps = None
    duration = None

    parts = output.strip().split("x")
    if len(parts) >= 2:
        with contextlib.suppress(ValueError):
            width = int(parts[0])
            remaining = parts[1].split(",")
            height = int(remaining[0])

            if len(remaining) > 1:
                fps_str = remaining[1]
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    if float(den) != 0:
                        fps = float(num) / float(den)
                else:
                    fps = float(fps_str)

            if len(remaining) > 2:
                duration = float(remaining[2])

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
    }


def get_video_info_safe(
    video_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Get video information using ffprobe (service layer safe version).

    Unlike get_video_info, this function does not call sys.exit on failure,
    making it safe for API/GUI use.

    Args:
        video_path (str): Path to video file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Video width, height, duration, fps, or None on error
    """
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,duration",
        "-of",
        "csv=s=x:p=0",
        str(video_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        info = _parse_video_csv_output(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return None

    if info["duration"] is None:
        format_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(video_path),
        ]
        try:
            format_result = subprocess.run(
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    info["duration"] = float(format_output)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    if info["width"] is not None and info["height"] is not None:
        return info

    return None


def get_audio_info_safe(
    audio_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Get audio information using ffprobe (service layer safe version).

    Unlike get_audio_info, this function does not call sys.exit on failure,
    making it safe for API/GUI use.

    Args:
        audio_path (str): Path to audio file
        ffprobe_path (str): Path to ffprobe executable

    Returns:
        dict: Audio duration, bitrate, sample_rate, channels
    """
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=bit_rate,sample_rate,channels,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "csv=p=0",
        str(audio_path),
    ]

    info: dict[str, Any] = {
        "duration": None,
        "bitrate": None,
        "sample_rate": None,
        "channels": None,
    }

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        info = _parse_audio_csv_output(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if info["duration"] is None:
        format_cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(audio_path),
        ]
        try:
            format_result = subprocess.run(
                format_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )
            format_output = format_result.stdout.strip()
            if format_output:
                with contextlib.suppress(ValueError):
                    info["duration"] = float(format_output)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    return info
