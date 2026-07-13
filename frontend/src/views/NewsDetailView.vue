<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { init, use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { addRecentView } from '@/utils/recentViews'
import {
  newsDetailPreviewArticle,
  newsDetailPreviewArticles,
  newsDetailPreviewEvent,
} from '@/mock/newsDetailMock'
import { getArticleDetail, getEventArticles } from '@/api/articles'
import { fetchEventDetailWithFallback } from '@/api/events'
import { unwrapPayload } from '@/api/helpers'

use([RadarChart, TooltipComponent, CanvasRenderer])

const route = useRoute()
const router = useRouter()

const fallbackText = '暂无'
const emptyContentText = '当前数据暂未提供新闻内容'
const verdictOptions = ['可信', '待验证', '疑似虚假']
const scoreLabelMap = {
  source_credibility: '信源可信度',
  sentiment_extremity: '情感正常度',
  sentiment_normality: '情感正常度',
  cross_validation: '交叉验证度',
  time_risk: '时效可信度',
  timeliness_risk: '时效可信度',
  text_features: '文本特征得分',
  text_feature_score: '文本特征得分',
}
const sufficiencyLabels = {
  sufficient: '充分',
  full: '充分',
  high: '充分',
  medium: '一般',
  moderate: '一般',
  basic: '一般',
  insufficient: '不足',
  low: '不足',
  limited: '不足',
  sparse: '不足',
}

const article = ref(null)
const eventInfo = ref(null)
const eventArticles = ref([])
const loading = ref(false)
const error = ref('')
const notFound = ref(false)
const isPreviewMode = ref(false)
const radarRef = ref(null)
let radarChart
let resizeObserver

const hasValue = (value) => value !== undefined && value !== null && value !== ''
const valueOrFallback = (value) => (hasValue(value) ? value : fallbackText)
const getArticleId = () => route.params.articleId ?? route.params.id
const getRouteEventId = () => route.query.eventId ?? route.params.eventId
const getArticleEventId = (item = article.value) => item?.event_id ?? item?.eventId ?? getRouteEventId()
const eventPath = (eventId = currentArticle.value.eventId) => (eventId ? `/report/${eventId}` : '/events')

const normalizeVerdict = (verdict) => {
  if (verdictOptions.includes(verdict)) return verdict
  const text = String(verdict ?? '').toLowerCase()
  if (['true', 'credible', 'real', '可信'].includes(text)) return '可信'
  if (['fake', 'false', '虚假', '假新闻', '不可信', '疑似虚假'].includes(text)) return '疑似虚假'
  return '待验证'
}
const verdictClass = (verdict) => {
  if (verdict === '可信') return 'is-credible'
  if (verdict === '疑似虚假') return 'is-fake'
  return 'is-pending'
}
const toScore = (value) => {
  const number = Number(value)
  if (!Number.isFinite(number)) return null
  return Math.max(0, Math.min(number <= 1 ? number * 100 : number, 100))
}
const formatPercent = (value) => {
  const number = toScore(value)
  if (number === null) return fallbackText
  return `${Number(number.toFixed(1))}%`
}
const formatTime = (value) => valueOrFallback(value)
const translateSufficiency = (value) => {
  if (['充分', '一般', '不足'].includes(value)) return value
  return sufficiencyLabels[String(value ?? '').toLowerCase()] || valueOrFallback(value)
}
const getArticles = (payload) => {
  const data = unwrapPayload(payload)
  const articles = data?.articles ?? data?.relatedNews ?? data?.related_news ?? []
  return Array.isArray(articles) ? articles : []
}
const findArticle = (articles, articleId) =>
  (Array.isArray(articles) ? articles : []).find((item) => String(item?.article_id ?? item?.id) === String(articleId))
const applyEventPayload = (payload) => {
  const data = unwrapPayload(payload)
  eventInfo.value = data?.event ?? data?.event_info ?? data
  eventArticles.value = getArticles(payload)
}

async function loadEvent(eventId) {
  if (!eventId) return null
  const payload = await fetchEventDetailWithFallback(eventId)
  applyEventPayload(payload)
  eventArticles.value = await getEventArticles(eventId)
  return payload
}

function applyPreviewData() {
  const articleId = getArticleId()
  const eventId = getRouteEventId()
  const matchedArticle =
    newsDetailPreviewArticles.find((item) => String(item.article_id) === String(articleId)) ??
    newsDetailPreviewArticles.find((item) => String(item.event_id) === String(eventId)) ??
    newsDetailPreviewArticle

  article.value = matchedArticle
  eventInfo.value = newsDetailPreviewEvent
  eventArticles.value = newsDetailPreviewArticles
  error.value = ''
  notFound.value = false
  isPreviewMode.value = true
}

async function loadNews() {
  const articleId = getArticleId()
  const queryEventId = getRouteEventId()

  article.value = null
  eventInfo.value = null
  eventArticles.value = []
  error.value = ''
  notFound.value = false
  isPreviewMode.value = false

  if (!articleId) {
    applyPreviewData()
    return
  }

  loading.value = true
  try {
    try {
      const articlePayload = await getArticleDetail(articleId)
      const data = unwrapPayload(articlePayload)
      const current = Array.isArray(data) ? findArticle(data, articleId) : data
      if (current && (current.article_id || current.id || !Array.isArray(data))) {
        article.value = current
        eventInfo.value = current.event ?? current.event_info ?? null
      }
    } catch (articleError) {
      console.warn('新闻详情接口不可用，改用事件接口回退。', articleError)
    }

    const eventId = getArticleEventId(article.value) ?? queryEventId
    if (eventId) {
      const eventPayload = await loadEvent(eventId)
      if (!article.value) article.value = findArticle(getArticles(eventPayload), articleId) ?? null
    }

    if (!article.value) applyPreviewData()
  } catch (loadError) {
    console.error('新闻数据加载失败。', loadError)
    applyPreviewData()
  } finally {
    loading.value = false
    nextTick(renderRadar)
  }
}

const currentArticle = computed(() => {
  const item = article.value ?? {}
  const eventId = getArticleEventId(item)
  return {
    raw: item,
    articleId: item.article_id ?? item.id ?? getArticleId(),
    eventId,
    title: valueOrFallback(item.title),
    source: valueOrFallback(item.source),
    publishTime: formatTime(item.publish_time ?? item.time),
    eventTitle: valueOrFallback(item.event_title ?? eventInfo.value?.title ?? eventInfo.value?.event_title ?? eventId),
    content: item.cleaned_text ?? item.text ?? item.content ?? '',
    url: item.url ?? item.original_url ?? '',
    verdict: normalizeVerdict(item.verdict),
    confidenceScore: item.confidence_score,
    confidenceDisplay: formatPercent(item.confidence_score),
    informationSufficiency: translateSufficiency(item.information_sufficiency),
    sentiment: valueOrFallback(item.sentiment),
    scoreBreakdown: item.score_breakdown,
  }
})
const hasBody = computed(() => currentArticle.value.content.trim().length > 0)
const hasUrl = computed(() => hasValue(currentArticle.value.url))
const originalState = computed(() => (hasUrl.value ? '可访问' : '未提供'))
const metadataItems = computed(() => [
  { icon: '◎', label: '新闻来源', value: currentArticle.value.source },
  { icon: '◷', label: '发布时间', value: currentArticle.value.publishTime },
  { icon: '◇', label: '所属事件', value: currentArticle.value.eventTitle, link: eventPath() },
  { icon: '#', label: '新闻编号', value: valueOrFallback(currentArticle.value.articleId) },
])
const validScoreItems = computed(() => {
  const breakdown = currentArticle.value.scoreBreakdown
  if (!breakdown || typeof breakdown !== 'object' || Array.isArray(breakdown)) return []
  return Object.entries(breakdown)
    .map(([key, source]) => {
      const rawValue = typeof source === 'object' && source !== null ? source.value ?? source.score : source
      const value = toScore(rawValue)
      return value === null ? null : { key, label: scoreLabelMap[key] ?? key, value }
    })
    .filter(Boolean)
})
const hasScoreBreakdown = computed(() => validScoreItems.value.length > 0)
const radarOption = computed(() => {
  const items = validScoreItems.value
  if (!items.length) return null
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(8, 18, 42, .92)',
      borderColor: 'rgba(129, 140, 248, .36)',
      textStyle: { color: '#e8edff' },
      formatter: () => items.map((item) => `${item.label}: ${Number(item.value.toFixed(1))}`).join('<br/>'),
    },
    radar: {
      center: ['50%', '50%'],
      radius: '68%',
      splitNumber: 4,
      indicator: items.map((item) => ({ name: `${item.label}\n${Number(item.value.toFixed(1))}`, max: 100 })),
      axisName: { color: '#b7c5dd', fontSize: 12, lineHeight: 17 },
      axisLine: { lineStyle: { color: 'rgba(129, 140, 248, .26)' } },
      splitLine: { lineStyle: { color: 'rgba(129, 140, 248, .24)' } },
      splitArea: { areaStyle: { color: ['rgba(30, 58, 138, .16)', 'rgba(76, 29, 149, .11)'] } },
    },
    series: [
      {
        type: 'radar',
        data: [{ value: items.map((item) => item.value), name: '可信度维度' }],
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 3, color: '#7c8cff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 1,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(56, 189, 248, .32)' },
              { offset: 1, color: 'rgba(168, 85, 247, .38)' },
            ],
          },
        },
        itemStyle: { color: '#e0f2fe', borderColor: '#22d3ee', borderWidth: 2 },
      },
    ],
  }
})
const relatedNews = computed(() => {
  const current = currentArticle.value
  return eventArticles.value
    .filter((item) => {
      const sameEvent = !current.eventId || String(item?.event_id ?? item?.eventId ?? current.eventId) === String(current.eventId)
      const otherArticle = String(item?.article_id ?? item?.id) !== String(current.articleId)
      return sameEvent && otherArticle
    })
    .sort((a, b) => String(b?.publish_time ?? b?.time ?? '').localeCompare(String(a?.publish_time ?? a?.time ?? '')))
    .slice(0, 4)
    .map((item) => ({
      articleId: item.article_id ?? item.id,
      eventId: item.event_id ?? item.eventId ?? current.eventId,
      title: valueOrFallback(item.title),
      source: valueOrFallback(item.source),
      publishTime: formatTime(item.publish_time ?? item.time),
      verdict: normalizeVerdict(item.verdict),
    }))
})

function renderRadar() {
  if (!radarRef.value || !radarOption.value) {
    radarChart?.dispose()
    radarChart = null
    return
  }
  if (!radarChart) radarChart = init(radarRef.value)
  radarChart.setOption(radarOption.value, true)
  radarChart.resize()
}
function openOriginal() {
  if (!hasUrl.value) return
  window.open(currentArticle.value.url, '_blank', 'noopener,noreferrer')
}
function openRelatedNews(item) {
  if (!item.articleId) return
  router.push({ path: `/news/${item.articleId}`, query: item.eventId ? { eventId: item.eventId } : {} })
}
function onRelatedKeydown(event, item) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    openRelatedNews(item)
  }
}

watch(
  () => [route.params.articleId, route.params.id, route.query.eventId, route.params.eventId],
  async () => {
    await loadNews()
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  },
  { immediate: true },
)
watch(radarOption, () => nextTick(renderRadar), { deep: true })
watch(
  currentArticle,
  (item) => {
    if (loading.value || error.value || notFound.value || !item?.articleId || item.title === fallbackText) return
    addRecentView({
      id: item.articleId,
      type: 'news',
      title: item.title,
      meta: item.verdict || item.source,
      path: route.fullPath,
    })
  },
  { immediate: true },
)

onMounted(() => {
  renderRadar()
  if (radarRef.value) {
    resizeObserver = new ResizeObserver(() => radarChart?.resize())
    resizeObserver.observe(radarRef.value)
  }
})
onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  radarChart?.dispose()
})
</script>

<template>
  <section class="news-detail-page">
    <div v-if="loading" class="detail-card state-card">新闻数据加载中...</div>
    <div v-else-if="error" class="detail-card state-card">
      <strong>新闻数据加载失败</strong>
      <span>请稍后重试，页面不会留空。</span>
    </div>
    <div v-else-if="notFound" class="detail-card state-card">
      <strong>未找到该新闻</strong>
      <span>请从事件列表重新进入。</span>
    </div>

    <article v-else class="detail-shell">
      <nav class="breadcrumb" aria-label="面包屑">
        <RouterLink to="/events">事件列表</RouterLink>
        <span>/</span>
        <RouterLink :to="eventPath()">{{ currentArticle.eventTitle }}</RouterLink>
        <span>/</span>
        <b>当前新闻</b>
      </nav>
      <span v-if="isPreviewMode" class="preview-badge">前端预览数据</span>

      <header class="hero-card detail-card">
        <div class="title-row">
          <RouterLink class="back-button" :to="eventPath()">← 返回所属事件</RouterLink>
          <span class="verdict-pill" :class="verdictClass(currentArticle.verdict)">{{ currentArticle.verdict }}</span>
          <h1>{{ currentArticle.title }}</h1>
          <div class="confidence-summary">
            <span class="verdict-pill" :class="verdictClass(currentArticle.verdict)">{{ currentArticle.verdict }}</span>
            <strong>综合可信度 {{ currentArticle.confidenceDisplay }}</strong>
          </div>
        </div>

        <div class="meta-row">
          <component
            :is="item.link ? 'RouterLink' : 'span'"
            v-for="item in metadataItems"
            :key="item.label"
            class="meta-item"
            :to="item.link"
          >
            <i>{{ item.icon }}</i>
            <em>{{ item.label }}</em>
            <b>{{ item.value }}</b>
          </component>
        </div>
      </header>

      <div class="main-grid">
        <section class="detail-card content-card">
          <div class="card-title">
            <span></span>
            <h2>新闻内容</h2>
          </div>
          <p v-if="hasBody" class="article-text">{{ currentArticle.content }}</p>
          <div v-else class="empty-state">{{ emptyContentText }}</div>

          <div class="content-actions">
            <button type="button" :disabled="!hasUrl" @click="openOriginal">
              {{ hasUrl ? '查看新闻原文 →' : '暂无原文链接' }}
            </button>
          </div>

          <footer class="compact-info">
            <span>来源：{{ currentArticle.source }}</span>
            <span>情感：{{ currentArticle.sentiment }}</span>
            <span>原文状态：{{ originalState }}</span>
          </footer>
        </section>

        <aside class="detail-card detection-card">
          <div class="card-title">
            <span></span>
            <h2>虚假文本检测</h2>
          </div>
          <div v-if="hasScoreBreakdown" ref="radarRef" class="radar-chart" aria-label="可信度维度雷达图"></div>
          <div v-else class="empty-state radar-empty">暂无可信度维度分析数据</div>

          <div class="detection-footer">
            <div>
              <small>检测状态</small>
              <span class="verdict-pill" :class="verdictClass(currentArticle.verdict)">{{ currentArticle.verdict }}</span>
            </div>
            <div>
              <small>综合可信度</small>
              <strong>{{ currentArticle.confidenceDisplay }}</strong>
            </div>
            <div>
              <small>信息充分度</small>
              <strong>{{ currentArticle.informationSufficiency }}</strong>
            </div>
          </div>
        </aside>
      </div>

      <section class="detail-card related-card">
        <div class="card-title">
          <span></span>
          <h2>同事件其他新闻</h2>
        </div>
        <div v-if="relatedNews.length" class="related-grid">
          <article
            v-for="item in relatedNews"
            :key="item.articleId"
            role="link"
            tabindex="0"
            @click="openRelatedNews(item)"
            @keydown="onRelatedKeydown($event, item)"
          >
            <h3>{{ item.title }}</h3>
            <p>{{ item.source }}</p>
            <time>{{ item.publishTime }}</time>
            <span class="verdict-pill" :class="verdictClass(item.verdict)">{{ item.verdict }}</span>
          </article>
        </div>
        <div v-else class="empty-related">该事件暂无其他相关新闻</div>
      </section>
    </article>
  </section>
</template>

<style scoped>
.news-detail-page {
  --card-bg: rgba(9, 24, 58, .72);
  --card-bg-soft: rgba(18, 35, 80, .54);
  --line: rgba(139, 154, 255, .28);
  --line-strong: rgba(125, 92, 255, .48);
  --muted: #91a2bf;
  --text: #e8edff;
  box-sizing: border-box;
  min-height: 720px;
  height: calc(100vh - var(--header-height, 76px));
  margin: -10px clamp(-48px, -3vw, -24px) -36px;
  padding: 18px 24px 24px;
  overflow: auto;
  color: var(--text);
  background:
    radial-gradient(circle at 12% 8%, rgba(38, 98, 255, .26), transparent 28%),
    radial-gradient(circle at 80% 10%, rgba(160, 90, 255, .22), transparent 32%),
    linear-gradient(135deg, rgba(5, 17, 42, .95), rgba(13, 24, 64, .97) 54%, rgba(8, 15, 42, .98));
}

.detail-shell {
  display: grid;
  min-height: 100%;
  grid-template-rows: auto auto auto minmax(0, 1fr) auto;
  gap: 14px;
}

.detail-card {
  min-width: 0;
  box-sizing: border-box;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--card-bg);
  box-shadow: 0 18px 50px rgba(1, 8, 30, .28), inset 0 1px 0 rgba(255, 255, 255, .04);
  backdrop-filter: blur(18px);
}

.state-card {
  display: grid;
  min-height: 240px;
  place-items: center;
  align-content: center;
  gap: 8px;
  color: #c7d2fe;
  font-size: 15px;
}

.state-card strong {
  color: #fff;
  font-size: 18px;
}

.breadcrumb {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
  color: #7285a7;
  font-size: 13px;
  line-height: 1.3;
}

.breadcrumb a,
.breadcrumb b {
  min-width: 0;
  overflow: hidden;
  color: #9fb2d4;
  font-weight: 600;
  text-decoration: none;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.breadcrumb b {
  color: #cdd7ee;
}

.preview-badge {
  width: fit-content;
  padding: 3px 9px;
  border: 1px solid rgba(251, 191, 36, .28);
  border-radius: 999px;
  color: #facc15;
  background: rgba(251, 191, 36, .1);
  font-size: 11px;
  font-weight: 800;
  line-height: 1.2;
}

.hero-card {
  padding: 16px 18px 15px;
}

.title-row {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.back-button {
  display: inline-flex;
  height: 34px;
  align-items: center;
  padding: 0 13px;
  border: 1px solid rgba(129, 140, 248, .34);
  border-radius: 10px;
  color: #c7d2fe;
  background: rgba(13, 29, 67, .56);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  transition: .18s ease;
}

.back-button:hover,
.related-grid article:hover {
  border-color: rgba(56, 189, 248, .58);
  box-shadow: 0 0 20px rgba(56, 189, 248, .1);
}

.verdict-pill {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
  white-space: nowrap;
}

.is-credible {
  border: 1px solid rgba(52, 211, 153, .34);
  color: #5eead4;
  background: rgba(20, 184, 166, .12);
}

.is-pending {
  border: 1px solid rgba(251, 191, 36, .34);
  color: #fbbf24;
  background: rgba(251, 191, 36, .12);
}

.is-fake {
  border: 1px solid rgba(248, 113, 113, .34);
  color: #fca5a5;
  background: rgba(248, 113, 113, .12);
}

h1 {
  min-width: 0;
  max-height: 72px;
  margin: 0;
  overflow: hidden;
  color: #fff;
  font-size: clamp(26px, 2vw, 30px);
  font-weight: 850;
  line-height: 1.2;
  overflow-wrap: anywhere;
}

.confidence-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-end;
  color: #c9d4e8;
  font-size: 13px;
  white-space: nowrap;
}

.confidence-summary strong {
  color: #eaf2ff;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  margin-top: 13px;
  color: var(--muted);
  font-size: 14px;
}

.meta-item {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 6px;
  color: inherit;
  text-decoration: none;
}

.meta-item + .meta-item::before {
  width: 1px;
  height: 12px;
  margin: 0 14px;
  background: rgba(145, 162, 191, .36);
  content: '';
}

.meta-item i,
.meta-item em {
  color: #7186a9;
  font-style: normal;
}

.meta-item b {
  min-width: 0;
  overflow: hidden;
  color: #aebbd5;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-grid {
  display: grid;
  min-height: 0;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 28px;
  align-items: stretch;
}

.content-card,
.detection-card {
  display: grid;
  min-height: 0;
  padding: 18px;
}

.content-card {
  grid-template-rows: auto minmax(0, 1fr) auto auto;
}

.detection-card {
  grid-template-rows: auto minmax(240px, 1fr) auto;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
}

.card-title span {
  width: 10px;
  height: 10px;
  border-radius: 4px;
  background: linear-gradient(135deg, #38bdf8, #8b5cf6);
  box-shadow: 0 0 14px rgba(56, 189, 248, .36);
}

.card-title h2 {
  margin: 0;
  color: #f8fbff;
  font-size: 17px;
  font-weight: 800;
}

.article-text {
  min-height: 0;
  margin: 0;
  overflow: auto;
  color: #c9d4e8;
  font-size: 16px;
  line-height: 1.9;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.empty-state,
.empty-related {
  display: grid;
  min-height: 120px;
  place-items: center;
  border: 1px dashed rgba(129, 140, 248, .24);
  border-radius: 14px;
  color: #7f91b2;
  background: rgba(10, 25, 58, .34);
  font-size: 14px;
  text-align: center;
}

.radar-empty {
  min-height: 0;
}

.content-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.content-actions button {
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid rgba(56, 189, 248, .34);
  border-radius: 10px;
  color: #7dd3fc;
  background: rgba(13, 29, 67, .58);
  font: inherit;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: .18s ease;
}

.content-actions button:disabled {
  border-color: rgba(129, 140, 248, .16);
  color: #64748b;
  cursor: not-allowed;
}

.compact-info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(129, 140, 248, .16);
  color: #95a7c5;
  font-size: 12px;
}

.radar-chart {
  width: 100%;
  height: clamp(320px, 36vh, 460px);
  min-height: 320px;
}

.detection-footer {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.detection-footer div {
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(129, 140, 248, .14);
  border-radius: 12px;
  background: var(--card-bg-soft);
}

.detection-footer small {
  display: block;
  margin-bottom: 8px;
  color: #7186a9;
  font-size: 11px;
}

.detection-footer strong {
  color: #eaf2ff;
  font-size: 18px;
  overflow-wrap: anywhere;
}

.related-card {
  padding: 16px 18px 18px;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.related-grid article {
  display: grid;
  min-width: 0;
  min-height: 118px;
  align-content: start;
  gap: 7px;
  padding: 13px;
  border: 1px solid rgba(129, 140, 248, .18);
  border-radius: 14px;
  background: rgba(13, 29, 67, .48);
  cursor: pointer;
  transition: .18s ease;
}

.related-grid h3 {
  display: -webkit-box;
  min-width: 0;
  margin: 0;
  overflow: hidden;
  color: #e8edff;
  font-size: 14px;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow-wrap: anywhere;
}

.related-grid p,
.related-grid time {
  margin: 0;
  overflow: hidden;
  color: #8395b5;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.related-grid .verdict-pill {
  margin-top: 2px;
}

.empty-related {
  min-height: 92px;
}

@media (max-width: 1100px) {
  .news-detail-page {
    height: auto;
    min-height: calc(100vh - var(--header-height, 76px));
  }

  .main-grid,
  .related-grid {
    grid-template-columns: 1fr;
  }

  .title-row {
    grid-template-columns: auto auto minmax(0, 1fr);
  }

  .confidence-summary {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }
}

@media (max-width: 760px) {
  .news-detail-page {
    margin: -6px -16px -24px;
    padding: 14px;
  }

  .title-row {
    grid-template-columns: 1fr;
    align-items: start;
  }

  h1 {
    font-size: 24px;
    max-height: none;
  }

  .meta-row {
    display: grid;
    gap: 8px;
  }

  .meta-item + .meta-item::before {
    display: none;
  }

  .detection-footer {
    grid-template-columns: 1fr;
  }
}
</style>
