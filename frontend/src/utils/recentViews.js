const STORAGE_KEY = 'opinion_system_recent_views'
const MAX_RECENT_VIEWS = 20

function normalizeRecord(record) {
  return {
    id: record.id,
    type: record.type,
    title: record.title,
    meta: record.meta,
    viewedAt: record.viewedAt,
    path: record.path,
  }
}

export function getRecentViews() {
  try {
    const rawRecords = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')

    if (!Array.isArray(rawRecords)) {
      return []
    }

    return rawRecords
      .filter((record) => record && record.path)
      .map(normalizeRecord)
      .slice(0, MAX_RECENT_VIEWS)
  } catch {
    return []
  }
}

export function addRecentView(record) {
  if (!record || !record.path) {
    return getRecentViews()
  }

  const nextRecord = normalizeRecord({
    ...record,
    id: record.id ?? record.path,
    viewedAt: record.viewedAt ?? new Date().toISOString(),
  })
  const records = getRecentViews().filter((item) => item.path !== nextRecord.path)
  const nextRecords = [nextRecord, ...records].slice(0, MAX_RECENT_VIEWS)

  localStorage.setItem(STORAGE_KEY, JSON.stringify(nextRecords))
  return nextRecords
}

export function clearRecentViews() {
  localStorage.removeItem(STORAGE_KEY)
  return []
}
