<script setup>
import { onMounted, ref } from 'vue'
import { fetchEventsWithFallback } from '@/api/events'

const metrics = [
  { label: '热点事件总数', value: '128', tone: 'purple', icon: '◆' },
  { label: '高风险事件', value: '8', tone: 'orange', icon: '!' },
  { label: '疑似虚假信息', value: '23', tone: 'pink', icon: '?' },
  { label: '今日舆情热度', value: '95.6', tone: 'blue', icon: '↗' },
]

const fallbackEvents = [
  { id: 'new-energy', title: '新能源车辆事件', tag: '科技', heat: '98.6', trend: '↑ 上升', trendClass: 'up' },
  { id: 'summer-tourism', title: '暑期文旅消费热度持续攀升', tag: '社会', heat: '96.8', trend: '↑ 上升', trendClass: 'up' },
  { id: 'ai-phone', title: '新一代 AI 手机引发行业讨论', tag: '科技', heat: '94.2', trend: '↑ 上升', trendClass: 'up' },
  { id: 'graduate-jobs', title: '高校毕业季就业服务受到关注', tag: '教育', heat: '91.7', trend: '↑ 上升', trendClass: 'up' },
  { id: 'public-transit', title: '多地公共交通服务优化升级', tag: '民生', heat: '89.5', trend: '— 持平', trendClass: 'steady' },
  { id: 'domestic-game', title: '国产游戏新品上线表现亮眼', tag: '文娱', heat: '87.3', trend: '↑ 上升', trendClass: 'up' },
  { id: 'food-safety', title: '夏季食品安全专项检查启动', tag: '社会', heat: '84.9', trend: '↑ 上升', trendClass: 'up' },
  { id: 'low-carbon', title: '城市低碳生活方式成为新风尚', tag: '环保', heat: '82.6', trend: '↓ 回落', trendClass: 'down' },
  { id: 'sports-event', title: '国际体育赛事带动全民热议', tag: '体育', heat: '80.4', trend: '↑ 上升', trendClass: 'up' },
  { id: 'health-service', title: '基层医疗服务能力提升计划发布', tag: '健康', heat: '78.1', trend: '— 持平', trendClass: 'steady' },
]

const events = ref(fallbackEvents)

function toHomeEvent(event) {
  const heat = Number(event.heat)
  const heatPercent = Number.isFinite(heat) ? Math.min(100, heat > 100 ? heat / 100 : heat) : 0

  return {
    id: event.id,
    title: event.title,
    tag: event.tags?.[0] ?? event.category ?? event.tag ?? '暂无',
    heat: Number(heatPercent.toFixed(1)),
    trend: event.stage || event.trend || '暂无',
    trendClass: event.sentimentType === 'risk' ? 'down' : event.sentimentType === 'positive' ? 'up' : 'steady',
  }
}

onMounted(async () => {
  events.value = (await fetchEventsWithFallback()).slice(0, 10).map(toHomeEvent)
})

const trendData = [
  { date: '07/05', value: 62.4 }, { date: '07/06', value: 68.7 }, { date: '07/07', value: 65.2 },
  { date: '07/08', value: 76.8 }, { date: '07/09', value: 81.5 }, { date: '07/10', value: 88.3 },
  { date: '07/11', value: 95.6 },
]

const risks = [
  { label: '高风险事件', value: 8, color: '#fb923c' },
  { label: '关注事件', value: 23, color: '#8b5cf6' },
  { label: '正常事件', value: 97, color: '#2dd4bf' },
]
</script>

<template>
  <section class="home-page">
    <section class="metrics" aria-label="数据概览">
      <article v-for="item in metrics" :key="item.label" class="metric-card" :class="item.tone">
        <div class="metric-copy"><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
        <div class="metric-icon">{{ item.icon }}</div>
      </article>
    </section>

    <main class="dashboard-content">
    <section class="hot-card">
      <header class="hot-header">
        <div><span>REAL-TIME HOTSPOTS</span><h1>🔥 实时热点事件 TOP10</h1></div>
        <RouterLink to="/events">查看全部 <b>→</b></RouterLink>
      </header>

      <div class="hot-list">
        <div class="list-head"><span>排名</span><span>热点事件</span><span>领域</span><span>热度指数</span><span>趋势状态</span></div>
        <RouterLink v-for="(event, index) in events" :key="event.id" :to="`/report/${event.id}`" class="hot-row">
          <strong class="rank" :class="{ podium: index < 3 }">{{ String(index + 1).padStart(2, '0') }}</strong>
          <span class="title">{{ event.title }}</span>
          <span><i class="tag">{{ event.tag }}</i></span>
          <span class="heat"><b>{{ event.heat }}</b><i><em :style="{ width: `${event.heat}%` }"></em></i></span>
          <span class="trend" :class="event.trendClass">{{ event.trend }}</span>
        </RouterLink>
      </div>
    </section>

    <aside class="right-column">
      <section class="side-card trend-card">
        <header class="side-header"><div><span>HEAT TREND</span><h2>舆情热度趋势</h2></div><i class="period-tag">近 7 天</i></header>
        <div class="trend-summary"><strong>95.6</strong><span>当前热度<br><b>↑ 8.3%</b></span></div>
        <div class="chart-wrap">
          <div class="y-axis"><span>100</span><span>80</span><span>60</span><span>40</span></div>
          <svg viewBox="0 0 420 190" preserveAspectRatio="none" aria-label="近7天舆情热度折线图">
            <defs><linearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#8b5cf6" stop-opacity=".38"/><stop offset="1" stop-color="#2563eb" stop-opacity="0"/></linearGradient><linearGradient id="trendLine" x1="0" y1="0" x2="1"><stop stop-color="#38bdf8"/><stop offset="1" stop-color="#a78bfa"/></linearGradient></defs>
            <g class="chart-grid"><line v-for="y in [18,68,118,168]" :key="y" x1="0" :y1="y" x2="420" :y2="y"/></g>
            <path class="area" d="M0 117 L70 101 L140 110 L210 81 L280 69 L350 52 L420 32 L420 168 L0 168 Z"/>
            <polyline class="line" points="0,117 70,101 140,110 210,81 280,69 350,52 420,32"/>
            <g class="points"><circle v-for="(item,index) in trendData" :key="item.date" :cx="index*70" :cy="[117,101,110,81,69,52,32][index]" r="4"><title>{{ item.date }}：{{ item.value }}</title></circle></g>
          </svg>
          <div class="x-axis"><span v-for="item in trendData" :key="item.date">{{ item.date }}</span></div>
        </div>
        <div class="trend-values"><span v-for="item in trendData" :key="item.date"><b>{{ item.value }}</b><small>{{ item.date }}</small></span></div>
      </section>

      <section class="side-card risk-card">
        <header class="side-header"><div><span>RISK OVERVIEW</span><h2>风险事件分布</h2></div><i class="period-tag">实时</i></header>
        <div class="risk-content">
          <div class="donut"><div><strong>128</strong><span>事件总数</span></div></div>
          <div class="risk-list"><div v-for="item in risks" :key="item.label"><span><i :style="{background:item.color,boxShadow:`0 0 10px ${item.color}`} "></i>{{ item.label }}</span><strong :style="{color:item.color}">{{ item.value }}</strong></div></div>
        </div>
        <button class="detail-button" type="button">查看风险详情 <span>→</span></button>
      </section>
    </aside>
    </main>

    <footer class="data-footer"><span><i></i>数据来源：全网公开媒体与社交平台</span><span>更新时间：2026-07-11 14:30</span><span>© 2026 舆见 OPINION INSIGHT</span></footer>
  </section>
</template>

<style scoped>
.home-page { display: grid; gap: 22px; max-width: 1480px; margin: 0 auto; color: #e8edff; }
.metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; }
.metric-card { --accent: #8b5cf6; position: relative; display: flex; min-height: 126px; align-items: center; justify-content: space-between; overflow: hidden; padding: 24px 26px; border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent); border-radius: 22px; background: linear-gradient(145deg, rgba(17, 34, 71, .88), rgba(8, 22, 49, .78)); box-shadow: inset 0 1px rgba(255,255,255,.05), 0 18px 46px rgba(1, 7, 25, .26); }
.metric-card::after { position: absolute; right: -38px; bottom: -48px; width: 140px; height: 140px; border-radius: 50%; background: var(--accent); filter: blur(70px); opacity: .28; content: ''; }
.metric-card.orange { --accent: #fb923c; }.metric-card.pink { --accent: #f472b6; }.metric-card.blue { --accent: #38bdf8; }
.metric-copy { display: grid; gap: 5px; }.metric-copy span { color: #95a6c8; font-size: 14px; }.metric-copy strong { color: #fff; font-size: 34px; font-weight: 800; line-height: 1.1; }
.metric-icon { z-index: 1; display: grid; width: 52px; height: 52px; place-items: center; border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent); border-radius: 16px; background: color-mix(in srgb, var(--accent) 12%, transparent); color: var(--accent); font-size: 23px; font-weight: 800; box-shadow: 0 0 24px color-mix(in srgb, var(--accent) 18%, transparent); }
.hot-card { overflow: hidden; border: 1px solid rgba(129, 140, 248, .26); border-radius: 26px; background: linear-gradient(145deg, rgba(15, 31, 68, .9), rgba(7, 20, 45, .84)); box-shadow: inset 0 1px rgba(255,255,255,.05), 0 26px 70px rgba(1, 7, 25, .3); }
.hot-header { display: flex; align-items: center; justify-content: space-between; padding: 24px 28px 18px; border-bottom: 1px solid rgba(125, 145, 190, .13); }
.hot-header span { color: #737df8; font-size: 10px; font-weight: 800; letter-spacing: .2em; }.hot-header h1 { margin: 4px 0 0; color: #fff; font-size: 22px; font-weight: 750; }.hot-header a { color: #90a2c4; font-size: 13px; text-decoration: none; }.hot-header a:hover { color: #a78bfa; }.hot-header b { margin-left: 5px; }
.hot-list { padding: 0 16px 14px; }.list-head, .hot-row { display: grid; grid-template-columns: 80px minmax(280px, 1fr) 120px 180px 120px; align-items: center; gap: 14px; padding: 0 16px; }
.list-head { height: 42px; color: #607499; font-size: 11px; }.hot-row { min-height: 60px; border-top: 1px solid rgba(125, 145, 190, .1); color: inherit; text-decoration: none; transition: background .2s, transform .2s; }.hot-row:hover { border-radius: 13px; background: rgba(99, 102, 241, .1); transform: translateX(3px); }
.rank { color: #60759a; font: 700 16px ui-monospace, monospace; }.rank.podium { color: #b49aff; font-size: 18px; text-shadow: 0 0 14px rgba(139,92,246,.75); }.title { overflow: hidden; color: #e5ebfa; font-size: 14px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.tag { display: inline-block; padding: 4px 10px; border: 1px solid rgba(129, 140, 248, .22); border-radius: 999px; background: rgba(99,102,241,.1); color: #b4bafc; font-size: 11px; font-style: normal; }
.heat { display: flex; align-items: center; gap: 10px; }.heat b { width: 36px; color: #fff; font-size: 13px; }.heat > i { width: 86px; height: 4px; overflow: hidden; border-radius: 5px; background: rgba(100,116,155,.18); }.heat em { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #38bdf8, #8b5cf6); box-shadow: 0 0 8px #6366f1; }
.trend { font-size: 12px; font-weight: 650; }.trend.up { color: #42d9b4; }.trend.down { color: #fb7185; }.trend.steady { color: #94a3b8; }
@media (max-width: 1000px) { .metrics { grid-template-columns: repeat(2, 1fr); }.list-head, .hot-row { grid-template-columns: 58px minmax(220px, 1fr) 90px 110px; }.list-head span:last-child, .trend { display: none; } }
@media (max-width: 640px) { .home-page { gap: 14px; }.metrics { gap: 12px; }.metric-card { min-height: 104px; padding: 18px; }.metric-copy strong { font-size: 28px; }.metric-icon { display: none; }.hot-header { padding: 20px 16px 14px; }.hot-header h1 { font-size: 18px; }.hot-list { padding: 0 8px 10px; }.list-head, .hot-row { grid-template-columns: 46px minmax(160px, 1fr) 64px; gap: 8px; padding: 0 8px; }.list-head span:nth-child(4), .heat { display: none; } }

/* right-side analysis area */
.metric-card,.hot-card { border-radius:20px }.metric-card { transition:transform .22s,border-color .22s,box-shadow .22s }.metric-card:hover,.side-card:hover { transform:translateY(-3px);border-color:rgba(139,92,246,.52);box-shadow:0 22px 55px rgba(1,7,25,.4) }.metric-copy strong { text-shadow:0 0 20px color-mix(in srgb,var(--accent) 55%,transparent) }
.dashboard-content { display:grid;grid-template-columns:minmax(0,1.85fr) minmax(340px,.85fr);gap:20px;align-items:stretch }.dashboard-content .list-head,.dashboard-content .hot-row { grid-template-columns:58px minmax(180px,1fr) 66px 130px 76px;gap:9px;padding-inline:12px }.right-column { display:grid;grid-template-rows:1.08fr .92fr;gap:20px }.side-card { min-height:0;padding:22px;border:1px solid rgba(129,140,248,.25);border-radius:20px;background:linear-gradient(145deg,rgba(15,31,68,.9),rgba(7,20,45,.84));box-shadow:inset 0 1px rgba(255,255,255,.05),0 20px 55px rgba(1,7,25,.28);transition:transform .22s,border-color .22s,box-shadow .22s }
.side-header { display:flex;align-items:center;justify-content:space-between }.side-header span { color:#737df8;font-size:9px;font-weight:800;letter-spacing:.18em }.side-header h2 { margin:3px 0 0;color:#fff;font-size:17px;font-weight:700 }.period-tag { padding:4px 9px;border:1px solid rgba(139,92,246,.28);border-radius:999px;background:rgba(139,92,246,.1);color:#aeb4e9;font-size:10px;font-style:normal }
.trend-summary { display:flex;align-items:center;gap:12px;margin:17px 0 6px }.trend-summary strong { color:#fff;font-size:30px;line-height:1;text-shadow:0 0 22px rgba(56,189,248,.65) }.trend-summary span { color:#7185a9;font-size:10px;line-height:1.5 }.trend-summary b { color:#2dd4bf }.chart-wrap { position:relative;padding:4px 0 22px 26px }.chart-wrap svg { display:block;width:100%;height:150px;overflow:visible }.chart-grid line { stroke:rgba(113,133,174,.16);stroke-width:1 }.area { fill:url(#trendArea) }.line { fill:none;stroke:url(#trendLine);stroke-width:3;filter:drop-shadow(0 0 6px rgba(99,102,241,.8)) }.points circle { fill:#c4b5fd;stroke:#6366f1;stroke-width:2 }.y-axis { position:absolute;top:3px;bottom:22px;left:0;display:flex;flex-direction:column;justify-content:space-between;color:#53698e;font-size:8px }.x-axis { position:absolute;right:0;bottom:0;left:26px;display:flex;justify-content:space-between;color:#617598;font-size:8px }.trend-values { display:grid;grid-template-columns:repeat(7,1fr);gap:3px }.trend-values span { display:grid;justify-items:center;padding:5px 1px;border-radius:7px;background:rgba(99,102,241,.06) }.trend-values b { color:#aeb8d4;font-size:9px }.trend-values small { color:#53698e;font-size:7px }
.risk-content { display:grid;grid-template-columns:140px 1fr;align-items:center;gap:20px;margin:25px 0 }.donut { position:relative;display:grid;width:136px;height:136px;place-items:center;border-radius:50%;background:conic-gradient(#fb923c 0 6.25%,#8b5cf6 6.25% 24.2%,#2dd4bf 24.2% 100%);box-shadow:0 0 28px rgba(99,102,241,.18) }.donut::after { position:absolute;inset:19px;border-radius:50%;background:#0b1c3d;box-shadow:inset 0 0 18px rgba(56,189,248,.08);content:'' }.donut div { z-index:1;display:grid;text-align:center }.donut strong { color:#fff;font-size:27px;line-height:1;text-shadow:0 0 18px rgba(167,139,250,.7) }.donut span { margin-top:5px;color:#7185a9;font-size:9px }.risk-list { display:grid;gap:15px }.risk-list div { display:flex;align-items:center;justify-content:space-between;color:#8fa1c1;font-size:11px }.risk-list span { display:flex;align-items:center }.risk-list i { width:7px;height:7px;margin-right:8px;border-radius:50% }.risk-list strong { font-size:19px;text-shadow:0 0 14px currentColor }.detail-button { width:100%;padding:11px;border:0;border-radius:11px;background:linear-gradient(135deg,#2563eb,#8b5cf6);color:#fff;font-weight:700;cursor:pointer;box-shadow:0 10px 25px rgba(79,70,229,.22);transition:transform .2s,box-shadow .2s }.detail-button:hover { transform:translateY(-2px);box-shadow:0 14px 30px rgba(79,70,229,.36) }.detail-button span { margin-left:6px }
.data-footer { display:flex;align-items:center;gap:28px;padding:4px 8px 0;color:#5f7398;font-size:10px }.data-footer span:last-child { margin-left:auto }.data-footer i { display:inline-block;width:6px;height:6px;margin-right:7px;border-radius:50%;background:#2dd4bf;box-shadow:0 0 8px #2dd4bf }
@media(max-width:1180px){.dashboard-content{grid-template-columns:1fr}.right-column{grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:auto}.dashboard-content .list-head,.dashboard-content .hot-row{grid-template-columns:58px minmax(220px,1fr) 90px 150px 90px}}
@media(max-width:900px){.right-column{grid-template-columns:1fr}.data-footer{flex-wrap:wrap;gap:8px 18px}.data-footer span:last-child{margin-left:0}}
@media(max-width:640px){.risk-content{grid-template-columns:112px 1fr;gap:12px}.donut{width:108px;height:108px}.donut::after{inset:15px}.trend-values{display:none}.dashboard-content .list-head,.dashboard-content .hot-row{grid-template-columns:46px minmax(160px,1fr) 64px}.data-footer span:last-child{width:100%}}

/* visual hierarchy polish */
.home-page { gap:18px }
.metrics { gap:14px }
.metric-card { min-height:96px;padding:17px 20px;background:linear-gradient(145deg,rgba(15,31,68,.58),rgba(7,20,45,.5));border-color:color-mix(in srgb,var(--accent) 22%,transparent);box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 12px 34px rgba(1,7,25,.18);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px) }
.metric-card::after { opacity:.16 }
.metric-copy { gap:2px }.metric-copy span { color:#7e91b2;font-size:12px }.metric-copy strong { font-size:29px }.metric-icon { width:42px;height:42px;border-radius:13px;font-size:18px;opacity:.82 }
.hot-card,.side-card { position:relative;background:linear-gradient(145deg,rgba(15,31,68,.72),rgba(7,20,45,.66));border:1px solid rgba(129,140,248,.28);box-shadow:inset 0 1px 0 rgba(255,255,255,.055),0 20px 60px rgba(1,7,25,.32),0 0 32px rgba(99,102,241,.055);backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px) }
.hot-card::before,.side-card::before { position:absolute;inset:0;z-index:0;border-radius:inherit;background:linear-gradient(120deg,rgba(56,189,248,.035),transparent 38%,rgba(139,92,246,.045));pointer-events:none;content:'' }.hot-card>* ,.side-card>* { position:relative;z-index:1 }
.hot-card { border-color:rgba(139,92,246,.4);box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 25px 70px rgba(1,7,25,.38),0 0 40px rgba(99,102,241,.08) }
.hot-header { padding:22px 24px 16px;background:linear-gradient(90deg,rgba(99,102,241,.07),transparent 58%) }.hot-header span,.side-header span { color:#8b92ff;text-shadow:0 0 13px rgba(99,102,241,.55) }.hot-header h1 { text-shadow:0 0 22px rgba(139,92,246,.18) }
.hot-header a { padding:8px 13px;border:1px solid rgba(129,140,248,.3);border-radius:10px;background:linear-gradient(135deg,rgba(37,99,235,.75),rgba(139,92,246,.72));color:#fff;font-size:11px;font-weight:700;box-shadow:0 8px 20px rgba(79,70,229,.2);transition:transform .2s,box-shadow .2s }.hot-header a:hover { color:#fff;transform:translateY(-2px);box-shadow:0 12px 26px rgba(79,70,229,.34) }
.hot-row { position:relative }.hot-row:hover { background:linear-gradient(90deg,rgba(37,99,235,.11),rgba(139,92,246,.09));box-shadow:inset 3px 0 0 rgba(139,92,246,.62) }
.hot-row:nth-child(2) .rank { color:#ffbf69;text-shadow:0 0 16px rgba(251,146,60,.85) }.hot-row:nth-child(3) .rank { color:#c4b5fd;text-shadow:0 0 16px rgba(167,139,250,.82) }.hot-row:nth-child(4) .rank { color:#67e8f9;text-shadow:0 0 16px rgba(34,211,238,.72) }
.tag { border-color:rgba(139,92,246,.32);background:linear-gradient(135deg,rgba(37,99,235,.13),rgba(139,92,246,.14));box-shadow:inset 0 1px rgba(255,255,255,.04) }.heat>i { height:5px }.heat em { background:linear-gradient(90deg,#22d3ee,#6366f1 58%,#a855f7);box-shadow:0 0 11px rgba(99,102,241,.8) }.trend.up::first-letter,.trend.down::first-letter { text-shadow:0 0 9px currentColor }
.area { opacity:.88;filter:drop-shadow(0 8px 13px rgba(99,102,241,.15)) }.line { stroke-width:3.5;filter:drop-shadow(0 0 4px #38bdf8) drop-shadow(0 0 9px rgba(139,92,246,.72)) }.points circle { fill:#eef2ff;stroke:#8b5cf6;stroke-width:2.5;filter:drop-shadow(0 0 4px #38bdf8) drop-shadow(0 0 7px #8b5cf6) }.chart-grid line { stroke:rgba(129,140,248,.14);stroke-dasharray:3 4 }
.trend-values span { border:1px solid rgba(129,140,248,.07);background:rgba(99,102,241,.075) }.trend-values b { color:#cad2e8;text-shadow:0 0 9px rgba(129,140,248,.35) }
.data-footer { margin-top:-2px;padding:8px 10px;border-top:1px solid rgba(129,140,248,.1);color:#63779b }
@media(max-width:640px){.metric-card{min-height:88px;padding:14px 16px}.metric-copy strong{font-size:26px}}
</style>
