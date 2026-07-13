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
            <h2>监测数据源</h2>
          </div>
        </div>

        <div class="source-stats">
          <div v-for="source in sourceStats" :key="source.label">
            <span>{{ source.label }}</span>
            <strong>{{ source.value }}</strong>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useLoginPromptStore } from '@/stores/loginPrompt'
import { useUserStore } from '@/stores/user'
import { clearRecentViews, getRecentViews } from '../../utils/recentViews'

const router = useRouter()
const userStore = useUserStore()
const loginPrompt = useLoginPromptStore()

const user = computed(() => {
  if (userStore.isGuest) {
    return {
      avatar: userStore.displayAvatar || '访',
      name: userStore.displayName || '游客用户',
      email: '登录后可完善邮箱与联系方式',
      registeredAt: '游客模式',
    }
  }

  return {
    avatar: userStore.displayAvatar || '林',
    name: userStore.displayName || '林知微',
    email: 'lin.zhiwei@example.com',
    registeredAt: '2025-03-18',
  }
})

const stats = computed(() => {
  if (userStore.isGuest) {
    return [
      { label: '关注领域', value: 0 },
      { label: '关注关键词', value: 0 },
      { label: '监测数据源', value: 0 },
    ]
  }

  return [
    { label: '关注领域', value: 5 },
    { label: '关注关键词', value: 12 },
    { label: '监测数据源', value: 8 },
  ]
})

const recentRecords = ref(getRecentViews().slice(0, 5))

function handleClearRecentViews() {
  if (promptLoginForGuest('清空浏览记录需要登录账号')) {
    return
  }

  clearRecentViews()
  recentRecords.value = []
}

function handleEditProfile() {
  if (promptLoginForGuest('编辑个人资料需要登录账号')) {
    return
  }

  router.push('/profile/info')
}

function promptLoginForGuest(message) {
  if (userStore.isLoggedIn) {
    return false
  }

  loginPrompt.openLogin({
    redirect: '/profile',
    message,
  })

  return true
}

const followedFields = computed(() =>
  userStore.isGuest
    ? ['登录后同步关注领域']
    : ['公共安全', '城市治理', '教育就业', '文旅消费', '医疗健康'],
)

const followedKeywords = computed(() =>
  userStore.isGuest
    ? ['登录后同步关注关键词']
    : ['高温保障', '新能源车', '毕业就业', '城市更新', '食品安全', '假期出行'],
)

const sourceStats = computed(() => {
  if (userStore.isGuest) {
    return [
      { label: '已配置数量', value: 0 },
      { label: '已启用数量', value: 0 },
      { label: '已停用数量', value: 0 },
    ]
  }

  return [
    { label: '已配置数量', value: 8 },
    { label: '已启用数量', value: 6 },
    { label: '已停用数量', value: 2 },
  ]
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
.source-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.stat-item,
.source-stats div {
  padding: 16px;
  border: 1px solid rgba(139, 92, 246, 0.18);
  border-radius: var(--profile-inner-radius);
  background: rgba(7, 22, 47, 0.46);
  min-width: 0;
}

.stat-item span,
.source-stats span {
  display: block;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 700;
}

.stat-item strong,
.source-stats strong {
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
