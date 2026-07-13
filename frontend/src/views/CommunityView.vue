<template>
  <section class="community-page">
    <div class="page-title">
      <span>Community</span>
      <h1>社区观点交流</h1>
      <p>围绕热点事件、分析方法和 AI 总结体验展开讨论，让舆情洞察更接近普通用户。</p>
    </div>

    <div class="post-grid">
      <article v-for="post in communityPosts" :key="post.title" class="post-card">
        <div class="author">{{ post.author.slice(0, 1) }}</div>
        <h2>{{ post.title }}</h2>
        <p>{{ post.content }}</p>
        <div class="post-meta">
          <span>{{ post.likes }} 赞同</span>
          <span>{{ post.replies }} 回复</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { communityPosts } from '@/data/mockOpinion'
</script>

<style scoped>
.community-page {
  display: grid;
  gap: 24px;
}

.page-title,
.post-card {
  border: 1px solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 24px 70px rgba(93, 73, 220, 0.11);
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

h1,
h2,
p {
  margin: 0;
}

h1 {
  margin-top: 8px;
  font-size: clamp(32px, 4vw, 48px);
}

.page-title p {
  max-width: 720px;
  margin-top: 12px;
  color: #94a3b8;
  line-height: 1.8;
}

.post-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.post-card {
  padding: 24px;
  border-radius: 28px;
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease;
}

.post-card:hover {
  box-shadow: 0 30px 76px rgba(93, 73, 220, 0.15);
  transform: translateY(-4px);
}

.author {
  display: grid;
  width: 46px;
  height: 46px;
  place-items: center;
  margin-bottom: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #805cff, #55d6ff);
  color: #fff;
  font-weight: 900;
}

.post-card h2 {
  font-size: 20px;
}

.post-card p {
  margin-top: 12px;
  color: #94a3b8;
  line-height: 1.75;
}

.post-meta {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  color: #805cff;
  font-size: 13px;
  font-weight: 850;
}

@media (max-width: 980px) {
  .post-grid {
    grid-template-columns: 1fr;
  }
}

/* dark blue technology news theme */
.page-title,
.post-card {
  border-color: rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(145deg, rgba(15, 30, 58, 0.84), rgba(8, 20, 38, 0.72)),
    rgba(15, 30, 58, 0.75);
  box-shadow: 0 24px 70px rgba(0, 217, 255, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.page-title span,
.post-meta {
  color: #00d9ff;
}

h1,
.post-card h2 {
  color: #ffffff;
}

.page-title p,
.post-card p {
  color: #94a3b8;
}

.post-card:hover {
  box-shadow: 0 30px 76px rgba(37, 99, 235, 0.2);
}

.author {
  background: linear-gradient(135deg, #2563eb, #8b5cf6);
}
</style>
