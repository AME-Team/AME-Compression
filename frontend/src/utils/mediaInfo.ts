/**
 * Formatting helpers for the source-media readout.
 *
 * The values come from GET /api/media/info, which fills `bit_rate` (bits per
 * second) and `bit_depth` from backend/ffmpeg.py::get_video_stream_details.
 * Both are optional: a probe that cannot read the stream simply omits them.
 */

/** Format a bits-per-second value the way encoders are usually quoted. */
export function formatBitRate(bitsPerSecond: number | null | undefined): string | null {
  if (bitsPerSecond === null || bitsPerSecond === undefined) return null
  if (!Number.isFinite(bitsPerSecond) || bitsPerSecond <= 0) return null
  if (bitsPerSecond >= 1_000_000) return `${(bitsPerSecond / 1_000_000).toFixed(2)} Mbps`
  if (bitsPerSecond >= 1_000) return `${Math.round(bitsPerSecond / 1_000)} kbps`
  return `${Math.round(bitsPerSecond)} bps`
}

/** Format a colour depth as the label users recognise on media players. */
export function formatBitDepth(bitDepth: number | null | undefined): string | null {
  if (bitDepth === null || bitDepth === undefined) return null
  if (!Number.isFinite(bitDepth) || bitDepth <= 0) return null
  return `${Math.round(bitDepth)}-bit`
}

/** Format a frame rate as the label users see in media players. */
export function formatFrameRate(fps: number | null | undefined): string | null {
  if (fps === null || fps === undefined) return null
  if (!Number.isFinite(fps) || fps <= 0) return null
  return `${Number.parseFloat((Math.round(fps * 100) / 100).toFixed(2))} fps`
}

/** Format a pixel count so the readout matches the resolution presets. */
export function formatResolution(
  width: number | null | undefined,
  height: number | null | undefined,
): string | null {
  if (!width || !height) return null
  if (!Number.isFinite(width) || !Number.isFinite(height)) return null
  return `${Math.round(width)}×${Math.round(height)}`
}
