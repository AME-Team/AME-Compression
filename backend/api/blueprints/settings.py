import time
from typing import cast

from flask import Blueprint, Response, jsonify, request

from ...settings import SettingsManager

settings_bp = Blueprint("settings", __name__)
settings_manager = SettingsManager.get_instance()

# NOTE: この許可集合は frontend/src/hooks/useTheme.ts の ThemeMode / ACCENT_COLORS と
# 常に同期させること。フロントエンドは renderer プロセス、バックエンドは別プロセスのため
# 定数を共有できない。片方を変更したら必ず両方を更新する。
VALID_THEME_MODES = {"light", "dark", "system"}
VALID_ACCENT_COLORS = {
    "trust-blue",
    "stable-green",
    "grounded-orange",
    "sophisticated-indigo",
    "clarity-teal",
}


@settings_bp.route("", methods=["GET"])
def get_settings() -> Response:
    # Return all settings or default values
    settings = {
        "language": settings_manager.get("language", "en"),
        "appearance_mode": settings_manager.get("appearance_mode", "system"),
        "accent_color": settings_manager.get("accent_color", "trust-blue"),
        "ffmpeg_path": settings_manager.get("ffmpeg_path", ""),
        "default_output_dir": settings_manager.get("default_output_dir", ""),
        # Add more default settings as needed
    }
    return jsonify(settings)


@settings_bp.route("", methods=["POST"])
def update_settings() -> Response | tuple[Response, int]:
    raw_data = request.json
    if not isinstance(raw_data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    if not raw_data:
        return jsonify({"error": "No data provided"}), 400

    # 実行時の型検証: None は保存せず、残りはすべて文字列であることを保証する。
    # 空文字は ffmpeg_path / default_output_dir のクリア操作として有効なため除外しない。
    data: dict[str, str] = {}
    for key, value in cast("dict[str, object]", raw_data).items():
        if value is None:
            continue
        if not isinstance(value, str):
            return jsonify({"error": f"Setting '{key}' must be a string"}), 400
        data[key] = value

    for key, allowed in (
        ("appearance_mode", VALID_THEME_MODES),
        ("accent_color", VALID_ACCENT_COLORS),
    ):
        value = data.get(key)
        if value is not None and value not in allowed:
            return jsonify({"error": f"Invalid {key}: {value}"}), 400

    settings_manager.update_all(data)

    return jsonify({"status": "success"})


@settings_bp.route("/health", methods=["GET"])
def health_check() -> Response:
    return jsonify({"status": "healthy", "timestamp": time.time(), "version": "1.0.0"})
