import logging
from typing import Any

from flask import Flask
from flask_cors import CORS

from .blueprints.jobs import jobs_bp
from .blueprints.media import media_bp
from .blueprints.settings import settings_bp
from .config import config_by_name
from .job_runner import job_runner

logger = logging.getLogger(__name__)


def create_app(config_name: str | dict[str, Any] = "dev") -> Flask:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = Flask(__name__)

    if isinstance(config_name, dict):
        app.config.from_mapping(config_name)
    else:
        app.config.from_object(config_by_name[config_name])

    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "app://."]}})

    job_runner.start_cleanup_thread()

    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(media_bp, url_prefix="/api/media")
    app.register_blueprint(settings_bp, url_prefix="/api/settings")

    logger.info("AmeCompression backend started (config=%s)", config_name)
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        methods = rule.methods or set()
        filtered = sorted(methods - {"HEAD", "OPTIONS"})
        logger.info("  %s %s", ", ".join(filtered), rule.rule)

    return app
