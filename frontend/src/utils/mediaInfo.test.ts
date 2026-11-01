import assert from 'node:assert/strict'
import { test } from 'node:test'
import { formatBitDepth, formatBitRate, formatFrameRate, formatResolution } from './mediaInfo.ts'

void test('formatBitRate switches unit at the Mbps and kbps boundaries', () => {
  assert.equal(formatBitRate(5_420_000), '5.42 Mbps')
  assert.equal(formatBitRate(1_000_000), '1.00 Mbps')
  assert.equal(formatBitRate(192_000), '192 kbps')
  assert.equal(formatBitRate(1_000), '1 kbps')
  assert.equal(formatBitRate(999), '999 bps')
})

void test('formatBitRate rejects values that cannot be shown', () => {
  assert.equal(formatBitRate(null), null)
  assert.equal(formatBitRate(undefined), null)
  assert.equal(formatBitRate(0), null)
  assert.equal(formatBitRate(-5), null)
  assert.equal(formatBitRate(Number.NaN), null)
  assert.equal(formatBitRate(Number.POSITIVE_INFINITY), null)
})

void test('formatBitDepth renders the depth reported by ffprobe', () => {
  assert.equal(formatBitDepth(8), '8-bit')
  assert.equal(formatBitDepth(10), '10-bit')
  assert.equal(formatBitDepth(null), null)
  assert.equal(formatBitDepth(0), null)
  assert.equal(formatBitDepth(Number.NaN), null)
})

void test('formatFrameRate trims trailing zeroes but keeps real decimals', () => {
  assert.equal(formatFrameRate(30), '30 fps')
  assert.equal(formatFrameRate(29.97), '29.97 fps')
  assert.equal(formatFrameRate(24000 / 1001), '23.98 fps')
  assert.equal(formatFrameRate(null), null)
  assert.equal(formatFrameRate(0), null)
  assert.equal(formatFrameRate(Number.NaN), null)
})

void test('formatResolution joins width and height', () => {
  assert.equal(formatResolution(1920, 1080), '1920×1080')
  assert.equal(formatResolution(3840, 2160), '3840×2160')
  assert.equal(formatResolution(null, 1080), null)
  assert.equal(formatResolution(1920, 0), null)
})
