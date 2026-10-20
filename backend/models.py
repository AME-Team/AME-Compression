"""Data models for compression results and progress events.

These models provide a clean interface for returning compression results
and progress information, independent of CLI/GUI/API boundaries.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# Use Forward references or TypeVars to avoid circular imports if needed
ProgressCallback = Callable[[Any], None]
OutputCallback = Callable[[str], None]
CancellationSource = Any


class CompressionStatus(Enum):
    """Status of a compression operation."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VideoCompressionParams:
    """Parameters for video compression.

    Attributes:
        compression_mode: ``"crf"`` (quality target) or ``"target_size"``
            (two-pass VBR towards a byte budget).
        target_size_bytes: Absolute output size target in bytes.
        target_size_percent: Output size target as a percentage of the input
            file size.
    """

    input_path: str | Path
    output_path: str | Path | None = None
    crf: int | None = None
    preset: int | None = None
    audio_bitrate: str | None = None
    audio_enabled: bool = True
    max_fps: int | None = None
    resolution: str | None = None
    volume_gain_db: str | float | None = None
    denoise_level: float | None = None
    compression_mode: str = "crf"
    target_size_bytes: int | None = None
    target_size_percent: float | None = None
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    on_progress: ProgressCallback | None = None
    on_output: OutputCallback | None = None
    cancellation_source: CancellationSource | None = None


@dataclass
class AudioCompressionParams:
    """Parameters for audio compression."""

    input_path: str | Path
    output_path: str | Path | None = None
    bitrate: str | None = None
    volume_gain_db: str | float | None = None
    denoise_level: float | None = None
    keep_metadata: bool = True
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    on_progress: ProgressCallback | None = None
    on_output: OutputCallback | None = None
    cancellation_source: CancellationSource | None = None


@dataclass
class ProgressEvent:
    """Progress event emitted during compression.

    Attributes:
        percent: Progress percentage (0.0 - 100.0)
        current_time: Current playback time in seconds
        total_duration: Total media duration in seconds
        fps: Current frames per second
        speed: Encoding speed multiplier
        frame: Current frame number
        eta: Estimated time remaining in seconds
        status: Current status message
        pass_index: Current encoding pass (1-based, 0 when single pass)
        pass_total: Total number of encoding passes
    """

    percent: float = 0.0
    current_time: float = 0.0
    total_duration: float = 0.0
    fps: float = 0.0
    speed: float = 0.0
    frame: int = 0
    eta: float = 0.0
    status: str = ""
    pass_index: int = 0
    pass_total: int = 0


@dataclass
class CompressionResult:
    """Result of a compression operation.

    Attributes:
        status: Final status of the operation
        input_path: Input file path
        output_path: Output file path (if successful)
        input_size: Input file size in bytes
        output_size: Output file size in bytes (if successful)
        compression_ratio: Compression ratio percentage (if successful)
        duration: Media duration in seconds
        error_message: Error message (if failed)
        metadata: Additional metadata
    """

    status: CompressionStatus
    input_path: str
    output_path: str | None = None
    input_size: int = 0
    output_size: int = 0
    compression_ratio: float = 0.0
    duration: float = 0.0
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=lambda: {})

    @property
    def is_success(self) -> bool:
        """Check if compression was successful."""
        return self.status == CompressionStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        """Check if compression failed."""
        return self.status == CompressionStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Check if compression was cancelled."""
        return self.status == CompressionStatus.CANCELLED


@dataclass
class VideoCompressionResult(CompressionResult):
    """Result of a video compression operation.

    Attributes:
        width: Output video width
        height: Output video height
        fps: Output FPS
        video_codec: Video codec used
        audio_codec: Audio codec used
        crf: CRF value used
        preset: Encoding preset used
        compression_mode: Mode used for the encode
        video_bitrate_kbps: Video bitrate targeted by the two-pass encode
        target_size_bytes: Requested output size (0 when not targeting a size)
        target_size_achieved: Whether the output stayed within the target
    """

    width: int | None = None
    height: int | None = None
    fps: float | None = None
    video_codec: str = ""
    audio_codec: str = ""
    crf: int = 0
    preset: int = 0
    compression_mode: str = "crf"
    video_bitrate_kbps: int = 0
    target_size_bytes: int = 0
    target_size_achieved: bool = False


@dataclass
class AudioCompressionResult(CompressionResult):
    """Result of an audio compression operation.

    Attributes:
        sample_rate: Output sample rate
        channels: Number of channels
        audio_codec: Audio codec used
        bitrate: Audio bitrate
    """

    sample_rate: int | None = None
    channels: int | None = None
    audio_codec: str = ""
    bitrate: str = ""


@dataclass
class VolumeAnalysisResult:
    """Result of volume analysis.

    Attributes:
        mean_volume: Mean volume level in dB
        max_volume: Max volume level in dB
        recommended_gain: Recommended gain adjustment in dB
        target_level: Target volume level in dB
    """

    mean_volume: float | None = None
    max_volume: float | None = None
    recommended_gain: float | None = None
    target_level: float = -23.0

    @property
    def has_data(self) -> bool:
        """Check if analysis has valid data."""
        return self.mean_volume is not None


@dataclass
class MediaInfo:
    """Media information structure.

    Attributes:
        width: Video width (video only)
        height: Video height (video only)
        fps: Video FPS (video only)
        duration: Duration in seconds
        bitrate: Bitrate in bps
        sample_rate: Sample rate in Hz (audio only)
        channels: Number of channels (audio only)
        codec_name: Codec name
        codec_long_name: Full codec name
        format_name: Format name
        metadata: Additional metadata
    """

    width: int | None = None
    height: int | None = None
    fps: float | None = None
    duration: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codec_name: str = ""
    codec_long_name: str = ""
    format_name: str = ""
    metadata: dict[str, Any] = field(default_factory=lambda: {})
