from typing import Any

from backend.analyzer import analyze_audio_quality, analyze_quality, calculate_bpp
from pytest import MonkeyPatch


class TestCalculateBpp:
    def test_normal_video(self) -> None:
        bpp = calculate_bpp(1920, 1080, 30, 5_000_000)
        assert isinstance(bpp, float)
        assert bpp > 0

    def test_zero_bitrate(self) -> None:
        assert calculate_bpp(1920, 1080, 30, 0) == 0.0

    def test_zero_fps(self) -> None:
        assert calculate_bpp(1920, 1080, 0, 5_000_000) == 0.0

    def test_zero_resolution(self) -> None:
        assert calculate_bpp(0, 1080, 30, 5_000_000) == 0.0

    def test_known_value(self) -> None:
        bpp = calculate_bpp(1920, 1080, 30, 4_976_640)
        assert abs(bpp - 0.08) < 0.01


class TestAnalyzeQuality:
    def test_nonexistent_file(self) -> None:
        result = analyze_quality("/nonexistent/file.mp4")
        assert result["status"] == "error"

    def test_returns_expected_keys(self) -> None:
        result = analyze_quality("/nonexistent/file.mp4")
        for key in [
            "status",
            "recommended_crf",
            "recommend_denoise",
            "denoise_level",
            "bpp",
            "reason",
            "metadata",
        ]:
            assert key in result

    def test_recommended_crf_in_valid_range(self) -> None:
        result = analyze_quality("/nonexistent/file.mp4")
        assert 0 <= result["recommended_crf"] <= 63

    def test_error_status_for_nonexistent(self) -> None:
        result = analyze_quality("/nonexistent/file.mp4")
        assert result["bpp"] == 0.0
        assert result["recommend_denoise"] is False
        assert result["denoise_level"] is None
        assert result["metadata"] == {}

    def test_denoise_not_recommended_for_error(self) -> None:
        result = analyze_quality("/nonexistent/file.mp4")
        assert result["recommend_denoise"] is False

    def test_analyze_quality_success(self, monkeypatch: MonkeyPatch) -> None:
        mock_meta = {
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "duration": 60.0,
            "bit_rate": 5000000,
            "codec_name": "h264",
        }

        def mock_extract(*_args: object, **_kwargs: object) -> dict[str, Any]:
            return mock_meta

        def mock_exists(*_args: object, **_kwargs: object) -> bool:
            return True

        monkeypatch.setattr("backend.analyzer._extract_video_metadata", mock_extract)
        monkeypatch.setattr("pathlib.Path.exists", mock_exists)
        monkeypatch.setattr("pathlib.Path.is_file", mock_exists)

        result = analyze_quality("/dummy/path.mp4")
        assert result["status"] == "success"
        assert 0 <= result["recommended_crf"] <= 63
        assert isinstance(result["recommend_denoise"], bool)


class TestAnalyzeAudioQuality:
    def test_nonexistent_file(self) -> None:
        result = analyze_audio_quality("/nonexistent/file.mp3")
        assert result["status"] == "error"

    def test_returns_expected_keys(self) -> None:
        result = analyze_audio_quality("/nonexistent/file.mp3")
        for key in [
            "status",
            "recommended_bitrate",
            "source_bitrate_kbps",
            "recommended_crf",
            "recommend_denoise",
            "denoise_level",
            "recommended_volume_gain",
            "bpp",
            "reason",
            "metadata",
        ]:
            assert key in result

    def test_default_values_for_error(self) -> None:
        result = analyze_audio_quality("/nonexistent/file.mp3")
        assert result["recommended_bitrate"] == 192
        assert result["recommended_crf"] is None
        assert result["recommend_denoise"] is None
        assert result["denoise_level"] is None
        assert result["recommended_volume_gain"] is None
        assert result["bpp"] is None
        assert result["metadata"] == {}

    def test_analyze_audio_quality_success(self, monkeypatch: MonkeyPatch) -> None:
        # Mock detailed media info
        mock_info = {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "bit_rate": "256000",
                    "sample_rate": "44100",
                    "channels": 2,
                }
            ],
            "format": {
                "bit_rate": "256000",
                "duration": "120.0",
            },
        }

        def mock_info_func(*_args: object, **_kwargs: object) -> dict[str, Any]:
            return mock_info

        def mock_volume_func(*_args: object, **_kwargs: object) -> dict[str, Any]:
            return {"recommended_gain": -1.5}

        def mock_ffmpeg_func(*_args: object, **_kwargs: object) -> str:
            return "/dummy/ffmpeg"

        def mock_exists(*_args: object, **_kwargs: object) -> bool:
            return True

        monkeypatch.setattr(
            "backend.analyzer.get_detailed_media_info",
            mock_info_func,
        )
        monkeypatch.setattr(
            "backend.analyzer.analyze_volume_level",
            mock_volume_func,
        )
        monkeypatch.setattr(
            "backend.analyzer.find_ffmpeg",
            mock_ffmpeg_func,
        )
        monkeypatch.setattr(
            "pathlib.Path.exists",
            mock_exists,
        )
        monkeypatch.setattr(
            "pathlib.Path.is_file",
            mock_exists,
        )

        result = analyze_audio_quality("/dummy/path.mp3")
        assert result["status"] == "success"
        assert result["recommended_bitrate"] == 256
        assert result["source_bitrate_kbps"] == 256
        assert result["recommended_volume_gain"] == -1.5
        assert result["recommended_crf"] is None
        assert result["recommend_denoise"] is None
        assert result["denoise_level"] is None
        assert result["bpp"] is None
        assert "mp3" in result["reason"]
