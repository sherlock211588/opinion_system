<template>
  <section class="profile-page">
    <div class="profile-card">
      <div class="avatar">{{ userStore.displayAvatar }}</div>
      <div>
        <span>Personal Center</span>
        <h1>个人中心</h1>
        <p>{{ userStore.displayName }}，已开启 AI 总结、热点追踪和分析报告能力。</p>
      </div>
    </div>

    <div class="profile-grid">
      <article>
        <span>关注话题</span>
        <strong>新能源、AI科技、城市文旅</strong>
      </article>
      <article>
        <span>收藏报告</span>
        <strong>12 篇</strong>
      </article>
      <article>
        <span>本周 AI 提问</span>
        <strong>38 次</strong>
      </article>
    </div>

    <section class="settings-card">
      <h2>偏好设置</h2>
      <label>
        <span>热点风险提醒</span>
        <input type="checkbox" checked />
      </label>
      <label>
        <span>每日舆情摘要</span>
        <input type="checkbox" checked />
      </label>
      <label>
        <span>AI 自动生成报告</span>
        <input type="checkbox" />
      </label>
    </section>
  </section>
</template>

<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<style scoped>
.profile-page {
  display: grid;
  gap: 24px;
}

.profile-card,
.profile-grid article,
.settings-card {
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 70px rgba(93, 73, 220, 0.11);
  backdrop-filter: blur(20px);
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 32px;
  border-radius: 32px;
}

.avatar {
  display: grid;
  width: 76px;
  height: 76px;
  place-items: center;
  border-radius: 24px;
  background: linear-gradient(135deg, #805cff, #55d6ff);
  color: #fff;
  font-size: 22px;
  font-weight: 900;
}

span {
  color: #805cff;
  font-weight: 900;
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  margin-top: 8px;
  font-size: 42px;
}

p {
  margin-top: 10px;
  color: #94a3b8;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.profile-grid article,
.settings-card {
  padding: 24px;
  border-radius: 28px;
}

.profile-grid strong {
  display: block;
  margin-top: 12px;
  color: #ffffff;
  font-size: 24px;
}

.settings-card {
  display: grid;
  gap: 16px;
}

.settings-card h2 {
  margin-bottom: 8px;
}

label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-radius: 18px;
  background: rgba(128, 92, 255, 0.08);
}

input {
  width: 20px;
  height: 20px;
  accent-color: #805cff;
}

@media (max-width: 760px) {
  .profile-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }
}

/* dark blue technology news theme */
.profile-card,
.profile-grid article,
.settings-card {
  border-color: rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(145deg, rgba(15, 30, 58, 0.84), rgba(8, 20, 38, 0.72)),
    rgba(15, 30, 58, 0.75);
  box-shadow: 0 24px 70px rgba(0, 217, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.avatar {
  background: linear-gradient(135deg, #2563eb, #8b5cf6);
}

span {
  color: #00d9ff;
}

h1,
h2,
.profile-grid strong {
  color: #ffffff;
}

p {
  color: #94a3b8;
}

label {
  background: rgba(37, 99, 235, 0.16);
  border: 1px solid rgba(56, 189, 248, 0.16);
}

input {
  accent-color: #2563eb;
}
</style>
