import logging
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request

from ...audio import compress_audio_service
from ...config import COMPRESSION_MODE_CRF, COMPRESSION_MODE_TARGET_SIZE
from ...ffmpeg import get_video_info_safe, resolve_ffmpeg_paths
from ...size_target import (
    SizeTarget,
    TargetSizeError,
    resolve_target_bitrate,
    resolve_target_bytes,
)
from ...video import compress_video_service
from ..job_runner import job_runner

logger = logging.getLogger(__name__)

jobs_bp = Blueprint("jobs", __name__)


class RequestValidationError(Exception):
    """Raised when a job request payload is invalid."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _resolve_target_duration(input_path: str) -> float | None:
    """Return the duration used to validate the target-size bitrate budget.

    Probing is best-effort: an unreadable file or a probe that cannot start
    returns None. The request then reaches the job runner, where
    ``backend/video.py::_resolve_plan`` calls ``resolve_target_bitrate`` again
    and raises the identical ``TargetSizeError`` message, so skipping the
    request-time check never lets an unreachable target slip through silently.
    """
    try:
        _, ffprobe_path = resolve_ffmpeg_paths()
        info = get_video_info_safe(input_path, ffprobe_path)
    except (OSError, ValueError, TypeError, KeyError, IndexError, RuntimeError) as exc:
        # Launching the probe can fail with OSError, and parsing its CSV output
        # raises ValueError/TypeError/KeyError/IndexError on unexpected shapes.
        # None keeps the request alive; the job runner re-checks the budget.
        logger.warning("Could not probe %s for target-size validation: %s", input_path, exc)
        return None
    if not info:
        return None
    duration = info.get("duration")
    if isinstance(duration, bool) or not isinstance(duration, int | float):
        return None
    return float(duration) if duration > 0 else None


def _resolve_target_fields(
    data: dict[str, Any], input_path: str, mode: str
) -> tuple[int | None, float | None]:
    """Validate the size target fields of a video job request.

    The byte target is checked against the input size, and — when ffprobe can
    read the duration — against the minimum video bitrate the encoder needs.
    Rejecting an unreachable target here keeps the UI from starting a job that
    would fail immediately.

    Args:
        data: Raw JSON payload.
        input_path: Existing input file path.
        mode: Requested compression mode.

    Returns:
        ``(target_size_bytes, target_size_percent)``.

    Raises:
        RequestValidationError: If the fields are inconsistent or invalid.
    """
    target_size_bytes = data.get("target_size_bytes")
    target_size_percent = data.get("target_size_percent")

    if mode != COMPRESSION_MODE_TARGET_SIZE:
        if target_size_bytes is not None or target_size_percent is not None:
            msg = (
                "target_size_bytes / target_size_percent require "
                f"compression_mode '{COMPRESSION_MODE_TARGET_SIZE}'"
            )
            raise RequestValidationError(msg)
        return None, None

    if isinstance(target_size_bytes, bool):
        msg = "目標サイズ (バイト) は整数で指定してください。"
        raise RequestValidationError(msg)
    if target_size_bytes is not None and not isinstance(target_size_bytes, int):
        msg = "目標サイズ (バイト) は整数で指定してください。"
        raise RequestValidationError(msg)
    if isinstance(target_size_percent, bool):
        msg = "割合は数値で指定してください。"
        raise RequestValidationError(msg)
    if target_size_percent is not None and not isinstance(target_size_percent, int | float):
        msg = "割合は数値で指定してください。"
        raise RequestValidationError(msg)

    target = SizeTarget(
        size_bytes=target_size_bytes,
        percent=float(target_size_percent) if target_size_percent is not None else None,
    )
    try:
        input_size = Path(input_path).stat().st_size
        resolve_target_bytes(input_size, target)
    except TargetSizeError as exc:
        raise RequestValidationError(str(exc)) from exc
    except OSError as exc:
        msg = "Could not read the input file size"
        raise RequestValidationError(msg) from exc

    duration = _resolve_target_duration(input_path)
    if duration is not None:
        try:
            resolve_target_bitrate(
                input_size=input_size,
                duration=duration,
                audio_bitrate=data.get("audio_bitrate"),
                target=target,
                audio_enabled=bool(data.get("audio_enabled", True)),
            )
        except TargetSizeError as exc:
            # The API returns user-facing Japanese messages verbatim (there is
            # no i18n layer in the backend); the frontend renders `error` as-is.
            raise RequestValidationError(str(exc)) from exc
    return target.size_bytes, target.percent


def _parse_video_request(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a video compression request and normalise its fields.

    Raises:
        RequestValidationError: If any field is missing or out of range.
    """
    input_path = data.get("input_path")
    if not input_path:
        msg = "input_path is required"
        raise RequestValidationError(msg)
    if not Path(input_path).exists():
        msg = f"Input path does not exist: {input_path}"
        raise RequestValidationError(msg, 404)

    max_crf = 63
    max_preset = 13
    crf = data.get("crf")
    if crf is not None and not (0 <= crf <= max_crf):
        msg = f"CRF must be between 0 and {max_crf}"
        raise RequestValidationError(msg)

    preset = data.get("preset")
    if preset is not None and not (0 <= preset <= max_preset):
        msg = f"Preset must be between 0 and {max_preset}"
        raise RequestValidationError(msg)

    compression_mode = data.get("compression_mode", COMPRESSION_MODE_CRF)
    if compression_mode not in (COMPRESSION_MODE_CRF, COMPRESSION_MODE_TARGET_SIZE):
        msg = (
            f"compression_mode must be '{COMPRESSION_MODE_CRF}' or '{COMPRESSION_MODE_TARGET_SIZE}'"
        )
        raise RequestValidationError(msg)

    target_size_bytes, target_size_percent = _resolve_target_fields(
        data, str(input_path), str(compression_mode)
    )
    return {
        "input_path": input_path,
        "crf": crf,
        "preset": preset,
        "compression_mode": compression_mode,
        "target_size_bytes": target_size_bytes,
        "target_size_percent": target_size_percent,
    }


@jobs_bp.route("/video", methods=["POST"])
def start_video_compression() -> tuple[Response, int]:
    """Start a video compression task."""
    data: dict[str, Any] = request.json or {}
    try:
        payload = _parse_video_request(data)
    except RequestValidationError as exc:
        return jsonify({"error": str(exc)}), exc.status

    ffmpeg_path, ffprobe_path = resolve_ffmpeg_paths()

    task_id = job_runner.start_task(
        "video",
        compress_video_service,
        input_path=payload["input_path"],
        output_path=data.get("output_path"),
        crf=payload["crf"],
        preset=payload["preset"],
        audio_bitrate=data.get("audio_bitrate"),
        audio_enabled=data.get("audio_enabled", True),
        max_fps=data.get("max_fps"),
        resolution=data.get("resolution"),
        volume_gain_db=data.get("volume_gain_db"),
        denoise_level=data.get("denoise_level"),
        compression_mode=payload["compression_mode"],
        target_size_bytes=payload["target_size_bytes"],
        target_size_percent=payload["target_size_percent"],
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
    )

    logger.info(
        "Video compression job started: %s -> %s (mode=%s)",
        task_id[:8],
        payload["input_path"],
        payload["compression_mode"],
    )
    return jsonify({"task_id": task_id}), 202


@jobs_bp.route("/audio", methods=["POST"])
def start_audio_compression() -> tuple[Response, int]:
    """Start an audio compression task."""
    data: dict[str, Any] = request.json or {}
    input_path = data.get("input_path")
    if not input_path:
        return jsonify({"error": "input_path is required"}), 400

    if not Path(input_path).exists():
        return jsonify({"error": f"Input path does not exist: {input_path}"}), 404

    ffmpeg_path, ffprobe_path = resolve_ffmpeg_paths()

    task_id = job_runner.start_task(
        "audio",
        compress_audio_service,
        input_path=input_path,
        output_path=data.get("output_path"),
        bitrate=data.get("bitrate"),
        volume_gain_db=data.get("volume_gain_db"),
        denoise_level=data.get("denoise_level"),
        keep_metadata=data.get("keep_metadata", True),
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
    )

    logger.info("Audio compression job started: %s -> %s", task_id[:8], input_path)
    return jsonify({"task_id": task_id}), 202


@jobs_bp.route("", methods=["GET"])
def list_jobs() -> Response:
    """List all compression tasks."""
    return jsonify(job_runner.list_tasks())


@jobs_bp.route("/<task_id>", methods=["GET"])
def get_job_status(task_id: str) -> tuple[Response, int]:
    """Get the status of a specific compression task."""
    task = job_runner.get_task(task_id)
    if not task:
        return jsonify({"error": "Job not found"}), 404

    return (
        jsonify(
            {
                "id": task["id"],
                "status": task["status"],
                "progress": task["progress"],
                "result": task["result"],
                "type": task["type"],
                "filename": task.get("filename", ""),
                "created_at": task.get("created_at"),
                "finished_at": task.get("finished_at"),
            }
        ),
        200,
    )


@jobs_bp.route("/<task_id>", methods=["DELETE"])
def cancel_job(task_id: str) -> tuple[Response, int]:
    """Cancel a specific compression task."""
    logger.info("Cancel requested for job: %s", task_id[:8])
    success = job_runner.cancel_task(task_id)
    if not success:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"status": "cancelling"}), 200
