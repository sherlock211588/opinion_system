<template>
  <section class="dashboard page-stack">
    <div class="hero-panel">
      <div>
        <span class="eyebrow">AI Opinion Insight</span>
        <h1>全局舆情概览</h1>
        <p>聚合新闻、社交与内容平台数据，快速发现热点、理解情绪变化，并生成可读的分析报告。</p>
      </div>

      <RouterLink class="hero-action liquid-link" to="/ai">
        <span>向 AI 提问</span>
      </RouterLink>
    </div>

    <div class="metric-grid">
      <MetricCard v-for="card in overviewCards" :key="card.label" :card="card" />
    </div>

    <div class="section-grid">
      <section class="glass-section feed-section">
        <div class="section-head">
          <div>
            <span>Hot Feed</span>
            <h2>热点事件信息流</h2>
          </div>
          <RouterLink to="/events">查看全部</RouterLink>
        </div>

        <article v-for="event in hotEvents" :key="event.id" class="event-card">
          <div>
            <h3>{{ event.title }}</h3>
            <p>{{ event.summary }}</p>
            <div class="meta">
              <span>{{ event.source }}</span>
              <span>{{ event.time }}</span>
              <em :class="event.sentimentType">{{ event.sentiment }}</em>
            </div>
          </div>
          <div class="event-side">
            <strong>{{ event.heat }}</strong>
            <RouterLink :to="`/events/${event.id}`">查看详情</RouterLink>
          </div>
        </article>
      </section>

      <section class="glass-section ai-entry">
        <span>AI Assistant</span>
        <h2>你想了解哪个舆情事件？</h2>
        <div class="chat-input">
          <input v-model="searchQuery" placeholder="请输入你想了解的舆情事件" @keyup.enter="searchAndGo" />
          <a href="#" @click.prevent="searchAndGo">{{ searching ? '搜索中...' : '分析' }}</a>
        </div>
        <div class="quick-tags">
          <span v-for="tag in quickTags" :key="tag" @click="searchByTag(tag)">{{ tag }}</span>
        </div>
        <p v-if="searchError" class="search-error">{{ searchError }}</p>
      </section>
    </div>

    <section class="glass-section analytics">
      <div class="section-head">
        <div>
          <span>Analytics</span>
          <h2>数据分析区域</h2>
        </div>
      </div>

      <div class="chart-grid">
        <div class="chart-card wide">
          <h3>全局热度趋势</h3>
          <BaseChart :option="trendOption" />
        </div>
        <div class="chart-card">
          <h3>情感比例</h3>
          <BaseChart :option="sentimentOption" />
        </div>
        <div class="chart-card keywords">
          <h3>热门关键词</h3>
          <div class="keyword-list">
            <span v-for="keyword in keywords" :key="keyword">{{ keyword }}</span>
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseChart from '@/components/BaseChart.vue'
import MetricCard from '@/components/MetricCard.vue'
import { fetchEventsWithFallback, normalizeEventItem } from '@/api/events'
import { searchSimilarEvents } from '@/api/analysis'
import { getDashboard } from '@/api/system'

const router = useRouter()
const searchQuery = ref('')
const searching = ref(false)
const searchError = ref('')
const quickTags = ['新能源汽车事件', '城市文旅热度', 'AI新品讨论']

// 看板数据（从 4号 /api/dashboard 拉取）
const dashboardKpi = ref({ total_events: 0, avg_heat: 0, risk_events: 0, platform_count: 0, dominant_sentiment: '', sentiment_positive_pct: 0 })
const dashboardSentiment = ref({ positive: 42, negative: 22, neutral: 36 })
const dashboardTrend = ref({ dates: [], values: [] })
const dashboardKeywords = ref([])

const hotEvents = ref([])

async function fetchDashboard() {
  try {
    const data = await getDashboard()
    if (!data) return

    const kpi = data.kpi || data
    dashboardKpi.value = {
      total_events: kpi.total_events ?? 0,
      avg_heat: kpi.avg_heat ?? 0,
      risk_events: kpi.risk_events ?? 0,
      platform_count: kpi.platform_count ?? 0,
      dominant_sentiment: kpi.dominant_sentiment ?? '',
      sentiment_positive_pct: kpi.sentiment_positive_pct ?? 0,
    }

    const sent = data.sentiment || {}
    if (sent.positive !== undefined) {
      dashboardSentiment.value = {
        positive: sent.positive ?? 0,
        negative: sent.negative ?? 0,
        neutral: sent.neutral ?? 0,
      }
    }

    const trend = data.heat_trend || []
    if (trend.length) {
      dashboardTrend.value = {
        dates: trend.map(t => t.date || ''),
        values: trend.map(t => t.value ?? 0),
      }
    } else {
      dashboardTrend.value = { dates: ['--'], values: [0] }
    }

    const kws = data.keywords || []
    dashboardKeywords.value = Array.isArray(kws)
      ? kws.map(kw => (typeof kw === 'string' ? kw : kw[0] || kw.name || ''))
      : []
  } catch {
    // 保持默认值，图表显示"暂无数据"
  }
}

onMounted(async () => {
  hotEvents.value = await fetchEventsWithFallback()
  await fetchDashboard()
})

// ---- 搜索 ----
async function searchAndGo() {
  const query = searchQuery.value.trim()
  if (!query || searching.value) return
  searching.value = true
  searchError.value = ''
  try {
    const results = await searchSimilarEvents(query, 5)
    if (results && results.length > 0 && results[0].similarity > 0.05) {
      router.push(`/report/${results[0].event_id}`)
    } else {
      searchError.value = '未找到相关事件，请尝试其他关键词'
    }
  } catch (e) {
    console.error('搜索错误:', e)
    searchError.value = '搜索服务暂不可用: ' + (e?.message || e?.response?.status || String(e))
    searching.value = false
    return
  } finally {
    searching.value = false
  }
}

function searchByTag(tag) {
  searchQuery.value = tag
  searchAndGo()
}

// ---- KPI 卡片 ----
const overviewCards = computed(() => {
  const k = dashboardKpi.value
  return [
    { label: '今日热点数量', value: k.total_events, suffix: '个', trend: '', desc: `共追踪 ${k.total_events} 个舆情事件` },
    { label: '当前热度指数', value: k.avg_heat, suffix: '', trend: '', desc: '全平台综合热度均值' },
    { label: '整体情感趋势', value: k.sentiment_positive_pct, suffix: '%', trend: k.dominant_sentiment, desc: '正面与中立观点占比' },
    { label: '数据来源数量', value: k.platform_count, suffix: '类', trend: '', desc: '新闻、社交与内容平台' },
  ]
})

// ---- 趋势图 ----
const trendOption = computed(() => ({
  color: ['#805CFF'],
  tooltip: { trigger: 'axis' },
  grid: { left: 36, right: 24, top: 36, bottom: 32 },
  xAxis: {
    type: 'category',
    data: dashboardTrend.value.dates,
    axisLine: { lineStyle: { color: '#D8D4EA' } },
    axisTick: { show: false },
    axisLabel: { color: '#7A8294' },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: 'rgba(128,92,255,.1)' } },
    axisLabel: { color: '#7A8294' },
  },
  series: [
    {
      data: dashboardTrend.value.values,
      type: 'line',
      smooth: true,
      symbolSize: 9,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(128,92,255,.26)' },
            { offset: 1, color: 'rgba(128,92,255,0)' },
          ],
        },
      },
    },
  ],
}))

// ---- 情感饼图 ----
const sentimentOption = computed(() => ({
  color: ['#805CFF', '#C8B6FF', '#FF7AB6'],
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, textStyle: { color: '#6B7280' } },
  series: [
    {
      type: 'pie',
      radius: ['46%', '70%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      label: { formatter: '{b}\n{d}%', color: '#4B5563' },
      data: [
        { value: dashboardSentiment.value.positive, name: '正面' },
        { value: dashboardSentiment.value.neutral, name: '中立' },
        { value: dashboardSentiment.value.negative, name: '负面' },
      ],
    },
  ],
}))

// ---- 关键词 ----
const keywords = computed(() => dashboardKeywords.value)
</script>
</script>

<style scoped>
.page-stack {
  display: grid;
  gap: 24px;
}

.hero-panel,
.glass-section,
.chart-card {
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 24px 70px rgba(93, 73, 220, 0.11);
  backdrop-filter: blur(20px);
}

.hero-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  padding: 34px;
  border-radius: 32px;
}

.eyebrow,
.section-head span,
.ai-entry > span {
  color: #805cff;
  font-size: 13px;
  font-weight: 900;
}

h1,
h2,
h3,
p {
  margin: 0;
}

.hero-panel h1 {
  margin-top: 10px;
  font-size: clamp(34px, 4vw, 54px);
  line-height: 1.1;
}

.hero-panel p {
  max-width: 680px;
  margin-top: 14px;
  color: #94a3b8;
  font-size: 16px;
  line-height: 1.8;
}

.liquid-link,
.event-side a,
.chat-input a,
.section-head a {
  text-decoration: none;
}

.liquid-link,
.chat-input a {
  position: relative;
  overflow: hidden;
  flex: 0 0 auto;
  padding: 14px 22px;
  border-radius: 999px;
  background: linear-gradient(135deg, #805cff, #6d5dfb);
  color: #fff;
  font-weight: 850;
  box-shadow: 0 18px 44px rgba(128, 92, 255, 0.24);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
}

.section-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(320px, 0.8fr);
  gap: 24px;
}

.glass-section {
  padding: 24px;
  border-radius: 30px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-head h2,
.ai-entry h2 {
  margin-top: 6px;
  font-size: 24px;
}

.section-head a {
  color: #6d5dfb;
  font-weight: 850;
}

.event-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 18px;
  padding: 18px;
  border: 1px solid rgba(128, 92, 255, 0.1);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.66);
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease;
}

.event-card + .event-card {
  margin-top: 14px;
}

.event-card:hover {
  box-shadow: 0 18px 42px rgba(93, 73, 220, 0.11);
  transform: translateY(-3px);
}

.event-card h3 {
  font-size: 18px;
}

.event-card p {
  margin-top: 8px;
  color: #94a3b8;
  line-height: 1.65;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
  color: #94a3b8;
  font-size: 13px;
}

.meta em {
  padding: 3px 9px;
  border-radius: 999px;
  font-style: normal;
  font-weight: 800;
}

.positive {
  background: rgba(128, 92, 255, 0.1);
  color: #6d5dfb;
}

.neutral {
  background: rgba(200, 182, 255, 0.18);
  color: #64748b;
}

.risk {
  background: rgba(255, 122, 182, 0.13);
  color: #e84f92;
}

.event-side {
  display: grid;
  align-content: space-between;
  justify-items: end;
}

.event-side strong {
  color: #805cff;
  font-size: 26px;
}

.event-side a {
  padding: 9px 14px;
  border-radius: 999px;
  background: rgba(128, 92, 255, 0.1);
  color: #6d5dfb;
  font-weight: 850;
}

.ai-entry {
  display: grid;
  align-content: start;
  gap: 18px;
}

.chat-input {
  display: flex;
  gap: 10px;
  padding: 8px;
  border: 1px solid rgba(128, 92, 255, 0.13);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.74);
}

.chat-input input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  padding: 0 10px;
  color: #ffffff;
}

.quick-tags,
.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick-tags span,
.keyword-list span {
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(128, 92, 255, 0.1);
  color: #6d5dfb;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: background 0.2s;
}
.quick-tags span:hover {
  background: rgba(128, 92, 255, 0.22);
}
.search-error {
  margin: 8px 0 0;
  color: #fb7185;
  font-size: 12px;
}

.chart-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr) minmax(260px, 0.7fr);
  gap: 18px;
}

.chart-card {
  min-height: 330px;
  padding: 20px;
  border-radius: 24px;
}

.keywords {
  min-height: auto;
}

.keyword-list {
  margin-top: 26px;
}

@media (max-width: 1180px) {
  .metric-grid,
  .chart-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .section-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .hero-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .event-card {
    grid-template-columns: 1fr;
  }

  .event-side {
    justify-items: start;
    gap: 12px;
  }
}
</style>
