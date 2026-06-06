import logging
from pathlib import Path
from typing import Any

from flask import Blueprint, Response, jsonify, request

from ...analyzer import analyze_quality
from ...audio import get_audio_info_safe
from ...ffmpeg import resolve_ffmpeg_paths
from ...video import get_video_info_safe
from ...volume import analyze_volume_level

logger = logging.getLogger(__name__)

media_bp = Blueprint("media", __name__)


@media_bp.route("/info", methods=["GET"])
def get_info() -> Response | tuple[Response, int]:
    path = request.args.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    path_obj = Path(path)
    if not path_obj.exists():
        return jsonify({"error": "File not found"}), 404

    logger.info("Getting media info for: %s", path)
    _, ffprobe_path = resolve_ffmpeg_paths()

    info = get_video_info_safe(path_obj, ffprobe_path)
    if info:
        info_dict: dict[str, Any] = info
        info_dict["type"] = "video"
        return jsonify(info_dict)

    info = get_audio_info_safe(path_obj, ffprobe_path)
    if info:
        info_dict = info
        info_dict["type"] = "audio"
        return jsonify(info_dict)

    logger.warning("Unsupported file format: %s", path)
    return jsonify({"error": "Unsupported file format"}), 400


@media_bp.route("/volume-analyze", methods=["POST"])
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

    logger.info("Analyzing volume for: %s", path)
    try:
        ffmpeg_path, _ = resolve_ffmpeg_paths()
        result = analyze_volume_level(path_obj, ffmpeg_path)
        if result["mean_volume"] is not None:
            return jsonify(result)
        else:
            logger.error("Volume analysis returned None for: %s", path)
            return jsonify({"error": "Failed to analyze volume"}), 500
    except Exception as e:
        logger.exception("Volume analysis failed for: %s", path)
        return jsonify({"error": str(e)}), 500


@media_bp.route("/analyze-settings", methods=["POST"])
def analyze_settings() -> Response | tuple[Response, int]:
    """Analyze a media file and return recommended compression settings."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    path = data.get("path")
    if not path:
        return jsonify({"error": "Path is required"}), 400

    path_obj = Path(path)
    if not path_obj.exists():
        return jsonify({"error": "File not found"}), 404

    logger.info("Analyzing optimal settings for: %s", path)
    try:
        _, ffprobe_path = resolve_ffmpeg_paths()
        result = analyze_quality(path_obj, ffprobe_path)
        logger.info("Analysis complete for: %s", path)
        return jsonify(result)
    except Exception as e:
        logger.exception("Quality analysis failed for: %s", path)
        return jsonify({"error": str(e)}), 500
