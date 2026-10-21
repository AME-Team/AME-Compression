import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  TARGET_SIZE_PERCENT_DEFAULT,
  TARGET_SIZE_PERCENT_MAX,
  TARGET_SIZE_PERCENT_MIN,
  clampTargetPercent,
  isValidTargetPercent,
  parseTargetPercent,
} from './targetSize.ts'

void test('range constants match the backend contract', () => {
  assert.equal(TARGET_SIZE_PERCENT_MIN, 1)
  assert.equal(TARGET_SIZE_PERCENT_MAX, 100)
  assert.equal(TARGET_SIZE_PERCENT_DEFAULT, 50)
})

void test('parseTargetPercent accepts integers and decimals', () => {
  assert.equal(parseTargetPercent('50'), 50)
  assert.equal(parseTargetPercent(' 37 '), 37)
  assert.equal(parseTargetPercent('12.5'), 12.5)
})

void test('parseTargetPercent rejects empty and non-numeric input', () => {
  assert.equal(parseTargetPercent(''), null)
  assert.equal(parseTargetPercent('   '), null)
  assert.equal(parseTargetPercent('abc'), null)
  assert.equal(parseTargetPercent('12,5'), null)
})

void test('isValidTargetPercent enforces the 1-100 range', () => {
  assert.equal(isValidTargetPercent(1), true)
  assert.equal(isValidTargetPercent(100), true)
  assert.equal(isValidTargetPercent(12.5), true)
  assert.equal(isValidTargetPercent(0), false)
  assert.equal(isValidTargetPercent(100.5), false)
  assert.equal(isValidTargetPercent(null), false)
})

void test('clampTargetPercent keeps the slider inside its range', () => {
  assert.equal(clampTargetPercent(null), 50)
  assert.equal(clampTargetPercent(0), 1)
  assert.equal(clampTargetPercent(150), 100)
  assert.equal(clampTargetPercent(42), 42)
  assert.equal(clampTargetPercent(12.5), 12.5)
})
