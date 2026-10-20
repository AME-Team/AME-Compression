"""Video compression functionality.

This module provides both CLI-oriented functions and service-layer functions
for video compression. The service layer functions return structured results
without side effects (print/exit), making them suitable for API and GUI use.

Two compression modes are supported:

* ``crf`` - constant quality in a single pass (the historical behaviour).
* ``target_size`` - two-pass VBR towards a byte budget supplied either as an
  absolute size or as a percentage of the input file size.
"""

import contextlib
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import (
    AUDIO_CODEC,
    COMPRESSION_MODE_TARGET_SIZE,
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_CRF,
    MAX_AUDIO_BITRATE,
    TWO_PASS_FIRST_PASS_SHARE,
    VIDEO_CODEC,
    VIDEO_PRESET,
)
from .ffmpeg import get_video_info_safe
from .models import (
    CompressionStatus,
    ProgressEvent,
    VideoCompressionParams,
    VideoCompressionResult,
    VolumeAnalysisResult,
)
from .progress_handler import (
    ProgressParser,
)
from .size_target import (
    SizeTarget,
    TargetBitratePlan,
    TargetSizeError,
    resolve_target_bitrate,
)
from .utils import (
    calculate_scaled_resolution,
    parse_bitrate,
)
from .volume import (
    analyze_volume_level,
    build_audio_filter,
    resolve_volume_gain,
)

__all__ = [
    "analyze_volume_service",
    "compress_video_service",
    "get_video_info_safe",
]

# Statistics accumulated while an encode runs (average speed / fps reporting).
Stats = dict[str, list[float]]


class CompressionError(RuntimeError):
    """Internal control-flow signal carrying a user-facing failure message."""


@dataclass(frozen=True)
class PassProgress:
    """Where a single FFmpeg invocation sits inside the whole job.

    Attributes:
        offset: Overall progress (%) at which this invocation starts.
        span: Share of the overall progress (%) this invocation covers.
        index: 1-based pass number (0 for single-pass encodes).
        total: Total number of passes.
    """

    offset: float = 0.0
    span: float = 100.0
    index: int = 0
    total: int = 0

    def map_event(self, event: ProgressEvent) -> ProgressEvent:
        """Map a per-pass progress event onto the overall job progress."""
        event.percent = self.offset + (event.percent * self.span / 100)
        event.pass_index = self.index
        event.pass_total = self.total
        return event


@dataclass(frozen=True)
class EncodeOutcome:
    """Result of running the encode command(s) for one job.

    Attributes:
        exit_code: Last FFmpeg exit code, or ``None`` when cancelled.
        scaled_resolution: Resolution of the output, if it was scaled.
        label: Human-readable name of the step that produced ``exit_code``.
    """

    exit_code: int | None
    scaled_resolution: tuple[int, int] | None
    label: str = "FFmpeg"


@dataclass
class JobContext:
    """Everything the encoder needs to know about the source file.

    Attributes:
        video_info: Probed source information.
        input_size: Size of the input file in bytes.
        total_duration: Media duration in seconds.
        stats: Mutable accumulator for average fps / speed.
        plan: Resolved bitrate budget when targeting a size, else ``None``.
    """

    video_info: dict[str, Any]
    input_size: int
    total_duration: float
    stats: Stats = field(
        default_factory=lambda: {"fps_list": [], "speed_list": [], "frame_list": []}
    )
    plan: TargetBitratePlan | None = None


def format_bitrate(bitrate: int | float | str | None) -> str:
    """Format bitrate to human readable string."""
    if bitrate is None:
        return "Unknown"
    try:
        bitrate = int(bitrate)
        if bitrate >= 1000000:
            return f"{bitrate / 1000000:.2f} Mbps"
        elif bitrate >= 1000:
            return f"{bitrate / 1000:.0f} kbps"
        else:
            return f"{bitrate} bps"
    except (ValueError, TypeError):
        return "Unknown"


def format_duration(seconds: float | str | None) -> str:
    """Format duration seconds to HH:MM:SS.ms format."""
    if seconds is None:
        return "Unknown"
    try:
        seconds = float(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{minutes:02d}:{secs:06.3f}"
    except (ValueError, TypeError):
        return "Unknown"


def format_file_size(size_bytes: float | str | None) -> str:
    """Format file size to human readable string."""
    if size_bytes is None:
        return "Unknown"
    try:
        size_bytes = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    except (ValueError, TypeError):
        return "Unknown"


def _get_scaled_resolution(
    params: VideoCompressionParams, video_info: dict[str, Any]
) -> tuple[int, int] | None:
    """Calculate scaled resolution based on params and video info."""
    w_val = video_info.get("width")
    h_val = video_info.get("height")
    original_width = int(w_val) if w_val is not None else None
    original_height = int(h_val) if h_val is not None else None

    custom_max_width = None
    custom_max_height = None
    if params.resolution:
        with contextlib.suppress(ValueError):
            res_parts = params.resolution.lower().split("x")
            if len(res_parts) == 2:
                custom_max_width = int(res_parts[0])
                custom_max_height = int(res_parts[1])

    if original_width is not None and original_height is not None:
        return calculate_scaled_resolution(
            original_width, original_height, custom_max_width, custom_max_height
        )
    return None


def _build_video_filters(params: VideoCompressionParams, video_info: dict[str, Any]) -> list[str]:
    """Build the filter list shared by every compression mode."""
    scaled_res = _get_scaled_resolution(params, video_info)
    video_filters: list[str] = []
    if scaled_res:
        video_filters.append(f"scale={scaled_res[0]}:{scaled_res[1]}")
    if params.max_fps is not None:
        video_filters.append(f"fps={params.max_fps}")
    return video_filters


def _resolve_audio_bitrate(params: VideoCompressionParams) -> str:
    """Return the effective audio bitrate, clamped to the supported maximum."""
    audio_bitrate = (
        params.audio_bitrate if params.audio_bitrate is not None else DEFAULT_AUDIO_BITRATE
    )
    if parse_bitrate(audio_bitrate) > MAX_AUDIO_BITRATE:
        return f"{MAX_AUDIO_BITRATE}k"
    return audio_bitrate


def _prepare_audio_args(params: VideoCompressionParams) -> list[str]:
    """Prepare FFmpeg audio arguments."""
    if not params.audio_enabled:
        return ["-an"]

    input_path = Path(params.input_path)
    audio_bitrate = _resolve_audio_bitrate(params)

    # Resolve volume gain
    gain_db = resolve_volume_gain(params.volume_gain_db, input_path, params.ffmpeg_path)

    args: list[str] = []
    audio_filter = build_audio_filter(gain_db, params.denoise_level)
    if audio_filter:
        args.extend(["-af", audio_filter])
    args.extend(["-c:a", AUDIO_CODEC, "-b:a", audio_bitrate])
    return args


def _video_codec_args(params: VideoCompressionParams, video_kbps: int | None) -> list[str]:
    """Build codec arguments for CRF (``video_kbps is None``) or VBR encoding."""
    preset = params.preset if params.preset is not None else VIDEO_PRESET
    if video_kbps is None:
        crf = params.crf if params.crf is not None else DEFAULT_CRF
        return ["-c:v", VIDEO_CODEC, "-crf", str(crf), "-b:v", "0", "-preset", str(preset)]
    return ["-c:v", VIDEO_CODEC, "-b:v", f"{video_kbps}k", "-preset", str(preset)]


def _prepare_video_command(
    params: VideoCompressionParams,
    video_info: dict[str, Any],
) -> tuple[list[str], tuple[int, int] | None]:
    """Prepare the single-pass (CRF) FFmpeg command for video compression."""
    input_path = Path(params.input_path)
    output_path = Path(params.output_path) if params.output_path else None

    scaled_res = _get_scaled_resolution(params, video_info)

    cmd = [params.ffmpeg_path, "-i", str(input_path), "-y"]

    video_filters = _build_video_filters(params, video_info)
    if video_filters:
        cmd.extend(["-vf", ",".join(video_filters)])

    cmd.extend(_video_codec_args(params, None))
    cmd.extend(_prepare_audio_args(params))
    cmd.append(str(output_path))
    return cmd, scaled_res


def _prepare_two_pass_commands(
    params: VideoCompressionParams,
    video_info: dict[str, Any],
    plan: TargetBitratePlan,
    passlogfile: Path,
) -> tuple[list[str], list[str], tuple[int, int] | None]:
    """Prepare the pass 1 / pass 2 FFmpeg commands for a target-size encode.

    Pass 1 analyses the clip (video only, output discarded) and writes the
    statistics file consumed by pass 2. Both passes must use the same filters
    and encoder settings, otherwise the statistics do not apply.

    Args:
        params: Compression parameters.
        video_info: Probed source information.
        plan: Resolved bitrate budget.
        passlogfile: Path prefix for FFmpeg's two-pass statistics files.

    Returns:
        A tuple of ``(pass1_command, pass2_command, scaled_resolution)``.
    """
    input_path = Path(params.input_path)
    output_path = Path(params.output_path) if params.output_path else None
    scaled_res = _get_scaled_resolution(params, video_info)
    video_filters = _build_video_filters(params, video_info)

    def _base(pass_index: int) -> list[str]:
        cmd = [params.ffmpeg_path, "-i", str(input_path), "-y"]
        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])
        cmd.extend(_video_codec_args(params, plan.video_kbps))
        cmd.extend(["-pass", str(pass_index), "-passlogfile", str(passlogfile)])
        return cmd

    pass1 = _base(1)
    pass1.extend(["-an", "-sn", "-dn", "-f", "null", "-"])

    pass2 = _base(2)
    pass2.extend(["-sn", "-dn"])
    pass2.extend(_prepare_audio_args(params))
    pass2.append(str(output_path))
    return pass1, pass2, scaled_res


def _handle_video_progress(
    line: str,
    params: VideoCompressionParams,
    parser: ProgressParser,
    stats: Stats,
    progress: PassProgress,
) -> None:
    """Handle a single line of output from FFmpeg."""
    event = parser.parse_line(line)
    if event:
        if event.fps > 0:
            stats["fps_list"].append(event.fps)
            stats["speed_list"].append(event.speed)
            stats["frame_list"].append(float(event.frame))
        if params.on_progress:
            params.on_progress(progress.map_event(event))
    elif params.on_output:
        params.on_output(line)


def _run_ffmpeg(
    cmd: list[str],
    params: VideoCompressionParams,
    stats: Stats,
    total_duration: float,
    progress: PassProgress | None = None,
) -> int | None:
    """Run one FFmpeg invocation while streaming progress.

    Args:
        cmd: Full command line.
        params: Compression parameters (progress/cancellation callbacks).
        stats: Mutable statistics accumulator.
        total_duration: Media duration used for progress calculation.
        progress: Progress mapping for this invocation (None = whole job).

    Returns:
        The process exit code, or ``None`` when cancellation was requested.
    """
    mapping = progress if progress is not None else PassProgress()
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        encoding="utf-8",
        errors="replace",
    )
    try:
        parser = ProgressParser(total_duration)
        parser.set_start_time(time.time())
        if process.stdout:
            for line in process.stdout:
                if params.cancellation_source and params.cancellation_source.is_cancelled:
                    process.terminate()
                    return None
                _handle_video_progress(line, params, parser, stats, mapping)
        process.wait()
        return process.returncode
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


def _remove_passlog(passlogfile: Path) -> None:
    """Delete the FFmpeg two-pass statistics files (best effort)."""
    parent = passlogfile.parent
    prefix = passlogfile.name
    if not parent.is_dir():
        return
    for candidate in parent.glob(f"{prefix}*"):
        with contextlib.suppress(OSError):
            candidate.unlink()


def _average(values: list[float]) -> float:
    """Return the arithmetic mean, or 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0


def _resolve_plan(
    params: VideoCompressionParams, input_size: int, total_duration: float
) -> TargetBitratePlan:
    """Resolve the two-pass bitrate plan for a target-size request."""
    return resolve_target_bitrate(
        input_size=input_size,
        duration=total_duration,
        audio_bitrate=_resolve_audio_bitrate(params),
        target=SizeTarget(
            size_bytes=params.target_size_bytes,
            percent=params.target_size_percent,
        ),
        audio_enabled=params.audio_enabled,
    )


def _build_context(params: VideoCompressionParams) -> JobContext:
    """Validate the input and build the job context.

    Raises:
        CompressionError: If the input cannot be compressed.
    """
    input_path = Path(params.input_path)
    if not input_path.exists():
        msg = f"Input file '{input_path}' does not exist"
        raise CompressionError(msg)

    if not params.output_path:
        params.output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"

    video_info = get_video_info_safe(input_path, params.ffprobe_path)
    if not video_info:
        msg = "Could not retrieve video information"
        raise CompressionError(msg)

    ctx = JobContext(
        video_info=video_info,
        input_size=input_path.stat().st_size,
        total_duration=video_info["duration"] or 0,
    )

    if params.compression_mode == COMPRESSION_MODE_TARGET_SIZE:
        try:
            ctx.plan = _resolve_plan(params, ctx.input_size, ctx.total_duration)
        except TargetSizeError as exc:
            raise CompressionError(str(exc)) from exc
    return ctx


def _encode_single_pass(params: VideoCompressionParams, ctx: JobContext) -> EncodeOutcome:
    """Encode with CRF in one pass."""
    cmd, scaled_res = _prepare_video_command(params, ctx.video_info)
    code = _run_ffmpeg(cmd, params, ctx.stats, ctx.total_duration)
    return EncodeOutcome(exit_code=code, scaled_resolution=scaled_res)


def _encode_two_pass(params: VideoCompressionParams, ctx: JobContext) -> EncodeOutcome:
    """Encode towards a bitrate budget with two passes (VBR)."""
    if ctx.plan is None:
        msg = "two-pass encode requested without a bitrate plan"
        raise CompressionError(msg)

    passlog_dir = Path(tempfile.mkdtemp(prefix="ame_passlog_"))
    passlogfile = passlog_dir / "pass"
    # Pass 1 only analyses the clip and runs much faster than the real encode, so
    # its fps/speed would skew the averages reported for the job; keep them apart.
    analysis_stats: Stats = {"fps_list": [], "speed_list": [], "frame_list": []}
    try:
        pass1, pass2, scaled_res = _prepare_two_pass_commands(
            params, ctx.video_info, ctx.plan, passlogfile
        )
        code = _run_ffmpeg(
            pass1,
            params,
            analysis_stats,
            ctx.total_duration,
            PassProgress(offset=0.0, span=TWO_PASS_FIRST_PASS_SHARE, index=1, total=2),
        )
        if code is None or code != 0:
            return EncodeOutcome(code, scaled_res, label="パス 1 (解析)")
        code = _run_ffmpeg(
            pass2,
            params,
            ctx.stats,
            ctx.total_duration,
            PassProgress(
                offset=TWO_PASS_FIRST_PASS_SHARE,
                span=100.0 - TWO_PASS_FIRST_PASS_SHARE,
                index=2,
                total=2,
            ),
        )
        return EncodeOutcome(code, scaled_res, label="パス 2 (本エンコード)")
    finally:
        _remove_passlog(passlogfile)
        with contextlib.suppress(OSError):
            passlog_dir.rmdir()


def _success_result(
    params: VideoCompressionParams,
    ctx: JobContext,
    outcome: EncodeOutcome,
    output_size: int,
) -> VideoCompressionResult:
    """Build the success result shared by both compression modes."""
    output_path = params.output_path
    scaled_res = outcome.scaled_resolution
    plan = ctx.plan
    return VideoCompressionResult(
        status=CompressionStatus.SUCCESS,
        input_path=str(params.input_path),
        output_path=str(output_path) if output_path else None,
        input_size=ctx.input_size,
        output_size=output_size,
        compression_ratio=(1 - output_size / ctx.input_size) * 100 if ctx.input_size else 0.0,
        duration=ctx.total_duration,
        width=scaled_res[0] if scaled_res else ctx.video_info.get("width"),
        height=scaled_res[1] if scaled_res else ctx.video_info.get("height"),
        fps=params.max_fps or ctx.video_info.get("fps"),
        video_codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC if params.audio_enabled else "",
        crf=params.crf if params.crf is not None else DEFAULT_CRF,
        preset=params.preset if params.preset is not None else VIDEO_PRESET,
        compression_mode=params.compression_mode,
        video_bitrate_kbps=plan.video_kbps if plan else 0,
        target_size_bytes=plan.target_bytes if plan else 0,
        target_size_achieved=output_size <= plan.target_bytes if plan else False,
        metadata={
            "avg_fps": _average(ctx.stats["fps_list"]),
            "avg_speed": _average(ctx.stats["speed_list"]),
            "total_kbps": plan.total_kbps if plan else 0.0,
            "audio_kbps": plan.audio_kbps if plan else 0,
            "video_only_bytes": plan.video_only_bytes if plan else 0,
        },
    )


def _cancelled_result(params: VideoCompressionParams, ctx: JobContext) -> VideoCompressionResult:
    """Build the result returned when a job is cancelled mid-encode."""
    return VideoCompressionResult(
        status=CompressionStatus.CANCELLED,
        input_path=str(params.input_path),
        output_path=str(params.output_path),
        input_size=ctx.input_size,
        duration=ctx.total_duration,
    )


def _failure(message: str, input_path: Path) -> VideoCompressionResult:
    """Build a failed result with a user-facing message."""
    return VideoCompressionResult(
        status=CompressionStatus.FAILED,
        input_path=str(input_path),
        error_message=message,
    )


def _discard_output(params: VideoCompressionParams) -> None:
    """Remove a partially written output file (best effort).

    A cancelled or failed encode leaves a truncated container behind; keeping it
    would let the user mistake a broken file for a successful result.
    """
    if not params.output_path:
        return
    output_path = Path(params.output_path)
    input_path = Path(params.input_path)
    # Never delete the source: a caller may (accidentally) point the output at it.
    if output_path.resolve() == input_path.resolve():
        return
    with contextlib.suppress(OSError):
        output_path.unlink(missing_ok=True)


def _finalize(
    params: VideoCompressionParams, ctx: JobContext, outcome: EncodeOutcome
) -> VideoCompressionResult:
    """Turn an encode outcome into the final result.

    Raises:
        CompressionError: If the encode did not produce a usable output.
    """
    if outcome.exit_code is None:
        _discard_output(params)
        return _cancelled_result(params, ctx)
    if outcome.exit_code != 0:
        _discard_output(params)
        msg = (
            f"{outcome.label} が異常終了しました (exit code {outcome.exit_code})。"
            "出力先の空き容量、入力ファイルの破損、FFmpeg のコーデック対応を確認してください。"
        )
        raise CompressionError(msg)

    if params.output_path is None:
        msg = "output path was not resolved before encoding"
        raise CompressionError(msg)
    output_path = Path(params.output_path)
    if not output_path.exists():
        msg = "FFmpeg finished but no output file was produced"
        raise CompressionError(msg)
    return _success_result(params, ctx, outcome, output_path.stat().st_size)


def compress_video_service(**kwargs: Any) -> VideoCompressionResult:
    """Compress video using FFmpeg with AV1 codec (service layer)."""
    # kwargs are caller-supplied (API / CLI), so validate the path before the
    # dataclass is built: a None here would otherwise raise TypeError in Path().
    if not kwargs.get("input_path"):
        return VideoCompressionResult(
            status=CompressionStatus.FAILED,
            input_path="",
            error_message="input_path is required",
        )

    params = VideoCompressionParams(**kwargs)
    input_path = Path(params.input_path)
    try:
        ctx = _build_context(params)
        outcome = (
            _encode_single_pass(params, ctx) if ctx.plan is None else _encode_two_pass(params, ctx)
        )
        return _finalize(params, ctx, outcome)
    except CompressionError as exc:
        return _failure(str(exc), input_path)
    except Exception as exc:
        # KeyboardInterrupt / SystemExit derive from BaseException, so they are
        # not caught here; every other failure becomes a user-facing message.
        return _failure(str(exc), input_path)


def analyze_volume_service(
    input_path: str | Path,
    ffmpeg_path: str = "ffmpeg",
) -> VolumeAnalysisResult:
    """Analyze volume level of media file (service layer).

    Args:
        input_path: Input media file path
        ffmpeg_path: Path to ffmpeg executable

    Returns:
        VolumeAnalysisResult with volume information
    """
    input_path = Path(input_path)

    if not input_path.exists():
        return VolumeAnalysisResult(
            mean_volume=None,
            max_volume=None,
            recommended_gain=None,
            target_level=-23.0,
        )

    volume_info = analyze_volume_level(input_path, ffmpeg_path)

    return VolumeAnalysisResult(
        mean_volume=volume_info["mean_volume"],
        max_volume=volume_info["max_volume"],
        recommended_gain=volume_info["recommended_gain"],
        target_level=-23.0,
    )
