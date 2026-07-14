import { request3 } from './request'
import { toArray, unwrapPayload } from './helpers'

// ============================================================
//  3号后端 — 事件分析 / 语义搜索 / 历史筛选
//  baseURL: http://localhost:8000/api
// ============================================================

// GET /analysis/events — 获取全部事件列表（精简版，不含详情）
export function getAnalysisEvents() {
  return request3.get('/analysis/events')
}

// GET /analysis/event/{eid} — 获取单事件完整详情（含情感、平台、时序、新闻）
export function getAnalysisEventDetail(eid) {
  return request3.get(`/analysis/event/${eid}`)
}

// GET /analysis/event/{eid}/articles — 获取事件关联的全部新闻
export function getAnalysisEventArticles(eid) {
  return request3.get(`/analysis/event/${eid}/articles`)
}

// POST /history/filter — 条件筛选（类别/关键词/时间）
export function filterHistoryEvents(params = {}) {
  return request3.post('/history/filter', {
    category: params.category ?? null,
    keyword: params.keyword ?? null,
    start_time: params.start_time ?? null,
    end_time: params.end_time ?? null,
  })
}

// POST /similar/search — FAISS 语义相似事件检索
export function searchSimilarEvents(query, topK = 5) {
  return request3.post('/similar/search', {
    query,
    top_k: topK,
  })
}

// ============================================================
//  带 mock 兜底的包装函数
// ============================================================

export async function fetchAnalysisEvents() {
  try {
    const payload = await getAnalysisEvents()
    const data = unwrapPayload(payload)
    return toArray(data)
  } catch (error) {
    console.warn('Analysis events API unavailable.', error)
    return []
  }
}

export async function fetchAnalysisEventDetail(eid) {
  try {
    const payload = await getAnalysisEventDetail(eid)
    return unwrapPayload(payload) ?? null
  } catch (error) {
    console.warn('Analysis event detail API unavailable.', error)
    return null
  }
}
