from backend.analyzer import analyze_audio_quality, analyze_quality, calculate_bpp


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
