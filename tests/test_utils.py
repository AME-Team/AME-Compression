from pathlib import Path

from backend.utils import (
    calculate_scaled_resolution,
    format_time,
    get_file_type,
    parse_bitrate,
)


class TestFormatTime:
    def test_zero(self) -> None:
        assert format_time(0) == "00:00.0"

    def test_seconds_only(self) -> None:
        assert format_time(45.5) == "00:45.5"

    def test_minutes_and_seconds(self) -> None:
        assert format_time(125.3) == "02:05.3"

    def test_large_value(self) -> None:
        assert format_time(3661.0) == "61:01.0"

    def test_exact_minute(self) -> None:
        assert format_time(60.0) == "01:00.0"


class TestGetFileType:
    def test_video_mp4(self) -> None:
        assert get_file_type("video.mp4") == "video"

    def test_video_mkv(self) -> None:
        assert get_file_type("movie.mkv") == "video"

    def test_video_avi(self) -> None:
        assert get_file_type("clip.avi") == "video"

    def test_video_mov(self) -> None:
        assert get_file_type("film.mov") == "video"

    def test_video_webm(self) -> None:
        assert get_file_type("video.webm") == "video"

    def test_video_case_insensitive(self) -> None:
        assert get_file_type("video.MP4") == "video"

    def test_audio_mp3(self) -> None:
        assert get_file_type("song.mp3") == "audio"

    def test_audio_wav(self) -> None:
        assert get_file_type("track.wav") == "audio"

    def test_audio_flac(self) -> None:
        assert get_file_type("audio.flac") == "audio"

    def test_audio_case_insensitive(self) -> None:
        assert get_file_type("song.MP3") == "audio"

    def test_unknown(self) -> None:
        assert get_file_type("document.pdf") == "unknown"

    def test_no_extension(self) -> None:
        assert get_file_type("noext") == "unknown"

    def test_path_object(self) -> None:
        assert get_file_type(Path("video.mp4")) == "video"


class TestParseBitrate:
    def test_with_k_suffix(self) -> None:
        assert parse_bitrate("192k") == 192

    def test_with_k_upper(self) -> None:
        assert parse_bitrate("320K") == 320

    def test_with_m_suffix(self) -> None:
        assert parse_bitrate("1m") == 1000

    def test_plain_number(self) -> None:
        assert parse_bitrate("128") == 128

    def test_with_whitespace(self) -> None:
        assert parse_bitrate("  256k  ") == 256

    def test_decimal_m_suffix(self) -> None:
        """Fractional megabit values convert via float math in parse_bitrate."""
        assert parse_bitrate("1.5m") == 1500

    def test_zero(self) -> None:
        """Zero kbps is a valid boundary value for parse_bitrate."""
        assert parse_bitrate("0k") == 0


class TestCalculateScaledResolution:
    def test_no_scaling_needed(self) -> None:
        assert calculate_scaled_resolution(1920, 1080) is None

    def test_no_scaling_exact_max(self) -> None:
        assert calculate_scaled_resolution(3840, 2160) is None

    def test_scaling_width_exceeds(self) -> None:
        result = calculate_scaled_resolution(7680, 2160)
        assert result is not None
        w, h = result
        assert w <= 3840
        assert h <= 2160
        assert w % 2 == 0
        assert h % 2 == 0

    def test_scaling_height_exceeds(self) -> None:
        result = calculate_scaled_resolution(1920, 4320)
        assert result is not None
        w, h = result
        assert w <= 3840
        assert h <= 2160
        assert w % 2 == 0
        assert h % 2 == 0

    def test_scaling_both_exceed(self) -> None:
        result = calculate_scaled_resolution(7680, 4320)
        assert result is not None
        w, h = result
        assert w <= 3840
        assert h <= 2160
        assert w % 2 == 0
        assert h % 2 == 0

    def test_custom_max(self) -> None:
        result = calculate_scaled_resolution(3840, 2160, max_width=1920, max_height=1080)
        assert result is not None
        w, h = result
        assert w <= 1920
        assert h <= 1080

    def test_aspect_ratio_preserved(self) -> None:
        orig_ratio = 7680 / 4320
        result = calculate_scaled_resolution(7680, 4320)
        assert result is not None
        w, h = result
        scaled_ratio = w / h
        assert abs(orig_ratio - scaled_ratio) < 0.05

    def test_minimum_resolution(self) -> None:
        result = calculate_scaled_resolution(1, 1)
        assert result is None
