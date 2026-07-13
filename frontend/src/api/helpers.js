export function unwrapPayload(payload) {
  return payload?.data ?? payload?.result ?? payload
}

export function hasValue(value) {
  return value !== undefined && value !== null && value !== ''
}

export function valueOrFallback(value, fallback = '') {
  return hasValue(value) ? value : fallback
}

export function toArray(value) {
  return Array.isArray(value) ? value : []
}

export function toNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function toRatio(value, fallback = 0) {
  const number = toNumber(value, fallback)
  if (number < 0) return fallback
  if (number > 1 && number <= 100) return number / 100
  return number <= 1 ? number : fallback
}

export function normalizeTags(value) {
  if (Array.isArray(value)) return value.filter(hasValue)
  if (typeof value === 'string') {
    return value
      .split(/[,\s，、]+/)
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return []
}
