/**
 * Percentage range accepted by the backend for target-size compression.
 * Mirrors TARGET_SIZE_PERCENT_MIN / TARGET_SIZE_PERCENT_MAX in
 * backend/config.py. Keep both sides in sync when the backend range changes.
 */
export const TARGET_SIZE_PERCENT_MIN = 1
export const TARGET_SIZE_PERCENT_MAX = 100

/**
 * UI fallback used when the input is empty or invalid.
 * Matches DEFAULT_SETTINGS.targetSizePercent in frontend/src/profiles.ts.
 */
export const TARGET_SIZE_PERCENT_DEFAULT = 50

/**
 * Parse a percentage typed by the user.
 *
 * Returns null for empty or non-numeric input so the caller can show a
 * validation error instead of silently sending an unintended value.
 */
export function parseTargetPercent(raw: string): number | null {
  const trimmed = raw.trim()
  if (trimmed === '') return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : null
}

/** True when the parsed percentage is inside the range the backend accepts. */
export function isValidTargetPercent(value: number | null): value is number {
  return value !== null && value >= TARGET_SIZE_PERCENT_MIN && value <= TARGET_SIZE_PERCENT_MAX
}

/** Clamp a parsed value into the range the slider can represent. */
export function clampTargetPercent(value: number | null): number {
  if (value === null) return TARGET_SIZE_PERCENT_DEFAULT
  return Math.min(TARGET_SIZE_PERCENT_MAX, Math.max(TARGET_SIZE_PERCENT_MIN, value))
}
