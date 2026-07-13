<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  eventId: {
    type: String,
    default: '',
  },
})

const router = useRouter()
const fallbackText = '暂未提供'
const allowedVerdicts = ['可信', '待验证', '疑似虚假']

const valueOrFallback = (value) => (value === undefined || value === null || value === '' ? fallbackText : value)
const normalizeVerdict = (verdict) => {
  if (allowedVerdicts.includes(verdict)) return verdict
  if (['假新闻', '虚假', '不可信', 'fake'].includes(String(verdict).toLowerCase())) return '疑似虚假'
  return '待验证'
}
const newsItems = computed(() =>
  (Array.isArray(props.data) ? props.data : []).map((item) => ({
    articleId: item.article_id ?? item.id,
    title: valueOrFallback(item.title),
    source: valueOrFallback(item.source),
    publishTime: valueOrFallback(item.publish_time ?? item.time),
    verdict: normalizeVerdict(item.verdict ?? item.status),
    confidenceScore: valueOrFallback(item.confidence_score),
    fakeProbability: valueOrFallback(item.fake_probability),
  })),
)

function openNews(news) {
  if (!news.articleId) return
  router.push({
    path: `/news/${news.articleId}`,
    query: props.eventId ? { eventId: props.eventId } : {},
  })
}

function onKeydown(event, news) {
  if (event.key === 'Enter' || event.key === ' ') openNews(news)
}
</script>

<template>
  <section class="card">
    <div class="title"><h2>相关新闻</h2><span>事件分析数据来源</span></div>
    <div class="list">
      <article
        v-for="news in newsItems"
        :key="news.articleId || news.title"
        role="link"
        tabindex="0"
        @click="openNews(news)"
        @keydown="onKeydown($event, news)"
      >
        <div class="news-main">
          <h3>{{ news.title }}</h3>
          <p><span>{{ news.source }}</span><time>{{ news.publishTime }}</time></p>
        </div>
        <div class="scores">
          <span>可信度 {{ news.confidenceScore }}</span>
          <span>疑似虚假 {{ news.fakeProbability }}</span>
        </div>
        <b :class="news.verdict">{{ news.verdict }}</b>
        <i>→</i>
      </article>
    </div>
  </section>
</template>

<style scoped>
.card { padding: 22px; border: 1px solid var(--line); border-radius: 20px; background: var(--card); backdrop-filter: blur(18px); }
.title { display: flex; justify-content: space-between; align-items: center; }
.title h2 { margin: 0; color: #fff; font-size: 18px; }
.title span { color: #7183a3; font-size: 11px; }
.list { display: grid; margin-top: 13px; }
.list article { display: grid; grid-template-columns: minmax(0, 1fr) auto auto 20px; gap: 16px; align-items: center; padding: 15px 8px; border-top: 1px solid rgba(129, 140, 248, .1); cursor: pointer; transition: .2s; }
.list article:hover { padding-left: 13px; background: rgba(99, 102, 241, .06); }
.news-main { min-width: 0; }
h3 { margin: 0; overflow: hidden; color: #cad5eb; font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
p { display: flex; gap: 18px; margin: 7px 0 0; color: #64748b; font-size: 10px; }
.scores { display: grid; gap: 4px; color: #8ea0bd; font-size: 10px; white-space: nowrap; }
article > b { padding: 4px 9px; border-radius: 99px; font-size: 10px; font-weight: 600; white-space: nowrap; }
.可信 { background: rgba(45, 212, 191, .12); color: #5eead4; }
.待验证 { background: rgba(167, 139, 250, .14); color: #c4b5fd; }
.疑似虚假 { background: rgba(251, 146, 60, .14); color: #fdba74; }
article > i { color: #6366f1; font-style: normal; }
@media (max-width: 700px) { .list article { grid-template-columns: 1fr auto; } .scores { grid-column: 1 / -1; grid-template-columns: repeat(2, minmax(0, 1fr)); } .list article > i { display: none; } p { display: grid; gap: 3px; } }
</style>
