<template>
  <section class="profile-layout">
    <main class="profile-content">
      <RouterView />
    </main>
  </section>
</template>

<style scoped>
.profile-layout {
  --profile-bg-deep: #050b24;
  --profile-bg-panel: #07162f;
  --profile-primary: #6366f1;
  --profile-primary-2: #8b5cf6;
  --profile-primary-3: #a855f7;
  --profile-card-radius: 20px;
  --profile-gap: 24px;

  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--profile-gap);
  align-items: start;
  min-height: calc(100vh - 96px);
  overflow: visible;
  padding-bottom: var(--profile-gap);
  background:
    radial-gradient(circle at 18% 6%, rgba(99, 102, 241, 0.18), transparent 30%),
    linear-gradient(180deg, var(--profile-bg-deep), var(--profile-bg-panel));
}

.profile-content {
  min-width: 0;
  overflow: visible;
}
</style>
