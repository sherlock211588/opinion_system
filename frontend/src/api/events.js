import request from './request'
import { eventDetailMock } from '@/mock/eventData'
import { hotEvents as mockHotEvents } from '@/data/mockOpinion'
import { newsDetailPreviewArticles } from '@/mock/newsDetailMock'
import { normalizeTags, toArray, toNumber, toRatio, unwrapPayload, valueOrFallback } from './helpers'

const sentimentTypeMap = {
  positive: 'positive',
  neutral: 'neutral',
  negative: 'risk',
  risk: 'risk',
}

const sentimentLabelMap = {
  positive: '正面',
  neutral: '中性',
  negative: '负面',
}

function normalizeSentimentDistribution(value = {}) {
  const source = value && typeof value === 'object' && !Array.isArray(value) ? value : {}
  return {
    positive: toRatio(source.positive, 0),
    negative: toRatio(source.negative, 0),
    neutral: toRatio(source.neutral, 0),
  }
}

function normalizeTimeseries(value = []) {
  return toArray(value)
    .map((item) => ({
      time: valueOrFallback(item?.time, ''),
      news_count: toNumber(item?.news_count, 0),
      hot_score: toNumber(item?.hot_score, 0),
      positive_ratio: toRatio(item?.positive_ratio, 0),
      negative_ratio: toRatio(item?.negative_ratio, 0),
      neutral_ratio: toRatio(item?.neutral_ratio, 0),
    }))
    .filter((item) => item.time)
    .sort((a, b) => String(a.time).localeCompare(String(b.time)))
}

export function normalizeThirdEvent(item = {}, index = 0) {
  return {
    event_id: valueOrFallback(item.event_id ?? item.id ?? item.eventId ?? item.event_code, `event-${index + 1}`),
    event_title: valueOrFallback(item.event_title ?? item.title ?? item.name, '暂无标题'),
    category: valueOrFallback(item.category ?? item.field, '暂无分类'),
    hot_score: toNumber(item.hot_score ?? item.heat ?? item.heat_index ?? item.score, 0),
    news_count: toNumber(item.news_count ?? item.news ?? item.article_count ?? item.related_count, 0),
    sentiment_distribution: normalizeSentimentDistribution(item.sentiment_distribution ?? item.distribution),
    timeseries: normalizeTimeseries(item.timeseries ?? item.time_series ?? item.trend),
  }
}

export function getEvents(params) {
  return request.get('/events', { params })
}

export function getEventDetail(eventId) {
  return request.get(`/event/${eventId}`)
}

export function getCrossEvent(params) {
  return request.get('/cross-event', { params })
}

export function normalizeEventItem(item = {}, index = 0) {
  const thirdEvent = normalizeThirdEvent(item, index)
  const distribution = thirdEvent.sentiment_distribution
  const dominantSentiment = Object.entries(distribution).sort((a, b) => b[1] - a[1])[0]?.[0] ?? 'neutral'
  const sentimentType =
    item.sentimentType ??
    sentimentTypeMap[String(item.sentiment_type ?? item.sentiment_label ?? item.sentiment ?? '').toLowerCase()] ??
    sentimentTypeMap[dominantSentiment] ??
    'neutral'

  return {
    raw: item,
    ...thirdEvent,
    id: thirdEvent.event_id,
    rank: String(item.rank ?? index + 1).padStart(2, '0'),
    title: thirdEvent.event_title,
    summary: valueOrFallback(item.summary ?? item.description ?? item.intro, '暂无摘要'),
    heat: thirdEvent.hot_score,
    source: valueOrFallback(item.source ?? item.platform ?? item.sources, '暂无来源'),
    time: valueOrFallback(
      item.time ?? item.publish_time ?? item.created_at ?? item.updated_at ?? thirdEvent.timeseries[0]?.time,
      '暂无时间',
    ),
    sentiment: valueOrFallback(item.sentiment ?? item.sentiment_label ?? item.status ?? sentimentLabelMap[dominantSentiment], '暂无情感'),
    sentimentType,
    tags: normalizeTags(item.tags ?? item.keywords ?? item.categories ?? thirdEvent.category),
    stage: valueOrFallback(item.stage ?? item.current_stage, '暂无阶段'),
    sentimentRate: Number((toRatio(item.sentiment_rate ?? item.sentimentRate ?? item.positive_rate ?? distribution[dominantSentiment], 0) * 100).toFixed(1)),
    news: thirdEvent.news_count,
  }
}

export function normalizeEventsPayload(payload) {
  const data = unwrapPayload(payload)
  const list = Array.isArray(data) ? data : data?.events ?? data?.items ?? data?.list ?? data?.records ?? []

  return toArray(list).map(normalizeEventItem)
}

export async function fetchEventsWithFallback(params) {
  try {
    const payload = await getEvents(params)
    const events = normalizeEventsPayload(payload)
    return events.length ? events : mockHotEvents.map(normalizeEventItem)
  } catch (error) {
    console.warn('事件列表接口不可用，使用本地模拟数据。', error)
    return mockHotEvents.map(normalizeEventItem)
  }
}

function buildLifecycleFromThirdEvent(thirdEvent) {
  if (!thirdEvent.timeseries.length) return {}

  const heatPoints = thirdEvent.timeseries.map((item) => ({ label: item.time, value: item.hot_score }))
  const newsPoints = thirdEvent.timeseries.map((item) => ({ label: item.time, value: item.news_count }))

  return {
    points: heatPoints,
    heat_trend: heatPoints,
    news_trend: newsPoints,
    labels: thirdEvent.timeseries.map((item) => item.time),
    heat: thirdEvent.hot_score,
    current_heat_index: thirdEvent.hot_score,
    current_avg_count: thirdEvent.news_count,
  }
}

export function mergeEventDetailWithMock(payload, eventId) {
  const data = unwrapPayload(payload)
  const source = data && typeof data === 'object' && !Array.isArray(data) ? data : {}
  const eventSource = source.event ?? source.event_info ?? source
  const normalizedItem = normalizeEventItem(eventSource, 0)
  const thirdEvent = normalizeThirdEvent(eventSource, 0)
  const lifecycleFromThird = buildLifecycleFromThirdEvent(thirdEvent)

  return {
    ...eventDetailMock,
    ...source,
    ...thirdEvent,
    id: eventId ?? thirdEvent.event_id ?? eventDetailMock.id,
    event: {
      ...eventDetailMock.event,
      ...source.event,
      title: normalizedItem.title,
      source: normalizedItem.source,
      time: normalizedItem.time,
      category: thirdEvent.category,
      heat: normalizedItem.heat || eventDetailMock.event.heat,
      stage: normalizedItem.stage || eventDetailMock.event.stage,
      riskLevel: valueOrFallback(eventSource.riskLevel ?? eventSource.risk_level, eventDetailMock.event.riskLevel),
      credibility: toNumber(eventSource.credibility ?? eventSource.credibility_score, eventDetailMock.event.credibility),
    },
    overview: {
      ...eventDetailMock.overview,
      ...(source.overview ?? {}),
      summary: valueOrFallback(source.overview?.summary ?? source.summary, normalizedItem.title),
    },
    lifecycle: { ...eventDetailMock.lifecycle, ...lifecycleFromThird, ...(source.lifecycle ?? source.lifecycle_analysis ?? {}) },
    propagation: { ...eventDetailMock.propagation, ...(source.propagation ?? source.propagation_analysis ?? {}) },
    relatedNews: source.relatedNews ?? source.related_news ?? eventDetailMock.relatedNews,
    sentiment_distribution: thirdEvent.sentiment_distribution,
    assistant: { ...eventDetailMock.assistant, ...(source.assistant ?? {}) },
  }
}

export async function fetchEventDetailWithFallback(eventId) {
  try {
    const payload = await getEventDetail(eventId)
    return mergeEventDetailWithMock(payload, eventId)
  } catch (error) {
    console.warn('事件详情接口不可用，使用本地模拟数据。', error)
    return { ...eventDetailMock, id: eventId || eventDetailMock.id }
  }
}

export function getMockEventArticles(eventId) {
  const filtered = newsDetailPreviewArticles.filter((item) => String(item.event_id ?? item.eventId) === String(eventId))
  return Promise.resolve(filtered.length ? filtered : newsDetailPreviewArticles)
}
