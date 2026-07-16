<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { fetchEventsWithFallback, getEvents, normalizeEventItem } from '@/api/events'

const activeSort = ref('按热度排序')
const activeTime = ref('今天')
const activeField = ref('全部领域')

const sortOptions = [
  { label: '按热度排序', icon: '🔥' },
  { label: '按时间排序', icon: '🕒' },
]
const timeOptions = ['今天', '昨天', '近7天', '近30天']
const fieldOptions = ['全部领域', '社会民生', '政治政策', '经济财经', '科技互联网', '体育赛事', '娱乐明星', '教育考试','健康医疗','灾害事故','国际事件','其他']

const fallbackEvents = [
  ['ev', '新能源汽车事件', ['科技', '政策'], '2026-07-11 14:42', '98.6', '高潮期', '中性', 52, 256],
  ['ai-chip', '国产 AI 芯片技术取得新突破', ['科技', '产业'], '2026-07-11 14:26', '96.8', '爆发期', '正面', 68, 218],
  ['city', '城市文旅消费热度持续攀升', ['社会', '财经'], '2026-07-11 13:58', '94.2', '高潮期', '正面', 71, 196],
  ['market', '多部门发布促进消费新政策', ['财经', '政策'], '2026-07-11 13:31', '91.7', '扩散期', '中性', 57, 183],
  ['weather', '多地启动高温天气应急响应', ['社会', '民生'], '2026-07-11 12:54', '88.5', '爆发期', '中性', 61, 169],
  ['space', '商业航天新型运载火箭完成测试', ['科技', '国际'], '2026-07-11 12:20', '85.9', '扩散期', '正面', 76, 148],
  ['education', '高校毕业生就业服务专项行动启动', ['教育', '社会'], '2026-07-11 11:46', '82.3', '上升期', '正面', 65, 132],
  ['sports', '国际赛事中国队刷新赛季最佳成绩', ['体育', '国际'], '2026-07-11 11:08', '79.6', '扩散期', '正面', 81, 119],
  ['film', '暑期档电影市场票房加速增长', ['娱乐', '财经'], '2026-07-11 10:35', '76.4', '上升期', '中性', 59, 104],
  ['health', '公共健康科普行动引发广泛关注', ['社会', '健康'], '2026-07-11 09:52', '73.8', '萌芽期', '正面', 72, 87],
].map(([id, title, tags, time, heat, stage, sentiment, sentimentRate, news], index) => ({
  id,
  rank: String(index + 1).padStart(2, '0'),
  title,
  tags,
  time,
  heat,
  stage,
  sentiment,
  sentimentRate,
  news,
}))

const events = ref(fallbackEvents.map(normalizeEventItem))
const loading = ref(false)

// 时间筛选 → start_time / end_time
const timeRange = computed(() => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`

  switch (activeTime.value) {
    case '今天': {
      const today = fmt(now)
      return { start_time: today, end_time: '' }
    }
    case '昨天': {
      const yesterday = new Date(now)
      yesterday.setDate(yesterday.getDate() - 1)
      const d = fmt(yesterday)
      return { start_time: d, end_time: d }
    }
    case '近7天': {
      const weekAgo = new Date(now)
      weekAgo.setDate(weekAgo.getDate() - 7)
      return { start_time: fmt(weekAgo), end_time: '' }
    }
    case '近30天': {
      const monthAgo = new Date(now)
      monthAgo.setDate(monthAgo.getDate() - 30)
      return { start_time: fmt(monthAgo), end_time: '' }
    }
    default:
      return { start_time: '', end_time: '' }
  }
})

async function loadEvents() {
  loading.value = true
  try {
    const params = {}
    if (activeField.value !== '全部领域') {
      params.category = activeField.value
    }
    const { start_time, end_time } = timeRange.value
    if (start_time) params.start_time = start_time
    if (end_time) params.end_time = end_time

    if (Object.keys(params).length > 0) {
      // 有筛选条件 → 调 4号 /api/events?...
      const payload = await getEvents(params)
      const list = payload?.events ?? payload?.data?.events ?? payload?.items ?? []
      events.value = (Array.isArray(list) ? list : []).map(normalizeEventItem)
    } else {
      // 无筛选 → 全量
      events.value = await fetchEventsWithFallback()
    }
  } catch {
    events.value = await fetchEventsWithFallback()
  } finally {
    loading.value = false
  }
}

// 筛选条件变化时重新加载
watch([activeTime, activeField], () => {
  loadEvents()
})

// 排序：纯前端，不重新请求
const sortedEvents = computed(() => {
  const list = [...events.value]
  if (activeSort.value === '按时间排序') {
    return list.sort((a, b) => String(b.time || '').localeCompare(String(a.time || '')))
  }
  // 按热度排序（默认）
  return list.sort((a, b) => (Number(b.heat) || 0) - (Number(a.heat) || 0))
})

onMounted(async () => {
  events.value = await fetchEventsWithFallback()
})
</script>

<template>
  <section class="hot-event-page">
    <header class="title-area">
      <div>
        <span class="title-eyebrow">HOT EVENTS</span>
        <h1><span aria-hidden="true">🔥</span> 热点事件</h1>
        <p>全网热点事件实时监测与追踪</p>
      </div>
      <div class="update-time">
        <span><i></i> 数据更新时间</span>
        <strong>2026-07-11 15:30</strong>
      </div>
    </header>

    <div class="content-layout">
      <aside class="filter-panel">
        <div class="filter-title">
          <span class="filter-icon" aria-hidden="true">≡</span>
          <div><strong>事件筛选</strong><small>EVENT FILTER</small></div>
        </div>

        <div class="filter-group">
          <label>排序方式</label>
          <button
            v-for="option in sortOptions"
            :key="option.label"
            type="button"
            class="sort-option"
            :class="{ active: activeSort === option.label }"
            @click="activeSort = option.label"
          >
            <span><i>{{ option.icon }}</i>{{ option.label }}</span>
          </button>
        </div>

        <div class="filter-group filter-section">
          <label>时间范围</label>
          <button
            v-for="option in timeOptions"
            :key="option"
            type="button"
            :class="{ active: activeTime === option }"
            @click="activeTime = option"
          >
            <span>{{ option }}</span>
            <b v-if="activeTime === option">✓</b>
          </button>
        </div>

        <div class="filter-group filter-section">
          <label>领域筛选</label>
          <button
            v-for="option in fieldOptions"
            :key="option"
            type="button"
            :class="{ active: activeField === option }"
            @click="activeField = option"
          >
            <span>{{ option }}</span>
            <b v-if="activeField === option">✓</b>
          </button>
        </div>
      </aside>

      <main class="event-section">
        <div class="list-toolbar">
          <div><strong>实时热点 TOP10</strong><span>共找到 {{ events.length }} 个热点事件</span><span v-if="loading" class="loading-hint">加载中...</span></div>
          <div class="view-switch" aria-label="视图切换">
            <button class="active" type="button"><span aria-hidden="true">☷</span> 列表视图</button>
            <button type="button"><span aria-hidden="true">▦</span> 卡片视图</button>
          </div>
        </div>

        <div class="event-list">
          <article v-for="event in sortedEvents" :key="event.id" class="event-card event-row">
            <div class="rank" :class="{ top: Number(event.rank) < 4 }">{{ event.rank }}</div>
            <div class="event-copy">
              <h2>{{ event.title }}</h2>
              <div class="tags"><span v-for="tag in event.tags" :key="tag">{{ tag }}</span></div>
            </div>
            <time>{{ event.time }}</time>
            <div class="row-metric heat-metric">
              <small>热度指数</small>
              <strong>{{ event.heat }}</strong>
            </div>
            <div class="row-metric"><small>生命周期阶段</small><span class="stage">{{ event.stage }}</span></div>
            <div class="row-metric"><small>情感倾向</small><span>{{ event.sentiment }} <b>{{ event.sentimentRate }}%</b></span></div>
            <div class="row-metric"><small>相关新闻</small><span><b>{{ event.news }}</b> 篇</span></div>
            <RouterLink class="analysis-button" :to="`/report/${event.id}`">查看分析 <span>→</span></RouterLink>
          </article>
        </div>
      </main>
    </div>
  </section>
</template>

<style scoped>
.hot-event-page{position:relative;max-width:1440px;margin:0 auto;color:#e9edff}.hot-event-page::before{position:fixed;inset:76px 0 0;z-index:-1;background:radial-gradient(circle at 74% 5%,rgba(99,102,241,.13),transparent 27%),linear-gradient(145deg,rgba(5,11,36,.9),rgba(7,22,47,.65));content:""}.title-area{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:24px;padding:2px 2px 0}.title-area h1{margin:0;color:#fff;font-size:clamp(28px,3vw,40px);font-weight:800;letter-spacing:-.03em}.title-area h1 span{display:inline-block;margin-right:7px;font-size:.78em;filter:drop-shadow(0 0 12px rgba(168,85,247,.5))}.title-area p{margin:6px 0 0;color:#7f90b1;font-size:14px}.live-status{display:flex;align-items:center;gap:8px;margin-bottom:5px;color:#8998b7;font-size:12px}.live-status i{width:7px;height:7px;border-radius:50%;background:#8b5cf6;box-shadow:0 0 0 5px rgba(139,92,246,.12),0 0 14px #8b5cf6}.content-layout{display:grid;grid-template-columns:minmax(218px,20%) minmax(0,80%);gap:20px;align-items:start}.filter-panel,.event-card{border:1px solid rgba(129,140,248,.16);background:rgba(15,30,70,.65);box-shadow:0 18px 50px rgba(1,5,24,.25);backdrop-filter:blur(20px)}.filter-panel{position:sticky;top:110px;overflow:hidden;padding:20px;border-radius:18px}.filter-title{display:flex;align-items:center;gap:11px;padding-bottom:17px;border-bottom:1px solid rgba(129,140,248,.12)}.filter-icon{display:grid;width:36px;height:36px;place-items:center;border-radius:11px;background:linear-gradient(135deg,#6366f1,#a855f7);color:#fff;font-size:22px;font-weight:800}.filter-title strong,.filter-title small{display:block}.filter-title strong{color:#fff;font-size:15px;font-weight:700}.filter-title small{margin-top:1px;color:#5f7196;font-size:8px;font-weight:800;letter-spacing:.18em}.filter-group{display:grid;gap:6px;margin-top:18px}.filter-group label{margin-bottom:4px;color:#687b9f;font-size:11px;font-weight:700;letter-spacing:.06em}.filter-group button{display:flex;align-items:center;justify-content:space-between;width:100%;padding:9px 11px;border:1px solid transparent;border-radius:10px;background:transparent;color:#91a1bf;font:inherit;font-size:12px;cursor:pointer;transition:.2s}.filter-group button em{color:#586b90;font-size:10px;font-style:normal}.filter-group button:hover,.filter-group button.active{border-color:rgba(139,92,246,.25);background:linear-gradient(90deg,rgba(99,102,241,.2),rgba(168,85,247,.08));color:#fff}.filter-group button.active::before{position:absolute;left:0;width:3px;height:24px;border-radius:0 4px 4px 0;background:#8b5cf6;content:""}.filter-group button.active em{color:#b8a9ff}.compact{margin-top:17px}.select-like{display:flex;align-items:center;justify-content:space-between;padding:9px 11px;border:1px solid rgba(129,140,248,.15);border-radius:10px;background:rgba(5,11,36,.34);color:#a8b4ce;font-size:11px}.trend-options{display:grid;grid-template-columns:repeat(3,1fr);padding:3px;border-radius:10px;background:rgba(5,11,36,.34)}.trend-options span{padding:6px 2px;border-radius:7px;color:#617397;font-size:10px;text-align:center}.trend-options .selected{background:rgba(99,102,241,.22);color:#c9c6ff}.monitor-card{margin-top:18px;padding:14px;border:1px solid rgba(168,85,247,.16);border-radius:13px;background:linear-gradient(135deg,rgba(99,102,241,.13),rgba(168,85,247,.08))}.monitor-card span,.monitor-card small,.monitor-card strong{display:block}.monitor-card span{color:#7f90b1;font-size:10px}.monitor-card strong{margin:1px 0;color:#fff;font-size:25px;font-weight:800}.monitor-card small{color:#766f9e;font-size:9px}.event-section{min-width:0}.list-toolbar{display:flex;align-items:center;justify-content:space-between;height:44px;padding:0 4px}.list-toolbar>div:first-child{display:flex;align-items:baseline;gap:12px}.list-toolbar strong{color:#fff;font-size:15px;font-weight:700}.list-toolbar div span{color:#66799d;font-size:10px}.sort-control{padding:7px 11px;border:1px solid rgba(129,140,248,.14);border-radius:9px;background:rgba(11,31,68,.6);color:#93a1bc;font-size:10px}.event-list{display:grid;gap:12px}.event-card{position:relative;display:grid;grid-template-columns:54px minmax(0,1fr) 135px;gap:17px;align-items:center;min-height:128px;padding:18px 20px;border-radius:18px;color:inherit;text-decoration:none;transition:border-color .2s,transform .2s,box-shadow .2s}.event-card:hover{border-color:rgba(139,92,246,.48);background:linear-gradient(115deg,rgba(15,30,70,.78),rgba(30,28,83,.7));box-shadow:0 18px 48px rgba(79,70,229,.14);transform:translateY(-2px)}.rank{display:grid;width:45px;height:45px;place-items:center;border:1px solid rgba(129,140,248,.16);border-radius:13px;background:rgba(7,22,47,.55);color:#7587a9;font-size:14px;font-weight:800}.rank.top{border-color:rgba(168,85,247,.3);background:linear-gradient(135deg,rgba(99,102,241,.25),rgba(168,85,247,.16));color:#c4b5fd;box-shadow:inset 0 0 18px rgba(139,92,246,.08)}.event-heading{display:flex;align-items:center;gap:10px}.event-heading h2{overflow:hidden;margin:0;color:#f6f7ff;font-size:16px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.tone{flex:none;padding:3px 7px;border-radius:6px;font-size:9px}.tone.负面{background:rgba(244,63,94,.12);color:#fb7185}.tone.正面{background:rgba(52,211,153,.12);color:#6ee7b7}.tone.中性{background:rgba(99,102,241,.14);color:#a5b4fc}.event-copy>p{overflow:hidden;margin:7px 0 0;color:#8292b0;font-size:11px;line-height:1.65;text-overflow:ellipsis;white-space:nowrap}.event-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:12px}.tags,.meta{display:flex;align-items:center;gap:7px;min-width:0}.tags span{padding:3px 7px;border-radius:6px;background:rgba(99,102,241,.1);color:#9096d6;font-size:9px;white-space:nowrap}.meta{color:#5f7194;font-size:9px;white-space:nowrap}.heat-block{position:relative;display:grid;justify-items:end;padding-right:20px;border-left:1px solid rgba(129,140,248,.11)}.heat-block small{color:#657797;font-size:9px}.heat-block strong{margin:2px 0;color:#c4b5fd;font-size:19px;font-weight:800}.heat-block span{color:#6ee7b7;font-size:9px}.heat-block i{position:absolute;right:0;top:50%;color:#56698e;font-size:25px;font-style:normal;transform:translateY(-50%)}
.filter-panel{padding:20px 18px 18px;background:linear-gradient(155deg,rgba(15,30,70,.78),rgba(7,22,47,.68));box-shadow:0 22px 55px rgba(1,5,24,.34),inset 0 1px 0 rgba(255,255,255,.035)}
.filter-title{padding:0 3px 17px}.filter-icon{width:34px;height:34px;background:linear-gradient(135deg,#6366f1,#a855f7);font-size:19px;box-shadow:0 8px 22px rgba(99,102,241,.25)}
.filter-group{gap:7px;margin-top:17px}.filter-group label{margin:0 4px 3px;color:#7182a4;font-size:10px;font-weight:750;letter-spacing:.1em}
.filter-group button{position:relative;min-height:36px;padding:8px 11px;border-color:rgba(129,140,248,.08);background:rgba(5,11,36,.2);color:#9aa9c5;font-size:11px;text-align:left}
.filter-group button span{display:flex;align-items:center;gap:8px}.filter-group button span i{width:18px;font-size:13px;font-style:normal;text-align:center;filter:saturate(.85)}
.filter-group button b{color:#ddd6fe;font-size:10px;font-weight:800}.filter-group button:hover{border-color:rgba(139,92,246,.3);background:rgba(99,102,241,.1);color:#fff}
.filter-group button.active{border-color:rgba(167,139,250,.34);background:linear-gradient(110deg,rgba(99,102,241,.82),rgba(168,85,247,.7));color:#fff;box-shadow:0 8px 20px rgba(79,70,229,.18),inset 0 1px 0 rgba(255,255,255,.11)}
.filter-group button.active::before{display:none}.filter-section{padding-top:16px;border-top:1px solid rgba(129,140,248,.11)}
.event-section .event-list{overflow:hidden;gap:0;border:1px solid rgba(129,140,248,.16);border-radius:18px;background:rgba(15,30,70,.48);box-shadow:0 18px 50px rgba(1,5,24,.25);backdrop-filter:blur(20px)}
.event-section .event-row{display:grid;grid-template-columns:46px minmax(180px,1.6fr) 116px 70px 92px 86px 70px 92px;gap:10px;min-height:80px;padding:12px 14px;border:0;border-bottom:1px solid rgba(129,140,248,.11);border-radius:0;background:transparent;box-shadow:none;backdrop-filter:none}
.event-section .event-row:last-child{border-bottom:0}.event-section .event-row:hover{border-color:rgba(139,92,246,.25);background:linear-gradient(90deg,rgba(99,102,241,.09),rgba(168,85,247,.035));box-shadow:none;transform:none}
.event-row .rank{width:38px;height:38px;border-radius:11px;font-size:12px}.event-row:nth-child(1) .rank{border-color:rgba(250,204,21,.42);background:linear-gradient(135deg,rgba(245,158,11,.28),rgba(234,88,12,.13));color:#fde68a}.event-row:nth-child(2) .rank{border-color:rgba(203,213,225,.35);background:linear-gradient(135deg,rgba(148,163,184,.24),rgba(100,116,139,.12));color:#e2e8f0}.event-row:nth-child(3) .rank{border-color:rgba(251,146,60,.35);background:linear-gradient(135deg,rgba(194,65,12,.26),rgba(124,45,18,.12));color:#fdba74}
.event-row .event-copy{min-width:0}.event-row .event-copy h2{overflow:hidden;margin:0;color:#f5f7ff;font-size:13px;font-weight:700;text-overflow:ellipsis;white-space:nowrap}.event-row .tags{gap:5px;margin-top:7px}.event-row .tags span{padding:2px 6px;border:1px solid rgba(129,140,248,.1);background:rgba(99,102,241,.1);font-size:8px}.event-row time{color:#7384a5;font-size:9px;white-space:nowrap}
.row-metric{display:grid;gap:3px;align-content:center}.row-metric small{color:#5f7194;font-size:8px;white-space:nowrap}.row-metric span{color:#aeb9d0;font-size:10px;white-space:nowrap}.row-metric b{color:#c4b5fd;font-weight:750}.row-metric .stage{width:max-content;padding:3px 7px;border-radius:6px;background:rgba(99,102,241,.12);color:#a5b4fc}.heat-metric strong{color:#c4b5fd;font-size:17px;font-weight:850;text-shadow:0 0 16px rgba(139,92,246,.35)}
.analysis-button{display:flex;align-items:center;justify-content:center;gap:4px;padding:8px 9px;border:1px solid rgba(167,139,250,.28);border-radius:9px;background:linear-gradient(135deg,rgba(99,102,241,.8),rgba(168,85,247,.72));color:#fff;font-size:9px;font-weight:700;text-decoration:none;white-space:nowrap;box-shadow:0 7px 17px rgba(79,70,229,.16);transition:.2s}.analysis-button:hover{border-color:rgba(196,181,253,.65);box-shadow:0 9px 21px rgba(99,102,241,.28);transform:translateY(-1px)}.analysis-button span{font-size:12px}
.title-eyebrow{display:block;margin-bottom:5px;color:#8b8cf8;font-size:9px;font-weight:850;letter-spacing:.24em;text-shadow:0 0 16px rgba(99,102,241,.45)}.update-time{display:grid;justify-items:end;gap:3px;margin-bottom:2px}.update-time span{display:flex;align-items:center;gap:7px;color:#66799d;font-size:9px}.update-time i{width:6px;height:6px;border-radius:50%;background:#8b5cf6;box-shadow:0 0 0 4px rgba(139,92,246,.1),0 0 11px rgba(139,92,246,.8)}.update-time strong{color:#b8c2d8;font-size:12px;font-weight:650;letter-spacing:.03em}
.view-switch{display:flex;gap:4px;padding:3px;border:1px solid rgba(129,140,248,.13);border-radius:10px;background:rgba(5,11,36,.35)}.view-switch button{display:flex;align-items:center;gap:5px;padding:6px 9px;border:0;border-radius:7px;background:transparent;color:#7182a3;font:inherit;font-size:9px;cursor:pointer;transition:.2s}.view-switch button:hover{color:#c4cce0}.view-switch button.active{background:linear-gradient(135deg,rgba(99,102,241,.32),rgba(139,92,246,.22));color:#d9d7ff;box-shadow:inset 0 0 0 1px rgba(167,139,250,.16)}
.event-section .event-list{border-color:rgba(129,140,248,.2);background:linear-gradient(145deg,rgba(15,30,70,.66),rgba(7,22,47,.58));box-shadow:0 22px 58px rgba(1,5,24,.32),inset 0 1px 0 rgba(255,255,255,.025)}.event-section .event-row{position:relative;transition:transform .2s ease,border-color .2s ease,background .2s ease,box-shadow .2s ease;will-change:transform}.event-section .event-row:hover{z-index:2;border-color:rgba(139,92,246,.5);background:linear-gradient(90deg,rgba(38,45,105,.72),rgba(28,28,82,.64));box-shadow:0 9px 25px rgba(79,70,229,.2),inset 0 0 0 1px rgba(167,139,250,.2),0 0 22px rgba(99,102,241,.09);transform:translateY(-2px)}
.event-row .tags span{padding:3px 8px;border-color:rgba(139,92,246,.18);border-radius:999px;background:linear-gradient(135deg,rgba(99,102,241,.14),rgba(168,85,247,.08));color:#a9a8e7}.heat-metric strong{color:#bdb6ff;text-shadow:0 0 7px rgba(99,102,241,.75),0 0 18px rgba(139,92,246,.48),0 0 30px rgba(59,130,246,.2)}
@media(max-width:1000px){.content-layout{grid-template-columns:230px minmax(0,1fr)}.event-card{grid-template-columns:45px minmax(0,1fr) 110px;padding-inline:14px}.event-footer{align-items:flex-start;flex-direction:column}.meta{display:none}}
@media(max-width:760px){.title-area{align-items:flex-start;flex-direction:column;gap:10px}.content-layout{grid-template-columns:1fr}.filter-panel{position:static}.filter-group:first-of-type{grid-template-columns:repeat(2,1fr)}.filter-group label{grid-column:1/-1}.monitor-card{display:none}.event-card{grid-template-columns:42px minmax(0,1fr)}.heat-block{display:none}.event-heading h2{white-space:normal}.event-copy>p{display:-webkit-box;white-space:normal;-webkit-box-orient:vertical;-webkit-line-clamp:2}.tags span:nth-child(3){display:none}}
</style>
