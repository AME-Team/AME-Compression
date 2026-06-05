from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request

from ...audio import get_audio_info_safe
from ...ffmpeg import find_ffmpeg, find_ffprobe
from ...video import get_video_info_safe
from ...volume import analyze_volume_level

media_bp = Blueprint("media", __name__)


def _resolve_ffmpeg_paths() -> tuple[str, str]:
    """Resolve ffmpeg and ffprobe paths, returning safe defaults on failure."""
    try:
        return find_ffmpeg(), find_ffprobe()
    except FileNotFoundError:
        return "ffmpeg", "ffprobe"


@media_bp.route("/media-info", methods=["GET"])
def get_info() -> Response | tuple[Response, int]:
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    path_obj = Path(path)
    if not path_obj.exists():
        return jsonify({"error": "File not found"}), 404

    _, ffprobe_path = _resolve_ffmpeg_paths()

    # Try video info first
    info = get_video_info_safe(path_obj, ffprobe_path)
    if info:
        info_dict: dict[str, Any] = info
        info_dict["type"] = "video"
        return jsonify(info_dict)

    # Try audio info
    info = get_audio_info_safe(path_obj, ffprobe_path)
    if info:
        info_dict = info
        info_dict["type"] = "audio"
        return jsonify(info_dict)

    return jsonify({"error": "Unsupported file format"}), 400


@media_bp.route("/volume/analyze", methods=["POST"])
def analyze_volume_endpoint() -> Response | tuple[Response, int]:
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    path_obj = Path(path)
    if not path_obj.exists():
        return jsonify({"error": "File not found"}), 404

    try:
        ffmpeg_path, _ = _resolve_ffmpeg_paths()
        result = analyze_volume_level(path_obj, ffmpeg_path)
        if result["mean_volume"] is not None:
            return jsonify(result)
        else:
            return jsonify({"error": "Failed to analyze volume"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
