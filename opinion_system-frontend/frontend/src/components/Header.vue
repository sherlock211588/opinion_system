<template>
  <header class="global-header">
    <RouterLink class="brand" to="/home" aria-label="舆见首页">
      <span class="brand-text">舆见</span>
    </RouterLink>

    <nav class="main-nav" aria-label="主导航">
      <RouterLink
        v-for="item in navItems"
        :key="item.label"
        :to="item.to"
        :class="{ active: isActive(item) }"
      >
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="header-actions">
      <form class="search" role="search" @submit.prevent="submitSearch">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m16.5 16.5 4 4"/></svg>
        <input v-model="keyword" type="search" placeholder="搜索事件 / 新闻 / 关键词" aria-label="全站搜索" />
      </form>
      <button class="ai-button" type="button" @click="$emit('open-assistant')">
        <span aria-hidden="true">✦</span> AI 助手
      </button>
      <button class="avatar" type="button" aria-label="个人中心" @click="openProfile">
        {{ userStore.displayAvatar }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useLoginPromptStore } from '@/stores/loginPrompt'
import { searchSimilarEvents } from '@/api/analysis'

defineOptions({ name: 'GlobalHeader' })
defineEmits(['open-assistant'])

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loginPrompt = useLoginPromptStore()
const keyword = ref('')

const navItems = [
  { label: '首页', to: '/home', match: (path) => path === '/home' },
  { label: '热点事件', to: '/events', match: (path) => path === '/events' || path.startsWith('/events/') },
  { label: '分析报告', to: '/report/ev', match: (path) => path.startsWith('/report/') },
  { label: '新闻详情', to: '/news/1', match: (path) => path.startsWith('/news/') },
  { label: '社区', to: '/community', match: (path) => path === '/community' },
]

function isActive(item) {
  return item.match(route.path)
}

async function submitSearch() {
  const q = keyword.value.trim()
  if (!q) return
  try {
    const results = await searchSimilarEvents(q, 5)
    if (results && results.length > 0 && results[0].similarity > 0.05) {
      router.push(`/report/${results[0].event_id}`)
    } else {
      router.push({ path: '/events', query: { q } })
    }
  } catch {
    router.push({ path: '/events', query: { q } })
  }
}

function openProfile() {
  if (userStore.isLoggedIn || userStore.isGuest) {
    router.push('/profile')
    return
  }

  loginPrompt.openLogin({
    redirect: '/profile',
    message: '请先登录后继续访问个人中心',
  })
}
</script>

<style scoped>
.global-header { position:sticky;top:0;z-index:50;display:grid;grid-template-columns:minmax(180px,1fr) auto minmax(300px,1fr);align-items:center;gap:24px;min-height:76px;padding:0 clamp(22px,4vw,64px);border-bottom:1px solid rgba(129,140,248,.16);background:rgba(7,18,40,.84);box-shadow:0 14px 40px rgba(2,6,23,.3);backdrop-filter:blur(22px) }
.brand { display:flex;align-items:center;color:#fff;text-decoration:none }.brand-text { display:inline-flex;min-width:154px;height:48px;align-items:center;color:#f8fbff;font-size:28px;font-weight:900;letter-spacing:.08em;text-shadow:0 10px 24px rgba(37,99,235,.38),0 0 18px rgba(56,189,248,.25) }
.main-nav { display:flex;justify-content:center;gap:4px }.main-nav a { position:relative;padding:27px 14px 25px;color:#9eacc5;font-size:14px;text-decoration:none;white-space:nowrap;transition:.2s }.main-nav a::after { position:absolute;right:14px;bottom:0;left:14px;height:2px;border-radius:2px;background:linear-gradient(90deg,#3b82f6,#a855f7);content:"";opacity:0;transform:scaleX(.3);transition:.2s }.main-nav a:hover,.main-nav a.active { color:#fff }.main-nav a.active::after { opacity:1;transform:scaleX(1) }
.header-actions { display:flex;align-items:center;justify-content:flex-end;gap:10px }.search { display:flex;width:clamp(170px,16vw,250px);height:40px;align-items:center;gap:8px;padding:0 12px;border:1px solid rgba(129,140,248,.2);border-radius:12px;background:rgba(13,29,59,.72);transition:.2s }.search:focus-within { border-color:rgba(139,92,246,.7);box-shadow:0 0 0 3px rgba(139,92,246,.1) }.search svg { width:16px;fill:none;stroke:#7183a5;stroke-width:1.8 }.search input { min-width:0;width:100%;border:0;outline:0;background:none;color:#e5e7eb;font:inherit;font-size:12px }.search input::placeholder { color:#607191 }
.ai-button,.avatar { border:0;color:#fff;cursor:pointer }.ai-button { height:40px;padding:0 14px;border:1px solid rgba(167,139,250,.32);border-radius:12px;background:linear-gradient(135deg,rgba(37,99,235,.88),rgba(139,92,246,.9));font-weight:750;white-space:nowrap;box-shadow:0 9px 22px rgba(79,70,229,.23);transition:.2s }.ai-button:hover,.avatar:hover { transform:translateY(-2px) }.ai-button span { margin-right:4px;color:#ddd6fe }.avatar { display:grid;width:39px;height:39px;place-items:center;border-radius:50%;background:linear-gradient(135deg,#2563eb,#8b5cf6);font-weight:850;transition:.2s }
@media(max-width:1100px){.global-header{grid-template-columns:auto 1fr;gap:12px;padding-top:10px}.main-nav{grid-column:1/-1;grid-row:2;justify-content:flex-start;overflow:auto}.main-nav a{padding:12px 14px}.header-actions{min-width:0}.main-nav a::after{bottom:0}}
@media(max-width:680px){.brand-text{min-width:112px;height:38px;font-size:24px}.search{display:none}.global-header{padding-inline:16px}.ai-button{font-size:0}.ai-button span{margin:0;font-size:15px}}
</style>
