import { newsDetailPreviewArticle, newsDetailPreviewArticles } from '@/mock/newsDetailMock'
import request from './request'
import { toArray, unwrapPayload } from './helpers'
import { normalizeThirdEvent } from './events'

export function checkArticle(data) {
  const payload = {
    ...data,
    event_data: data?.event_data ? normalizeThirdEvent(data.event_data) : data?.event_data,
    articles: Array.isArray(data?.articles) ? data.articles.map(normalizeThirdArticle) : data?.articles,
  }
  return request.post('/articles/check', payload)
}

export function normalizeThirdArticle(item = {}) {
  return {
    ...item,
    id: item.id ?? item.article_id,
    title: item.title ?? '',
    cleaned_text: item.cleaned_text ?? item.text ?? item.content ?? '',
    source: item.source ?? '',
    publish_time: item.publish_time ?? item.time ?? '',
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

function normalizeArticleDetailPayload(payload, articleId) {
  const data = unwrapPayload(payload)
  const article = data?.article ?? data?.article_info ?? data?.detail ?? data

  if (Array.isArray(article)) {
    const matched = article.find((item) => String(item?.article_id ?? item?.id) === String(articleId)) ?? null
    return matched ? normalizeThirdArticle(matched) : null
  }

  return article && typeof article === 'object' ? normalizeThirdArticle(article) : null
}

function normalizeArticlesPayload(payload) {
  const data = unwrapPayload(payload)
  const articles = Array.isArray(data)
    ? data
    : data?.articles ?? data?.relatedNews ?? data?.related_news ?? data?.items ?? data?.list ?? data?.records ?? []

  return toArray(articles).map(normalizeThirdArticle)
}

export async function getArticleDetail(articleId) {
  try {
    const payload = await request.get(`/articles/${articleId}`)
    return normalizeArticleDetailPayload(payload, articleId) ?? normalizeThirdArticle(getMockArticleDetail(articleId))
  } catch (error) {
    console.warn('Article detail API unavailable, using local mock data.', error)
    return normalizeThirdArticle(getMockArticleDetail(articleId))
  }
}

export async function getEventArticles(eventId) {
  try {
    const payload = await request.get('/articles', { params: { event_id: eventId, eventId } })
    const articles = normalizeArticlesPayload(payload)
    return articles.length ? articles : getMockEventArticles(eventId).map(normalizeThirdArticle)
  } catch (error) {
    console.warn('Event articles API unavailable, using local mock data.', error)
    return getMockEventArticles(eventId).map(normalizeThirdArticle)
  }
}
