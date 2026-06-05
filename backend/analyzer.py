"""Quality analysis and optimal settings suggestion for video files.

This module analyzes media files using ffprobe metadata and provides
recommended compression settings (CRF, denoise, etc.) based on the
computed Bits-Per-Pixel (BPP) metric.

The analysis follows a two-tier strategy:

1. **Fast tier** - BPP calculation from metadata (instant).
2. **Extended tier** - Short sample encoding with SSIM quality measurement
   (future upgrade path).

The fast tier is used by default.  It computes BPP from the video's bitrate,
resolution, and frame-rate, then maps the result to a recommended CRF value.
"""

import contextlib
import logging
from pathlib import Path
from typing import Any

from .config import (
    CRF_MAX,
    CRF_MIN,
    DEFAULT_CRF,
    DEFAULT_DENOISE_LEVEL,
)
from .ffmpeg import get_detailed_media_info, get_video_info_safe

logger = logging.getLogger(__name__)


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

    basic_info = get_video_info_safe(media_path, ffprobe_path)
    if not basic_info:
        return None

    detailed = get_detailed_media_info(media_path, ffprobe_path)
    bit_rate = None
    codec_name = ""

    if detailed:
        streams = detailed.get("streams", [])
        for stream in streams:
            if stream.get("codec_type") == "video":
                br = stream.get("bit_rate")
                if br is not None:
                    with contextlib.suppress(ValueError, TypeError):
                        bit_rate = int(br)
                codec_name = stream.get("codec_name", "")
                break

        if bit_rate is None:
            fmt = detailed.get("format", {})
            br = fmt.get("bit_rate")
            if br is not None:
                with contextlib.suppress(ValueError, TypeError):
                    bit_rate = int(br)

    return {
        "width": basic_info.get("width"),
        "height": basic_info.get("height"),
        "fps": basic_info.get("fps"),
        "duration": basic_info.get("duration"),
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
    if not media_path.exists():
        return {
            "status": "error",
            "recommended_crf": DEFAULT_CRF,
            "recommend_denoise": False,
            "denoise_level": None,
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

    return {
        "status": "success",
        "recommended_crf": recommended_crf,
        "recommend_denoise": recommend_denoise,
        "denoise_level": denoise_level,
        "bpp": round(bpp, 4),
        "reason": reason,
        "metadata": meta,
    }
