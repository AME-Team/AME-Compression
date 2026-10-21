"""Unit tests for target-size bitrate planning."""

import pytest
from backend.config import (
    CONTAINER_OVERHEAD_RATIO,
    MIN_VIDEO_BITRATE_KBPS,
    TARGET_SIZE_MAX_MB,
)
from backend.size_target import (
    MB_IN_BYTES,
    SizeTarget,
    TargetSizeError,
    resolve_audio_bitrate_for_budget,
    resolve_target_bitrate,
    resolve_target_bytes,
)


class TestResolveTargetBytes:
    def test_absolute_bytes(self) -> None:
        assert resolve_target_bytes(
            500 * MB_IN_BYTES, SizeTarget(size_bytes=100 * MB_IN_BYTES)
        ) == (100 * MB_IN_BYTES)

    def test_percent_of_input(self) -> None:
        assert resolve_target_bytes(200 * MB_IN_BYTES, SizeTarget(percent=25.0)) == 50 * MB_IN_BYTES

    def test_percent_never_zero(self) -> None:
        tiny = resolve_target_bytes(10, SizeTarget(percent=1.0))
        assert tiny == 1

    def test_percent_below_minimum_is_rejected(self) -> None:
        with pytest.raises(TargetSizeError, match="範囲"):
            resolve_target_bytes(MB_IN_BYTES, SizeTarget(percent=0.5))

    def test_both_given_is_rejected(self) -> None:
        with pytest.raises(TargetSizeError, match="どちらか一方"):
            resolve_target_bytes(MB_IN_BYTES, SizeTarget(size_bytes=MB_IN_BYTES, percent=50.0))

    def test_neither_given_is_rejected(self) -> None:
        with pytest.raises(TargetSizeError, match="指定されていません"):
            resolve_target_bytes(MB_IN_BYTES, SizeTarget())

    def test_percent_out_of_range(self) -> None:
        with pytest.raises(TargetSizeError, match="範囲"):
            resolve_target_bytes(MB_IN_BYTES, SizeTarget(percent=150.0))

    def test_too_small_and_too_large_absolute(self) -> None:
        with pytest.raises(TargetSizeError, match="以上"):
            resolve_target_bytes(MB_IN_BYTES, SizeTarget(size_bytes=0))
        with pytest.raises(TargetSizeError, match="以下"):
            resolve_target_bytes(
                MB_IN_BYTES, SizeTarget(size_bytes=(TARGET_SIZE_MAX_MB + 1) * MB_IN_BYTES)
            )

    def test_unknown_input_size(self) -> None:
        with pytest.raises(TargetSizeError, match="サイズを取得できません"):
            resolve_target_bytes(0, SizeTarget(size_bytes=MB_IN_BYTES))


class TestResolveTargetBitrate:
    def test_absolute_target_subtracts_audio_and_overhead(self) -> None:
        duration = 60.0
        target = 30 * MB_IN_BYTES
        plan = resolve_target_bitrate(
            input_size=100 * MB_IN_BYTES,
            duration=duration,
            audio_bitrate="192k",
            target=SizeTarget(size_bytes=target),
        )

        expected_total = (target * 8) / duration / 1000
        assert plan.target_bytes == target
        assert abs(plan.total_kbps - expected_total) < expected_total * 1e-6
        assert plan.audio_kbps == 192
        expected_video = int(expected_total * (1 - CONTAINER_OVERHEAD_RATIO) - 192)
        assert plan.video_kbps == expected_video
        assert plan.video_only_bytes > 0

    def test_percent_target(self) -> None:
        plan = resolve_target_bitrate(
            input_size=400 * MB_IN_BYTES,
            duration=120.0,
            audio_bitrate="128k",
            target=SizeTarget(percent=50.0),
        )
        assert plan.target_bytes == 200 * MB_IN_BYTES
        assert plan.audio_kbps == 128

    def test_audio_disabled_keeps_full_budget(self) -> None:
        plan = resolve_target_bitrate(
            input_size=100 * MB_IN_BYTES,
            duration=60.0,
            audio_bitrate="192k",
            target=SizeTarget(size_bytes=30 * MB_IN_BYTES),
            audio_enabled=False,
        )
        assert plan.audio_kbps == 0

    def test_target_too_small_for_audio(self) -> None:
        with pytest.raises(TargetSizeError, match="小さすぎます"):
            resolve_target_bitrate(
                input_size=100 * MB_IN_BYTES,
                duration=3600.0,
                audio_bitrate="320k",
                target=SizeTarget(size_bytes=60 * MB_IN_BYTES),
            )

    def test_unknown_duration(self) -> None:
        with pytest.raises(TargetSizeError, match="長さを取得できない"):
            resolve_target_bitrate(
                input_size=100 * MB_IN_BYTES,
                duration=0.0,
                audio_bitrate="192k",
                target=SizeTarget(percent=50.0),
            )

    def test_invalid_audio_bitrate(self) -> None:
        with pytest.raises(TargetSizeError, match="オーディオビットレート"):
            resolve_target_bitrate(
                input_size=100 * MB_IN_BYTES,
                duration=60.0,
                audio_bitrate="not-a-bitrate",
                target=SizeTarget(percent=50.0),
            )

    def test_minimum_video_bitrate_boundary(self) -> None:
        # A 1-minute clip at 1 MB leaves far too little room for video.
        with pytest.raises(TargetSizeError, match=f"最低 {MIN_VIDEO_BITRATE_KBPS}"):
            resolve_target_bitrate(
                input_size=100 * MB_IN_BYTES,
                duration=60.0,
                audio_bitrate="192k",
                target=SizeTarget(size_bytes=MB_IN_BYTES),
            )


class TestResolveAudioBitrateForBudget:
    def test_default_when_unspecified(self) -> None:
        assert resolve_audio_bitrate_for_budget(None) == "192k"

    def test_keeps_supported_bitrate(self) -> None:
        assert resolve_audio_bitrate_for_budget("128k") == "128k"

    def test_bare_numbers_become_kbps(self) -> None:
        # The value reaches FFmpeg as -b:a, where a unit-less number means bits/s.
        assert resolve_audio_bitrate_for_budget(128) == "128k"
        assert resolve_audio_bitrate_for_budget("320") == "320k"
        assert resolve_audio_bitrate_for_budget("192K") == "192k"

    def test_blank_value_falls_back_to_default(self) -> None:
        assert resolve_audio_bitrate_for_budget("") == "192k"

    def test_clamps_to_supported_maximum(self) -> None:
        # The request check and the job check must budget with the same ceiling.
        assert resolve_audio_bitrate_for_budget("999k") == "320k"
