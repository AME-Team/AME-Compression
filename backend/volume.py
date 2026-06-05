"""Volume analysis and adjustment functionality."""

import math
import re
import subprocess
from pathlib import Path

from .config import (
    DENOISE_MAX,
    DENOISE_MIN,
    MAX_VOLUME_LEVEL,
    TARGET_VOLUME_LEVEL,
)


def analyze_volume_level(
    input_path: str | Path, ffmpeg_path: str = "ffmpeg"
) -> dict[str, float | None]:
    """Analyze audio volume level using FFmpeg's volumedetect filter.

    Args:
        input_path (str): Path to input file (video or audio)
        ffmpeg_path (str): Path to ffmpeg executable

    Returns:
        dict: mean_volume (dB), max_volume (dB), recommended_gain (dB)
    """
    cmd = [
        ffmpeg_path,
        "-i",
        str(input_path),
        "-af",
        "volumedetect",
        "-vn",
        "-sn",
        "-dn",
        "-f",
        "null",
        "-",
    ]

    mean_volume = None
    max_volume = None

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",  # Replace undecodable characters to avoid UnicodeDecodeError
            check=False,  # volumedetect outputs to stderr, return code may be 0
        )

        # Parse volumedetect output from stderr (use empty string if None)
        output = result.stderr or ""

        # Parse mean_volume (e.g., [Parsed_volumedetect_0 @ ...] mean_volume: -27.5 dB)
        mean_match = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", output)
        if mean_match:
            mean_volume = float(mean_match.group(1))

        # Parse max_volume (e.g., [Parsed_volumedetect_0 @ ...] max_volume: -5.2 dB)
        max_match = re.search(r"max_volume:\s*(-?[\d.]+)\s*dB", output)
        if max_match:
            max_volume = float(max_match.group(1))

    except FileNotFoundError:
        return {
            "mean_volume": None,
            "max_volume": None,
            "recommended_gain": None,
        }

    # Calculate recommended gain
    recommended_gain = None
    if mean_volume is not None and max_volume is not None:
        recommended_gain = calculate_recommended_gain(mean_volume, max_volume)

    return {
        "mean_volume": mean_volume,
        "max_volume": max_volume,
        "recommended_gain": recommended_gain,
    }


def calculate_recommended_gain(mean_volume: float, max_volume: float) -> float:
    """Calculate recommended volume gain based on current audio levels.

    Args:
        mean_volume (float): Current mean volume in dB
        max_volume (float): Current max volume in dB

    Returns:
        float: Recommended gain in dB
    """
    # Calculate gain needed to reach target level
    gain_for_target = TARGET_VOLUME_LEVEL - mean_volume

    # Calculate maximum safe gain (to prevent clipping)
    # Leave 1dB headroom from 0dB
    max_safe_gain = MAX_VOLUME_LEVEL - max_volume

    # Use the smaller of the two to prevent clipping
    recommended_gain = min(gain_for_target, max_safe_gain)

    # Round to 1 decimal place
    recommended_gain = round(recommended_gain, 1)

    return recommended_gain


def parse_volume_gain(gain_str: str | None) -> tuple[float | None, bool]:
    """Parse volume gain string and return gain in dB.

    Args:
        gain_str (str): Gain string (e.g., "2.0", "10dB", "auto")

    Returns:
        tuple: (gain_db, is_auto) where gain_db is the gain in dB,
               and is_auto is True if "auto" was specified
    """
    if gain_str is None:
        return None, False

    gain_str = gain_str.strip()

    # Check for auto mode
    if gain_str.lower() == "auto":
        return None, True

    # Check for dB suffix
    if gain_str.lower().endswith("db"):
        try:
            return float(gain_str[:-2]), False
        except ValueError as err:
            raise ValueError(f"Invalid dB value '{gain_str}'") from err

    # Treat as multiplier (convert to dB)
    try:
        multiplier = float(gain_str)
    except ValueError as err:
        raise ValueError(f"Invalid volume gain value '{gain_str}'") from err

    if multiplier <= 0:
        raise ValueError("Volume multiplier must be positive")

    # Convert multiplier to dB: dB = 20 * log10(multiplier)
    gain_db = 20 * math.log10(multiplier)
    return round(gain_db, 1), False


def build_audio_filter(
    volume_gain_db: float | None = None, denoise_level: float | None = None
) -> str | None:
    """Build audio filter string for FFmpeg.

    Args:
        volume_gain_db (float): Volume gain in dB (None = no adjustment)
        denoise_level (float): Denoise level 0.0-1.0 (None = no denoise)

    Returns:
        str: Audio filter string or None if no filters needed
    """
    audio_filters: list[str] = []

    # Add denoise filter if specified
    if denoise_level is not None and denoise_level > 0:
        # Map 0.0-1.0 to noise reduction amount
        # Higher level = more aggressive noise reduction
        noise_reduction = int(denoise_level * 97)  # 0-97 range for afftdn
        audio_filters.append(f"afftdn=nr={noise_reduction}")

    # Add volume filter if specified
    if volume_gain_db is not None:
        audio_filters.append(f"volume={volume_gain_db}dB")

    if audio_filters:
        return ",".join(audio_filters)

    return None


def validate_denoise_level(denoise: float | None) -> float | None:
    """Validate and cap denoise level to valid range.

    Args:
        denoise (float): Denoise level

    Returns:
        float: Validated denoise level
    """
    if denoise is None:
        return None
    if denoise < DENOISE_MIN or denoise > DENOISE_MAX:
        print(
            f"Warning: Denoise level capped to {DENOISE_MIN}-{DENOISE_MAX} (requested: {denoise})"
        )
        return max(DENOISE_MIN, min(DENOISE_MAX, denoise))
    return denoise


def resolve_volume_gain(
    volume_gain_db: str | float | None,
    input_path: str | Path,
    ffmpeg_path: str = "ffmpeg",
) -> float | None:
    """Resolve volume gain to a numeric dB value.

    If volume_gain_db is \"auto\", analyze the input file to determine
    the recommended gain. If it's a string, parse it.

    Args:
        volume_gain_db: Volume gain value (str, float, or None)
        input_path: Path to input file for analysis
        ffmpeg_path: Path to ffmpeg executable

    Returns:
        float | None: Resolved gain in dB, or None if no gain specified
    """
    if volume_gain_db is None:
        return None

    if isinstance(volume_gain_db, str):
        gain_val, is_auto = parse_volume_gain(volume_gain_db)
        if is_auto:
            vol_info = analyze_volume_level(input_path, ffmpeg_path)
            return vol_info.get("recommended_gain")
        return gain_val

    return volume_gain_db
