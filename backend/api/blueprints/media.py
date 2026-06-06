import logging
from pathlib import Path
from typing import Any, cast

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


@media_bp.route("/batch-analyze-settings", methods=["POST"])
def batch_analyze_settings() -> Response | tuple[Response, int]:
    """Analyze multiple media files and return per-file recommended settings."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    raw_paths = data.get("paths")
    if not raw_paths or not isinstance(raw_paths, list):
        return jsonify({"error": "paths must be a non-empty list"}), 400
    paths = [str(p) for p in cast(list[str], raw_paths)]

    logger.info("Batch analyzing %d files", len(paths))
    try:
        _, ffprobe_path = resolve_ffmpeg_paths()
        results: list[dict[str, Any]] = []
        for file_path in paths:
            path_obj = Path(file_path)
            if not path_obj.exists():
                results.append(
                    {
                        "path": file_path,
                        "status": "error",
                        "recommended_crf": 25,
                        "recommend_denoise": False,
                        "denoise_level": None,
                        "bpp": 0.0,
                        "reason": "File not found.",
                        "metadata": {},
                    }
                )
                continue
            result = analyze_quality(path_obj, ffprobe_path)
            result["path"] = file_path
            results.append(result)
        logger.info("Batch analysis complete for %d files", len(paths))
        return jsonify(results)
    except Exception as e:
        logger.exception("Batch quality analysis failed")
        return jsonify({"error": str(e)}), 500
