<template>
  <section class="events-page">
    <div class="page-title">
      <span>Hot Discovery</span>
      <h1>热点事件列表</h1>
      <p>像浏览热搜一样发现事件，同时看到来源、热度、情感变化和 AI 可分析线索。</p>
    </div>

    <div class="filter-bar">
      <button class="active">全部热点</button>
      <button>新闻平台</button>
      <button>社交平台</button>
      <button>内容社区</button>
    </div>

    <div class="event-list">
      <article v-for="event in hotEvents" :key="event.id" class="event-row">
        <div class="rank">{{ event.heat.toString().slice(0, 2) }}</div>
        <div class="event-main">
          <h2>{{ event.title }}</h2>
          <p>{{ event.summary }}</p>
          <div class="tags">
            <span v-for="tag in event.tags" :key="tag">#{{ tag }}</span>
          </div>
          <div class="meta">
            <span>{{ event.source }}</span>
            <span>{{ event.time }}</span>
            <em :class="event.sentimentType">{{ event.sentiment }}</em>
          </div>
        </div>
        <div class="heat">
          <span>热度</span>
          <strong>{{ event.heat }}</strong>
          <RouterLink :to="`/events/${event.id}`">查看详情</RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { hotEvents as mockHotEvents } from '@/data/mockOpinion'
import { fetchEventsWithFallback, normalizeEventItem } from '@/api/events'

const hotEvents = ref(mockHotEvents.map(normalizeEventItem))

onMounted(async () => {
  hotEvents.value = await fetchEventsWithFallback()
})
</script>

<style scoped>
.events-page {
  display: grid;
  gap: 22px;
}

.page-title,
.filter-bar,
.event-row {
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 24px 70px rgba(93, 73, 220, 0.1);
  backdrop-filter: blur(20px);
}

.page-title {
  padding: 32px;
  border-radius: 32px;
}

.page-title span {
  color: #805cff;
  font-weight: 900;
}

.page-title h1 {
  margin: 8px 0;
  font-size: clamp(32px, 4vw, 48px);
}

.page-title p {
  max-width: 720px;
  margin: 0;
  color: #94a3b8;
  line-height: 1.8;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 14px;
  border-radius: 24px;
}

.filter-bar button {
  padding: 11px 16px;
  border-radius: 999px;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  font-weight: 800;
}

.filter-bar .active,
.filter-bar button:hover {
  background: linear-gradient(135deg, #805cff, #6d5dfb);
  color: #fff;
}

.event-list {
  display: grid;
  gap: 16px;
}

.event-row {
  display: grid;
  grid-template-columns: 76px 1fr 150px;
  gap: 22px;
  align-items: center;
  padding: 22px;
  border-radius: 28px;
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease;
}

.event-row:hover {
  box-shadow: 0 30px 78px rgba(93, 73, 220, 0.16);
  transform: translateY(-4px);
}

.rank {
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  border-radius: 20px;
  background: rgba(128, 92, 255, 0.1);
  color: #805cff;
  font-size: 22px;
  font-weight: 900;
}

h2,
p {
  margin: 0;
}

h2 {
  font-size: 22px;
}

.event-main p {
  margin-top: 9px;
  color: #94a3b8;
  line-height: 1.7;
}

.tags,
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 13px;
}

.tags span {
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(200, 182, 255, 0.2);
  color: #6d5dfb;
  font-size: 13px;
  font-weight: 800;
}

.meta {
  color: #94a3b8;
  font-size: 13px;
}

.meta em {
  padding: 2px 9px;
  border-radius: 999px;
  font-style: normal;
  font-weight: 850;
}

.positive {
  background: rgba(128, 92, 255, 0.11);
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

.heat {
  display: grid;
  justify-items: end;
  gap: 8px;
}

.heat span {
  color: #94a3b8;
  font-size: 13px;
}

.heat strong {
  color: #805cff;
  font-size: 30px;
}

.heat a {
  padding: 10px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, #805cff, #6d5dfb);
  color: #fff;
  text-decoration: none;
  font-weight: 850;
}

@media (max-width: 760px) {
  .event-row {
    grid-template-columns: 1fr;
  }

  .heat {
    justify-items: start;
  }
}

/* dark blue technology news theme */
.page-title,
.filter-bar,
.event-row {
  border-color: rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(145deg, rgba(15, 30, 58, 0.84), rgba(8, 20, 38, 0.72)),
    rgba(15, 30, 58, 0.75);
  box-shadow: 0 24px 70px rgba(0, 217, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.page-title span,
.rank,
.heat strong {
  color: #38bdf8;
}

.page-title h1,
h2 {
  color: #ffffff;
}

.page-title p,
.event-main p,
.meta,
.heat span {
  color: #94a3b8;
}

.filter-bar button {
  color: #cbd5e1;
}

.filter-bar .active,
.filter-bar button:hover,
.heat a {
  background: linear-gradient(135deg, #2563eb, #8b5cf6);
  color: #ffffff;
}

.rank,
.tags span {
  background: rgba(37, 99, 235, 0.16);
  border: 1px solid rgba(56, 189, 248, 0.16);
}

.tags span {
  color: #93c5fd;
}

.event-row:hover {
  box-shadow: 0 30px 78px rgba(37, 99, 235, 0.2);
}

.positive {
  background: rgba(37, 99, 235, 0.18);
  color: #93c5fd;
}

.neutral {
  background: rgba(0, 217, 255, 0.14);
  color: #67e8f9;
}

.risk {
  background: rgba(255, 77, 141, 0.16);
  color: #ff8ab5;
}
</style>
