"""Integration test: real FFmpeg two-pass encode towards a byte target.

The unit tests stub ``_run_ffmpeg``; this test runs the actual encoder so that a
regression in the ``-pass`` / ``-passlogfile`` wiring (or a libsvtav1 build that
ignores those flags) is caught. It is skipped when ffmpeg with libsvtav1 is not
available (e.g. a minimal CI image or Windows runner without SVT-AV1).
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from backend.video import compress_video_service

SAMPLE_SECONDS = 8
# Fixed bitrate budget: independent of how large the generated sample is, and
# comfortably above MIN_VIDEO_BITRATE_KBPS once the audio track is subtracted.
TARGET_KBPS = 1200
OVERSHOOT_TOLERANCE = 1.15


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def _libsvtav1_available() -> bool:
    """Return True when ffmpeg, ffprobe and the libsvtav1 encoder are usable."""
    if FFMPEG is None or FFPROBE is None:
        return False
    probe = subprocess.run(
        [FFMPEG, "-hide_banner", "-h", "encoder=libsvtav1"],
        capture_output=True,
        text=True,
        check=False,
    )
    return "libsvtav1" in probe.stdout


pytestmark = pytest.mark.skipif(
    not _libsvtav1_available(), reason="ffmpeg with libsvtav1 is required"
)


def _passlog_dirs() -> set[str]:
    root = Path(tempfile.gettempdir())
    return {str(path) for path in root.glob("ame_passlog_*") if path.is_dir()}


@pytest.fixture(scope="module")
def sample(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a short clip with video and audio to encode."""
    target = tmp_path_factory.mktemp("source") / "sample.mp4"
    command = [
        str(FFMPEG),
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=640x360:rate=30:duration={SAMPLE_SECONDS}",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=440:duration={SAMPLE_SECONDS}",
        "-c:v",
        "libsvtav1",
        "-crf",
        "35",
        "-preset",
        "12",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-y",
        str(target),
    ]
    subprocess.run(command, check=True, capture_output=True)
    return target


def test_two_pass_encode_reaches_target_size(sample: Path, tmp_path: Path) -> None:
    """A real two-pass encode must land inside the requested size budget."""
    output = tmp_path / "out.mp4"
    target_bytes = int(TARGET_KBPS * 1000 * SAMPLE_SECONDS / 8)
    before = _passlog_dirs()

    result = compress_video_service(
        input_path=str(sample),
        output_path=str(output),
        preset=12,
        audio_bitrate="96k",
        compression_mode="target_size",
        target_size_bytes=target_bytes,
    )

    assert result.is_success, result.error_message
    assert result.compression_mode == "target_size"
    assert result.video_bitrate_kbps > 0
    assert result.target_size_bytes == target_bytes
    produced = output.stat().st_size
    # VBR and container overhead make an exact match impossible, but the encode
    # must respect the budget instead of ignoring the two-pass parameters.
    assert produced <= target_bytes * OVERSHOOT_TOLERANCE
    assert produced >= target_bytes * 0.5
    # The statistics files must not survive the job.
    assert _passlog_dirs() == before
