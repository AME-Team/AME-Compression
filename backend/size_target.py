"""Target-size helpers for two-pass video compression.

The target-size mode converts a byte budget (absolute size or a percentage of
the original file) into a video bitrate for a two-pass VBR encode. Everything
that can reject a request lives here so the API layer, the service layer and
the tests share one implementation.
"""

from dataclasses import dataclass

from .config import (
    CONTAINER_OVERHEAD_RATIO,
    DEFAULT_AUDIO_BITRATE,
    MAX_AUDIO_BITRATE,
    MIN_VIDEO_BITRATE_KBPS,
    TARGET_SIZE_MAX_MB,
    TARGET_SIZE_MIN_MB,
    TARGET_SIZE_PERCENT_MAX,
    TARGET_SIZE_PERCENT_MIN,
)
from .utils import parse_bitrate

__all__ = [
    "MB_IN_BYTES",
    "SizeTarget",
    "TargetBitratePlan",
    "TargetSizeError",
    "resolve_audio_bitrate_for_budget",
    "resolve_target_bitrate",
    "resolve_target_bytes",
]

MB_IN_BYTES = 1024 * 1024


class TargetSizeError(ValueError):
    """Raised when a target-size request cannot be honoured.

    The message is user-facing (shown in the UI), so it must state what is
    wrong and what the user can do about it.
    """


@dataclass(frozen=True)
class SizeTarget:
    """User-supplied size target: exactly one of the two fields is set.

    Attributes:
        size_bytes: Absolute target size in bytes.
        percent: Target size as a percentage of the input file size.
    """

    size_bytes: int | None = None
    percent: float | None = None


@dataclass(frozen=True)
class TargetBitratePlan:
    """Resolved bitrate budget for a target-size encode.

    Attributes:
        target_bytes: Size the output file should not exceed.
        duration: Media duration in seconds used for the budget.
        total_kbps: Bitrate budget for the whole file.
        audio_kbps: Bitrate reserved for the audio track.
        video_kbps: Bitrate budget left for the video track (pass 2).
        video_only_bytes: Bytes the video track alone may occupy.
    """

    target_bytes: int
    duration: float
    total_kbps: float
    audio_kbps: int
    video_kbps: int
    video_only_bytes: int


def _validate_bytes(input_size: int, size_bytes: int) -> int:
    """Validate an absolute size target and return it as bytes."""
    if input_size <= 0:
        msg = "入力ファイルのサイズを取得できませんでした。"
        raise TargetSizeError(msg)
    size_mb = size_bytes / MB_IN_BYTES
    if size_bytes <= 0 or size_mb < TARGET_SIZE_MIN_MB:
        msg = f"目標サイズは {TARGET_SIZE_MIN_MB} MB 以上を指定してください。"
        raise TargetSizeError(msg)
    if size_mb > TARGET_SIZE_MAX_MB:
        msg = f"目標サイズは {TARGET_SIZE_MAX_MB} MB 以下を指定してください。"
        raise TargetSizeError(msg)
    return int(size_bytes)


def _validate_percent(input_size: int, percent: float) -> int:
    """Validate a percentage target and return the resulting byte count."""
    if input_size <= 0:
        msg = "入力ファイルのサイズを取得できませんでした。"
        raise TargetSizeError(msg)
    if not TARGET_SIZE_PERCENT_MIN <= percent <= TARGET_SIZE_PERCENT_MAX:
        msg = (
            f"割合は {TARGET_SIZE_PERCENT_MIN}% から "
            f"{TARGET_SIZE_PERCENT_MAX}% の範囲で指定してください。"
        )
        raise TargetSizeError(msg)
    return max(1, int(input_size * percent / 100))


def resolve_target_bytes(input_size: int, target: SizeTarget) -> int:
    """Resolve the requested output size in bytes.

    Exactly one of ``target.size_bytes`` and ``target.percent`` must be set;
    passing both (or neither) is reported to the user instead of silently
    preferring one of them.

    Args:
        input_size: Size of the input file in bytes.
        target: Requested size target.

    Returns:
        Target size in bytes.

    Raises:
        TargetSizeError: If the combination or the value is invalid.
    """
    if target.size_bytes is not None and target.percent is not None:
        msg = "目標サイズは絶対サイズと割合のどちらか一方だけを指定してください。"
        raise TargetSizeError(msg)
    if target.size_bytes is not None:
        return _validate_bytes(input_size, target.size_bytes)
    if target.percent is None:
        msg = "目標サイズが指定されていません。絶対サイズ (MB) か割合 (%) を入力してください。"
        raise TargetSizeError(msg)
    return _validate_percent(input_size, target.percent)


def resolve_audio_bitrate_for_budget(raw_audio_bitrate: str | int | float | None) -> str:
    """Return the audio bitrate both the request layer and the job layer budget with.

    Applies the same default (``DEFAULT_AUDIO_BITRATE``) and the same ceiling
    (``MAX_AUDIO_BITRATE``) as the encoder, and always returns a lower-case
    ``kbps`` string so the value is valid both for the budget math and as an
    FFmpeg ``-b:a`` argument. ``parse_bitrate`` raises ``ValueError`` for input
    that is not a bitrate at all; callers turn that into a user-facing error.
    """
    text = DEFAULT_AUDIO_BITRATE if raw_audio_bitrate is None else str(raw_audio_bitrate).strip()
    if text == "":
        text = DEFAULT_AUDIO_BITRATE
    kbps = parse_bitrate(text)
    kbps = min(kbps, MAX_AUDIO_BITRATE)
    return f"{kbps}k"


def resolve_target_bitrate(
    input_size: int,
    duration: float | None,
    audio_bitrate: str | int | float | None,
    target: SizeTarget,
    audio_enabled: bool = True,
) -> TargetBitratePlan:
    """Convert a size target into a two-pass video bitrate budget.

    The audio track keeps its own bitrate, container overhead is reserved at
    ``CONTAINER_OVERHEAD_RATIO``, and the remainder becomes the video bitrate
    for the second pass.

    Args:
        input_size: Size of the input file in bytes.
        duration: Media duration in seconds.
        audio_bitrate: Audio bitrate string (e.g. ``"192k"``) or kbps number.
        target: Requested size target.
        audio_enabled: Whether the output carries an audio track.

    Returns:
        A resolved bitrate plan.

    Raises:
        TargetSizeError: If the media cannot reach the requested size.
    """
    target_bytes = resolve_target_bytes(input_size, target)

    if duration is None or duration <= 0:
        msg = "動画の長さを取得できないため、目標サイズからのビットレートを計算できません。"
        raise TargetSizeError(msg)

    total_kbps = (target_bytes * 8) / duration / 1000
    available_kbps = total_kbps * (1 - CONTAINER_OVERHEAD_RATIO)

    audio_kbps = 0
    if audio_enabled:
        try:
            audio_kbps = parse_bitrate(resolve_audio_bitrate_for_budget(audio_bitrate))
        except (TypeError, ValueError) as exc:
            msg = f"オーディオビットレートの値が不正です: {audio_bitrate!r}"
            raise TargetSizeError(msg) from exc

    video_kbps = int(available_kbps - audio_kbps)
    if video_kbps < MIN_VIDEO_BITRATE_KBPS:
        msg = (
            f"目標サイズが小さすぎます。音声 {audio_kbps} kbps を差し引くと "
            f"映像に {max(video_kbps, 0)} kbps しか残らず、"
            f"最低 {MIN_VIDEO_BITRATE_KBPS} kbps を下回ります。"
            "目標サイズを大きくするか、音声ビットレートを下げてください。"
        )
        raise TargetSizeError(msg)

    return TargetBitratePlan(
        target_bytes=target_bytes,
        duration=duration,
        total_kbps=round(total_kbps, 2),
        audio_kbps=audio_kbps,
        video_kbps=video_kbps,
        video_only_bytes=int(video_kbps * 1000 * duration / 8),
    )
