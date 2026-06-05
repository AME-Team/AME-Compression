from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request

from ...audio import compress_audio_service
from ...ffmpeg import find_ffmpeg, find_ffprobe
from ...video import compress_video_service
from ..job_runner import job_runner

jobs_bp = Blueprint("jobs", __name__)


def _resolve_ffmpeg_paths() -> tuple[str, str]:
    """Resolve ffmpeg and ffprobe paths, returning safe defaults on failure."""
    try:
        return find_ffmpeg(), find_ffprobe()
    except FileNotFoundError:
        return "ffmpeg", "ffprobe"


@jobs_bp.route("/video", methods=["POST"])
def start_video_compression() -> tuple[Response, int]:
    """Start a video compression task."""
    data: dict[str, Any] = request.json or {}
    input_path = data.get("input_path")
    if not input_path:
        return jsonify({"error": "input_path is required"}), 400

    if not Path(input_path).exists():
        return jsonify({"error": f"Input path does not exist: {input_path}"}), 404

    # Simple validation
    max_crf = 63
    max_preset = 13
    crf = data.get("crf")
    if crf is not None and not (0 <= crf <= max_crf):
        return jsonify({"error": f"CRF must be between 0 and {max_crf}"}), 400

    preset = data.get("preset")
    if preset is not None and not (0 <= preset <= max_preset):
        return jsonify({"error": f"Preset must be between 0 and {max_preset}"}), 400

    ffmpeg_path, ffprobe_path = _resolve_ffmpeg_paths()

    task_id = job_runner.start_task(
        "video",
        compress_video_service,
        input_path=input_path,
        output_path=data.get("output_path"),
        crf=crf,
        preset=preset,
        audio_bitrate=data.get("audio_bitrate"),
        audio_enabled=data.get("audio_enabled", True),
        max_fps=data.get("max_fps"),
        resolution=data.get("resolution"),
        volume_gain_db=data.get("volume_gain_db"),
        denoise_level=data.get("denoise_level"),
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
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

    ffmpeg_path, ffprobe_path = _resolve_ffmpeg_paths()

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
    success = job_runner.cancel_task(task_id)
    if not success:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"status": "cancelling"}), 200
