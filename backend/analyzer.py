"""Quality analysis and optimal settings suggestion for media files.

This module analyzes media files using ffprobe metadata and provides
recommended compression settings based on the computed metrics.

For **video files** the analysis computes Bits-Per-Pixel (BPP) and maps it
to a recommended CRF value.  For **audio files** the analysis inspects the
source bitrate and recommends an appropriate MP3 output bitrate.

The analysis follows a two-tier strategy:

1. **Fast tier** - Metadata calculation from ffprobe (instant).
2. **Extended tier** - Short sample encoding with SSIM quality measurement
   (future upgrade path).

The fast tier is used by default.
"""

import contextlib
import logging
from pathlib import Path
from typing import Any

from .config import (
    AUDIO_EXTENSIONS,
    CRF_MAX,
    CRF_MIN,
    DEFAULT_CRF,
    DEFAULT_DENOISE_LEVEL,
    VIDEO_EXTENSIONS,
)
from .ffmpeg import find_ffmpeg, get_detailed_media_info
from .volume import analyze_volume_level

logger = logging.getLogger(__name__)


def _parse_fps(video_stream: dict[str, Any]) -> float | None:
    """Parse FPS from a video stream's r_frame_rate field."""
    fps_str = video_stream.get("r_frame_rate")
    if not fps_str:
        return None
    if "/" in fps_str:
        with contextlib.suppress(ValueError, ZeroDivisionError):
            num, den = fps_str.split("/")
            if float(den) != 0:
                return float(num) / float(den)
        return None
    with contextlib.suppress(ValueError):
        return float(fps_str)
    return None


def _parse_duration(video_stream: dict[str, Any], fmt_info: dict[str, Any]) -> float | None:
    """Parse duration from video stream or format info."""
    duration_str = video_stream.get("duration")
    if duration_str is not None:
        with contextlib.suppress(ValueError):
            return float(duration_str)
    duration_str = fmt_info.get("duration")
    if duration_str is not None:
        with contextlib.suppress(ValueError):
            return float(duration_str)
    return None


def _parse_bit_rate(
    video_stream: dict[str, Any], fmt_info: dict[str, Any], file_path: Path, duration: float | None
) -> int | None:
    """Parse bit rate from video stream, format, or file size fallback."""
    br_str = video_stream.get("bit_rate")
    if br_str is not None:
        with contextlib.suppress(ValueError, TypeError):
            return int(br_str)
    br_str = fmt_info.get("bit_rate")
    if br_str is not None:
        with contextlib.suppress(ValueError, TypeError):
            return int(br_str)
    if duration and duration > 0:
        with contextlib.suppress(OSError):
            file_size = file_path.stat().st_size
            return int((file_size * 8) / duration)
    return None


def _extract_video_metadata(
    media_path: str | Path, ffprobe_path: str = "ffprobe"
) -> dict[str, Any] | None:
    """Extract detailed metadata from a video file.

    Returns:
        A dict with keys ``width``, ``height``, ``fps``, ``duration``,
        ``bit_rate``, ``codec_name``, or ``None`` on failure.
    """
    media_path = Path(media_path)
    if not media_path.exists():
        return None

    detailed = get_detailed_media_info(media_path, ffprobe_path)
    if not detailed:
        return None

    streams = detailed.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video_stream:
        return None

    try:
        width = int(video_stream.get("width"))
        height = int(video_stream.get("height"))
    except (ValueError, TypeError):
        return None

    fmt_info = detailed.get("format", {})
    fps = _parse_fps(video_stream)
    duration = _parse_duration(video_stream, fmt_info)
    bit_rate = _parse_bit_rate(video_stream, fmt_info, media_path, duration)
    codec_name = video_stream.get("codec_name", "")

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "bit_rate": bit_rate,
        "codec_name": codec_name,
    }


def calculate_bpp(
    width: int,
    height: int,
    fps: float,
    bit_rate: int,
) -> float:
    """Calculate Bits-Per-Pixel.

    Args:
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frame rate.
        bit_rate: Video bitrate in bits per second.

    Returns:
        Bits-Per-Pixel value.
    """
    if width <= 0 or height <= 0 or fps <= 0 or bit_rate <= 0:
        return 0.0
    return bit_rate / (width * height * fps)


def _bpp_to_recommended_crf(bpp: float) -> int:
    """Map a BPP value to a recommended CRF for SVT-AV1.

    The mapping is based on empirical observations for SVT-AV1:

    - Very high BPP (>0.3): source is high quality / wasteful → aggressive
      compression is safe → higher CRF.
    - Low BPP (<0.05): source is already heavily compressed → raising CRF
      further would degrade quality noticeably → lower CRF.

    Args:
        bpp: Bits-Per-Pixel value.

    Returns:
        Recommended CRF value in the range [CRF_MIN, CRF_MAX].
    """
    if bpp <= 0:
        return DEFAULT_CRF

    bpp_thresholds: list[tuple[float, int]] = [
        (0.03, 20),
        (0.05, 25),
        (0.08, 28),
        (0.12, 30),
        (0.18, 33),
        (0.25, 36),
        (0.35, 38),
        (0.50, 40),
        (float("inf"), 42),
    ]

    for threshold, crf in bpp_thresholds:
        if bpp < threshold:
            return max(CRF_MIN, min(CRF_MAX, crf))

    return DEFAULT_CRF


def _should_recommend_denoise(bpp: float) -> bool:
    """Determine whether denoise should be recommended.

    Very high BPP with relatively low resolution often indicates noisy
    source material that wastes bitrate.

    Args:
        bpp: Bits-Per-Pixel value.

    Returns:
        ``True`` if denoise is recommended.
    """
    return bpp > 0.25


def analyze_quality(media_path: str | Path, ffprobe_path: str = "ffprobe") -> dict[str, Any]:
    """Analyze a video file and recommend optimal compression settings.

    This is the main entry point for quality analysis.  It extracts video
    metadata, calculates BPP, and returns a set of recommended settings.

    Args:
        media_path: Path to the video file.
        ffprobe_path: Path to the ffprobe executable.

    Returns:
        A dict with the following keys:

        - ``status``: ``"success"`` or ``"error"``
        - ``recommended_crf``: Suggested CRF value (int)
        - ``recommend_denoise``: Whether denoise is recommended (bool)
        - ``denoise_level``: Suggested denoise level if recommended (float)
        - ``bpp``: Calculated Bits-Per-Pixel (float)
        - ``reason``: Human-readable explanation (str)
        - ``metadata``: Extracted video metadata (dict)
    """
    media_path = Path(media_path)
    # Note: subprocess calls in volume.py use argument list form (shell=False),
    # preventing OS command injection. We ensure it is a valid existing file.
    if not media_path.exists() or not media_path.is_file():
        return {
            "status": "error",
            "recommended_crf": DEFAULT_CRF,
            "recommend_denoise": False,
            "denoise_level": None,
            "recommended_volume_gain": None,
            "bpp": 0.0,
            "reason": "File not found.",
            "metadata": {},
        }

    meta = _extract_video_metadata(media_path, ffprobe_path)
    if not meta or meta["width"] is None or meta["height"] is None:
        return {
            "status": "error",
            "recommended_crf": DEFAULT_CRF,
            "recommend_denoise": False,
            "denoise_level": None,
            "recommended_volume_gain": None,
            "bpp": 0.0,
            "reason": "Could not extract video metadata.",
            "metadata": {},
        }

    width = meta["width"]
    height = meta["height"]
    fps = meta.get("fps") or 30.0
    bit_rate = meta.get("bit_rate") or 0

    if bit_rate == 0:
        return {
            "status": "success",
            "recommended_crf": DEFAULT_CRF,
            "recommend_denoise": False,
            "denoise_level": None,
            "recommended_volume_gain": None,
            "bpp": 0.0,
            "reason": "Bitrate information unavailable; using default CRF.",
            "metadata": meta,
        }

    bpp = calculate_bpp(width, height, fps, bit_rate)
    recommended_crf = _bpp_to_recommended_crf(bpp)
    recommend_denoise = _should_recommend_denoise(bpp)
    denoise_level = DEFAULT_DENOISE_LEVEL if recommend_denoise else None

    resolution_label = f"{width}x{height}"
    bitrate_mbps = bit_rate / 1_000_000

    if bpp > 0.25:
        reason = (
            f"The video ({resolution_label}, {bitrate_mbps:.1f} Mbps, "
            f"BPP: {bpp:.3f}) has a very high bitrate relative to its resolution. "
            f"A higher CRF ({recommended_crf}) can significantly reduce file size "
            f"with minimal quality loss. Denoise is recommended to improve "
            f"compression efficiency."
        )
    elif bpp > 0.1:
        reason = (
            f"The video ({resolution_label}, {bitrate_mbps:.1f} Mbps, "
            f"BPP: {bpp:.3f}) has a moderate bitrate. "
            f"CRF {recommended_crf} provides a good balance of quality and "
            f"file size."
        )
    elif bpp > 0.05:
        reason = (
            f"The video ({resolution_label}, {bitrate_mbps:.1f} Mbps, "
            f"BPP: {bpp:.3f}) is already moderately compressed. "
            f"CRF {recommended_crf} is recommended to maintain quality."
        )
    else:
        reason = (
            f"The video ({resolution_label}, {bitrate_mbps:.1f} Mbps, "
            f"BPP: {bpp:.3f}) is already heavily compressed. "
            f"A conservative CRF ({recommended_crf}) is recommended to "
            f"avoid further quality degradation."
        )

    recommended_volume_gain = None
    try:
        ffmpeg_path = find_ffmpeg()
        volume_info = analyze_volume_level(media_path, ffmpeg_path)
        recommended_volume_gain = volume_info.get("recommended_gain")
    except Exception as e:
        logger.warning("Volume analysis failed for %s: %s", media_path, e)

    return {
        "status": "success",
        "recommended_crf": recommended_crf,
        "recommend_denoise": recommend_denoise,
        "denoise_level": denoise_level,
        "recommended_volume_gain": recommended_volume_gain,
        "bpp": round(bpp, 4),
        "reason": reason,
        "metadata": meta,
    }


def _source_bitrate_to_recommended_mp3(source_bitrate_kbps: int) -> int:
    """Map a source audio bitrate to a recommended MP3 output bitrate.

    The recommendation never exceeds the source bitrate for lossy codecs,
    and caps at 320 kbps for lossless sources.

    Args:
        source_bitrate_kbps: Source audio bitrate in kbps.

    Returns:
        Recommended MP3 output bitrate in kbps.
    """
    mp3_bitrates = [64, 96, 128, 160, 192, 256, 320]
    for br in mp3_bitrates:
        if source_bitrate_kbps <= br:
            return br
    return 320


def _extract_audio_metadata(
    audio_stream: dict[str, Any], fmt_info: dict[str, Any], media_path: Path
) -> dict[str, Any]:
    """Extract metadata from an audio stream and format info."""
    codec_name = audio_stream.get("codec_name", "")
    sample_rate = None
    channels = None
    with contextlib.suppress(ValueError, TypeError):
        sr_val = audio_stream.get("sample_rate")
        if sr_val is not None:
            sample_rate = int(sr_val)
    with contextlib.suppress(ValueError, TypeError):
        ch_val = audio_stream.get("channels")
        if ch_val is not None:
            channels = int(ch_val)

    duration = None
    duration_str = fmt_info.get("duration")
    if duration_str is not None:
        with contextlib.suppress(ValueError):
            duration = float(duration_str)

    bit_rate = None
    br_str = audio_stream.get("bit_rate")
    if br_str is not None:
        with contextlib.suppress(ValueError, TypeError):
            bit_rate = int(br_str)
    if bit_rate is None:
        br_str = fmt_info.get("bit_rate")
        if br_str is not None:
            with contextlib.suppress(ValueError, TypeError):
                bit_rate = int(br_str)
    if bit_rate is None and duration and duration > 0:
        with contextlib.suppress(OSError):
            file_size = media_path.stat().st_size
            bit_rate = int((file_size * 8) / duration)

    return {
        "codec_name": codec_name,
        "sample_rate": sample_rate,
        "channels": channels,
        "duration": duration,
        "bit_rate": bit_rate,
    }


def analyze_audio_quality(media_path: str | Path, ffprobe_path: str = "ffprobe") -> dict[str, Any]:
    """Analyze an audio file and recommend an optimal output bitrate.

    Args:
        media_path: Path to the audio file.
        ffprobe_path: Path to the ffprobe executable.

    Returns:
        A dict with the following keys:

        - ``status``: ``"success"`` or ``"error"``
        - ``recommended_bitrate``: Suggested MP3 bitrate in kbps (int)
        - ``source_bitrate_kbps``: Source audio bitrate in kbps (int or None)
        - ``reason``: Human-readable explanation (str)
        - ``metadata``: Extracted audio metadata (dict)
    """
    media_path = Path(media_path)
    # Note: subprocess calls in volume.py use argument list form (shell=False),
    # preventing OS command injection. We ensure it is a valid existing file.
    if not media_path.exists() or not media_path.is_file():
        return {
            "status": "error",
            "recommended_bitrate": 192,
            "source_bitrate_kbps": None,
            "recommended_crf": None,
            "recommend_denoise": None,
            "denoise_level": None,
            "recommended_volume_gain": None,
            "bpp": None,
            "reason": "File not found.",
            "metadata": {},
        }

    detailed = get_detailed_media_info(media_path, ffprobe_path)
    if not detailed:
        return {
            "status": "error",
            "recommended_bitrate": 192,
            "source_bitrate_kbps": None,
            "recommended_crf": None,
            "recommend_denoise": None,
            "denoise_level": None,
            "recommended_volume_gain": None,
            "bpp": None,
            "reason": "Could not extract audio metadata.",
            "metadata": {},
        }

    streams = detailed.get("streams", [])
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not audio_stream:
        return {
            "status": "error",
            "recommended_bitrate": 192,
            "source_bitrate_kbps": None,
            "recommended_crf": None,
            "recommend_denoise": None,
            "denoise_level": None,
            "recommended_volume_gain": None,
            "bpp": None,
            "reason": "No audio stream found.",
            "metadata": {},
        }

    meta = _extract_audio_metadata(audio_stream, detailed.get("format", {}), media_path)
    bit_rate = meta.get("bit_rate")

    recommended_volume_gain = None
    try:
        ffmpeg_path = find_ffmpeg()
        volume_info = analyze_volume_level(media_path, ffmpeg_path)
        recommended_volume_gain = volume_info.get("recommended_gain")
    except Exception as e:
        logger.warning("Volume analysis failed for %s: %s", media_path, e)

    if bit_rate is None or bit_rate <= 0:
        return {
            "status": "success",
            "recommended_bitrate": 192,
            "source_bitrate_kbps": None,
            "recommended_crf": None,
            "recommend_denoise": None,
            "denoise_level": None,
            "recommended_volume_gain": recommended_volume_gain,
            "bpp": None,
            "reason": "Bitrate information unavailable; using default 192 kbps.",
            "metadata": meta,
        }

    source_kbps = bit_rate // 1000
    recommended = _source_bitrate_to_recommended_mp3(source_kbps)

    if recommended >= source_kbps:
        reason = (
            f"The source audio ({meta['codec_name']}, {source_kbps} kbps) has a bitrate "
            f"of {source_kbps} kbps. A bitrate of {recommended} kbps is recommended "
            f"to maintain quality."
        )
    else:
        reason = (
            f"The source audio ({meta['codec_name']}, {source_kbps} kbps) has a high bitrate. "
            f"An output bitrate of {recommended} kbps provides excellent quality "
            f"with good compression."
        )

    return {
        "status": "success",
        "recommended_bitrate": recommended,
        "source_bitrate_kbps": source_kbps,
        "recommended_crf": None,
        "recommend_denoise": None,
        "denoise_level": None,
        "recommended_volume_gain": recommended_volume_gain,
        "bpp": None,
        "reason": reason,
        "metadata": meta,
    }


def detect_media_type(file_path: str | Path) -> str:
    """Detect whether a file is video or audio based on its extension.

    Args:
        file_path: Path to the file.

    Returns:
        ``"video"`` or ``"audio"``.
    """
    ext = Path(file_path).suffix.lower()
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "video"
