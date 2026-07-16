<template>
  <section class="profile-panel">
    <article class="overview-card user-card">
      <div class="user-main">
        <div class="avatar" aria-hidden="true">{{ user.avatar }}</div>
        <div>
          <span class="eyebrow">User Overview</span>
          <h1>{{ user.name }}</h1>
          <p>{{ user.email }}</p>
          <p class="muted">注册时间：{{ user.registeredAt }}</p>
        </div>
      </div>

      <div class="user-stats">
        <div v-for="stat in stats" :key="stat.label" class="stat-item">
          <span>{{ stat.label }}</span>
          <strong>{{ stat.value }}</strong>
        </div>
      </div>

      <button class="action-button primary" type="button" @click="handleEditProfile">
        {{ userStore.isGuest ? '登录后编辑' : '编辑资料' }}
      </button>
    </article>

    <article class="overview-card recent-card">
      <div class="section-heading">
        <div>
          <span class="eyebrow">Recent Views</span>
          <h2>最近浏览</h2>
        </div>
        <button class="ghost-button clear-button" type="button" @click="handleClearRecentViews">
          清空记录
        </button>
      </div>

      <div v-if="recentRecords.length" class="recent-list">
        <div v-for="record in recentRecords" :key="record.path" class="recent-item">
          <div class="record-meta">
            <span class="type-tag">{{ record.type }}</span>
            <span>{{ record.meta }}</span>
          </div>
          <h3>{{ record.title }}</h3>
          <div class="record-footer">
            <time>{{ record.viewedAt }}</time>
            <RouterLink class="ghost-button" :to="record.path">再次查看</RouterLink>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">暂无浏览记录</div>
    </article>

    <div class="summary-grid">
      <article class="overview-card">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Following</span>
            <h2>关注领域 / 关注关键词</h2>
          </div>
        </div>

        <div class="tag-group">
          <span v-for="field in followedFields" :key="field" class="soft-tag">{{ field }}</span>
        </div>
        <div class="tag-group keyword-tags">
          <span v-for="keyword in followedKeywords" :key="keyword" class="soft-tag keyword">{{ keyword }}</span>
        </div>
      </article>

      <article class="overview-card">
        <div class="section-heading">
          <div>
            <span class="eyebrow">Data Sources</span>
            <h2>监测数据源（共 {{ sourceNames.length }} 个）</h2>
          </div>
        </div>

        <div v-if="sourceNames.length" class="source-list">
          <template v-for="name in sourceNames" :key="name">
            <a
              v-if="sourceUrls[name]"
              :href="sourceUrls[name]"
              target="_blank"
              rel="noopener noreferrer"
              class="source-chip linked"
              :title="sourceUrls[name]"
            >{{ name }}</a>
            <span v-else class="source-chip" :title="name">{{ name }}</span>
          </template>
        </div>
        <div v-else class="empty-state">暂无数据源信息</div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useLoginPromptStore } from '@/stores/loginPrompt'
import { useUserStore } from '@/stores/user'
import { clearRecentViews, getRecentViews } from '../../utils/recentViews'
import { getDashboard } from '@/api/system'

const router = useRouter()
const userStore = useUserStore()
const loginPrompt = useLoginPromptStore()

// 看板数据
const dashboard = ref({
  kpi: {},
  categories: [],
  top_keywords: [],
  source_count: { total: 0, active: 0, inactive: 0 },
  source_names: [],
  source_urls: {},
})

onMounted(async () => {
  try {
    const data = await getDashboard()
    if (data) {
      dashboard.value = {
        kpi: data.kpi || {},
        categories: data.categories || [],
        top_keywords: data.top_keywords || [],
        source_count: data.source_count || { total: 0, active: 0, inactive: 0 },
        source_names: data.source_names || [],
        source_urls: data.source_urls || {},
      }
    }
  } catch {
    // keep defaults
  }
})

const user = computed(() => {
  if (userStore.isGuest) {
    return {
      avatar: userStore.displayAvatar || '访',
      name: userStore.displayName || '游客用户',
      email: '登录后可完善邮箱',
      registeredAt: '游客模式',
    }
  }
  const u = userStore.currentUser || {}
  return {
    avatar: userStore.displayAvatar || '林',
    name: userStore.displayName || u.username || '',
    email: u.email || '',
    registeredAt: u.created_at ? u.created_at.slice(0, 10) : '',
  }
})

const stats = computed(() => {
  const k = dashboard.value.kpi || {}
  const kws = dashboard.value.top_keywords || []
  const cats = dashboard.value.categories || []
  if (userStore.isGuest) {
    return [
      { label: '事件总数', value: k.total_events || 0 },
      { label: '数据来源', value: k.platform_count || 0 },
      { label: '热度指数', value: k.avg_heat || 0 },
    ]
  }
  return [
    { label: '关注领域', value: cats.length },
    { label: '关注关键词', value: kws.length },
    { label: '监测数据源', value: k.platform_count || 0 },
  ]
})

const recentRecords = ref(getRecentViews().slice(0, 5))

function handleClearRecentViews() {
  if (promptLoginForGuest('清空浏览记录需要登录账号')) return
  clearRecentViews()
  recentRecords.value = []
}

function handleEditProfile() {
  if (promptLoginForGuest('编辑个人资料需要登录账号')) return
  router.push('/profile/info')
}

function promptLoginForGuest(message) {
  if (userStore.isLoggedIn) return false
  loginPrompt.openLogin({ redirect: '/profile', message })
  return true
}

const followedFields = computed(() => {
  const cats = dashboard.value.categories || []
  if (userStore.isGuest) return ['登录后可同步关注领域']
  return cats.length ? cats : ['暂无数据']
})

const followedKeywords = computed(() => {
  const kws = dashboard.value.top_keywords || []
  if (userStore.isGuest) return ['登录后可同步关注关键词']
  return kws.length ? kws : ['暂无数据']
})

const sourceNames = computed(() => {
  if (userStore.isGuest) return []
  return dashboard.value.source_names || []
})
const sourceUrls = computed(() => {
  return dashboard.value.source_urls || {}
})
</script>

<style scoped>
.profile-panel {
  --profile-bg-deep: #050b24;
  --profile-bg-panel: #07162f;
  --profile-primary: #6366f1;
  --profile-primary-2: #8b5cf6;
  --profile-primary-3: #a855f7;
  --profile-card-radius: 20px;
  --profile-inner-radius: 18px;
  --profile-gap: 24px;

  display: grid;
  gap: var(--profile-gap);
  min-width: 0;
  overflow: visible;
}

.overview-card {
  min-width: 0;
  border: 1px solid rgba(139, 92, 246, 0.24);
  border-radius: var(--profile-card-radius);
  background:
    linear-gradient(145deg, rgba(7, 22, 47, 0.86), rgba(5, 11, 36, 0.72)),
    rgba(7, 22, 47, 0.72);
  box-shadow: 0 20px 58px rgba(5, 11, 36, 0.34);
  backdrop-filter: blur(20px);
}

.user-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 0.7fr) auto;
  gap: var(--profile-gap);
  align-items: center;
  padding: 28px;
}

.user-main {
  display: flex;
  gap: 18px;
  align-items: center;
  min-width: 0;
}

.avatar {
  display: grid;
  width: 76px;
  height: 76px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid rgba(139, 92, 246, 0.44);
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 26%, rgba(255, 255, 255, 0.38), transparent 28%),
    linear-gradient(135deg, var(--profile-primary), var(--profile-primary-2) 56%, var(--profile-primary-3));
  color: #fff;
  font-size: 30px;
  font-weight: 900;
  box-shadow: 0 18px 38px rgba(99, 102, 241, 0.34);
}

.eyebrow {
  color: #c4b5fd;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin: 0;
}

h1 {
  margin-top: 8px;
  color: #fff;
  font-size: 30px;
  overflow-wrap: anywhere;
}

h2 {
  margin-top: 8px;
  color: #fff;
  font-size: 22px;
  overflow-wrap: anywhere;
}

h3 {
  margin-top: 10px;
  color: #f8fafc;
  font-size: 16px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

p {
  margin-top: 8px;
  color: #94a3b8;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.muted {
  color: #64748b;
}

.user-stats,
.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
  max-height: 260px;
  overflow-y: auto;
}

.source-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 4px 10px;
  border: 1px solid rgba(56, 189, 248, 0.24);
  border-radius: 14px;
  background: rgba(56, 189, 248, 0.08);
  color: #7dd3fc;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
  text-decoration: none;
  transition: background 0.2s, border-color 0.2s;
}
.source-chip.linked {
  cursor: pointer;
}
.source-chip.linked:hover {
  background: rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.5);
}

.stat-item {
  padding: 16px;
  border: 1px solid rgba(139, 92, 246, 0.18);
  border-radius: var(--profile-inner-radius);
  background: rgba(7, 22, 47, 0.46);
  min-width: 0;
}

.stat-item span {
  display: block;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 700;
}

.stat-item strong {
  display: block;
  margin-top: 8px;
  color: #fff;
  font-size: 28px;
  overflow-wrap: anywhere;
}

.action-button,
.ghost-button {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 18px;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
  transition: 0.2s ease;
}

.action-button {
  padding: 0 16px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(99, 102, 241, 0.14);
  color: #ede9fe;
}

.action-button.primary {
  border-color: rgba(168, 85, 247, 0.5);
  background: linear-gradient(135deg, var(--profile-primary), var(--profile-primary-2), var(--profile-primary-3));
  color: #fff;
  box-shadow: 0 14px 30px rgba(99, 102, 241, 0.28);
}

.action-button:hover,
.ghost-button:hover {
  transform: translateY(-1px);
}

.recent-card {
  padding: 28px;
}

.section-heading {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
}

.recent-list {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.recent-item {
  display: grid;
  gap: 10px;
  padding: 18px;
  min-width: 0;
  border: 1px solid rgba(139, 92, 246, 0.18);
  border-radius: var(--profile-inner-radius);
  background: rgba(7, 22, 47, 0.44);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.recent-item:hover {
  transform: translateY(-3px);
  border-color: rgba(168, 85, 247, 0.46);
  background: rgba(7, 22, 47, 0.62);
  box-shadow: 0 14px 36px rgba(99, 102, 241, 0.2), 0 0 24px rgba(168, 85, 247, 0.12);
}

.record-meta,
.record-footer {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
}

.record-meta {
  justify-content: flex-start;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.type-tag,
.soft-tag {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(99, 102, 241, 0.12);
  color: #ddd6fe;
  font-weight: 800;
}

.type-tag {
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
}

.record-footer time {
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.ghost-button {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(168, 85, 247, 0.3);
  background: rgba(139, 92, 246, 0.12);
  color: #ddd6fe;
}

.clear-button {
  cursor: pointer;
}

.empty-state {
  display: grid;
  min-height: 142px;
  margin-top: 18px;
  place-items: center;
  border: 1px dashed rgba(139, 92, 246, 0.28);
  border-radius: var(--profile-inner-radius);
  background: rgba(7, 22, 47, 0.34);
  color: #94a3b8;
  font-size: 14px;
  font-weight: 700;
}

.summary-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: var(--profile-gap);
}

.summary-grid .overview-card {
  padding: 24px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.keyword-tags {
  margin-top: 12px;
}

.soft-tag {
  min-height: 34px;
  padding: 0 12px;
  border-radius: 18px;
  font-size: 13px;
  overflow-wrap: anywhere;
}

.soft-tag.keyword {
  border-color: rgba(168, 85, 247, 0.34);
  background: rgba(168, 85, 247, 0.12);
  color: #f3e8ff;
}

@media (max-width: 1080px) {
  .user-card,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .user-card {
    align-items: stretch;
  }
}

@media (max-width: 760px) {
  .user-stats,
  .source-stats {
    grid-template-columns: 1fr;
  }

  .section-heading,
  .record-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .user-main {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
