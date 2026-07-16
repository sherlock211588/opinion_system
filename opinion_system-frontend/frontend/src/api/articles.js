import { request3, request4 as request } from './request'
import { newsDetailPreviewArticle, newsDetailPreviewArticles } from '@/mock/newsDetailMock'
import { toArray, unwrapPayload } from './helpers'
import { normalizeThirdEvent } from './events'

// ============================================================
//  4号后端 — 文章虚假检测
// ============================================================

export function checkArticle(data) {
  const payload = {
    ...data,
    event_data: data?.event_data ? normalizeThirdEvent(data.event_data) : data?.event_data,
    articles: Array.isArray(data?.articles) ? data.articles.map(normalizeThirdArticle) : data?.articles,
  }
  return request.post('/articles/check', payload)
}

// ============================================================
//  4号后端 — 事件文章列表（含虚假检测判定）
// ============================================================

export async function getEventArticles(eventId) {
  if (!eventId) return getMockEventArticles('').map(normalizeThirdArticle)
  try {
    // 4号 GET /api/articles?event_id= → 返回含 verdict/confidence_score 的文章列表
    const data = await request.get('/articles', { params: { event_id: eventId } })
    const articles = Array.isArray(data) ? data : []
    return articles.length ? articles.map(normalizeThirdArticle) : getMockEventArticles(eventId).map(normalizeThirdArticle)
  } catch (error) {
    console.warn('Event articles API unavailable (4号), trying 3号 fallback.', error)
    try {
      const payload = await request3.get(`/analysis/event/${eventId}/articles`)
      const articles = normalizeArticlesPayload(payload)
      return articles.length ? articles : getMockEventArticles(eventId).map(normalizeThirdArticle)
    } catch (err2) {
      console.warn('3号 fallback also unavailable, using mock.', err2)
      return getMockEventArticles(eventId).map(normalizeThirdArticle)
    }
  }
}

// ============================================================
//  4号后端 — 单篇文章详情（含虚假检测）
// ============================================================

export async function getArticleDetail(articleId) {
  if (!articleId) return normalizeThirdArticle(getMockArticleDetail(articleId))
  try {
    // 4号 GET /api/articles/{article_id}
    const payload = await request.get(`/articles/${articleId}`)
    const data = unwrapPayload(payload)
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return normalizeThirdArticle(data)
    }
    return normalizeThirdArticle(getMockArticleDetail(articleId))
  } catch (error) {
    console.warn('Article detail API unavailable (4号), using mock.', error)
    return normalizeThirdArticle(getMockArticleDetail(articleId))
  }
}

// ============================================================
//  工具函数
// ============================================================

export function normalizeThirdArticle(item = {}) {
  return {
    ...item,
    id: item.id ?? item.article_id,
    article_id: item.article_id ?? item.id,
    title: item.title ?? '',
    cleaned_text: item.cleaned_text ?? item.text ?? item.content ?? '',
    source: item.source ?? '',
    publish_time: item.publish_time ?? item.time ?? '',
    sentiment: item.sentiment ?? '',
    verdict: item.verdict ?? '待验证',
    confidence_score: item.confidence_score ?? null,
    fake_probability: item.fake_probability ?? null,
    information_sufficiency: item.information_sufficiency ?? '一般',
    score_breakdown: item.score_breakdown ?? null,
    url: item.url ?? item.original_url ?? '',
    event_id: item.event_id ?? null,
  }
}

function getMockArticleDetail(articleId) {
  return (
    newsDetailPreviewArticles.find((item) => String(item.article_id ?? item.id) === String(articleId)) ??
    newsDetailPreviewArticle
  )
}

function getMockEventArticles(eventId) {
  const articles = newsDetailPreviewArticles.filter((item) => String(item.event_id ?? item.eventId) === String(eventId))
  return articles.length ? articles : newsDetailPreviewArticles
}

function normalizeArticlesPayload(payload) {
  const data = unwrapPayload(payload)
  const articles = Array.isArray(data)
    ? data
    : data?.articles ?? data?.relatedNews ?? data?.related_news ?? data?.items ?? data?.list ?? data?.records ?? []
  return toArray(articles).map(normalizeThirdArticle)
}
