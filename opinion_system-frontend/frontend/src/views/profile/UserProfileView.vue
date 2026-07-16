<template>
  <section class="profile-panel">
    <article class="profile-card">
      <div class="card-heading">
        <span>Basic Profile</span>
        <h1>基本资料</h1>
      </div>

      <form class="profile-form" @submit.prevent="saveProfile">
        <div class="avatar-row">
          <div class="avatar">{{ profile.avatar }}</div>
          <button class="secondary-button" type="button">更换头像</button>
        </div>

        <label class="form-field">
          <span>用户名</span>
          <div class="input-action">
            <input v-model="draftProfile.username" type="text" :readonly="!isEditingProfile" />
            <button class="secondary-button" type="button" @click="startEditProfile">
              {{ isEditingProfile ? '编辑中' : '编辑资料' }}
            </button>
          </div>
        </label>

        <label class="form-field">
          <span>邮箱</span>
          <div class="input-action">
            <input v-model="draftProfile.email" type="email" :readonly="!isEditingProfile" />
            <button class="secondary-button" type="button" @click="startEditProfile">
              {{ isEditingProfile ? '编辑中' : '编辑资料' }}
            </button>
          </div>
        </label>

        <label class="form-field">
          <span>手机号</span>
          <input v-model="draftProfile.phone" type="tel" />
        </label>

        <label class="form-field">
          <span>注册时间</span>
          <input v-model="draftProfile.registeredAt" type="text" readonly />
        </label>

        <div class="form-actions">
          <p v-if="profileMessage" class="form-message">{{ profileMessage }}</p>
          <button class="save-button" type="submit">保存修改</button>
        </div>
      </form>
    </article>

    <article class="profile-card">
      <div class="card-heading">
        <span>Account Security</span>
        <h2>账号与安全</h2>
      </div>

      <form class="profile-form security-form">
        <label class="form-field">
          <span>登录密码</span>
          <div class="input-action">
            <input v-model="security.password" type="password" readonly />
            <button class="secondary-button" type="button" @click="openPasswordDialog">修改密码</button>
          </div>
        </label>

        <label class="form-field">
          <span>当前登录状态</span>
          <input v-model="security.status" type="text" readonly />
        </label>

        <div class="form-actions">
          <button class="danger-button" type="button" @click="confirmLogout">退出当前账号</button>
        </div>
      </form>
    </article>

    <div v-if="isPasswordDialogOpen" class="modal-backdrop" @click.self="closePasswordDialog">
      <section class="password-modal" role="dialog" aria-modal="true" aria-labelledby="password-dialog-title">
        <div class="card-heading">
          <span>Password</span>
          <h2 id="password-dialog-title">修改密码</h2>
        </div>

        <form class="profile-form" @submit.prevent="savePassword">
          <label class="form-field">
            <span>当前密码</span>
            <input v-model="passwordForm.currentPassword" type="password" autocomplete="current-password" />
          </label>

          <label class="form-field">
            <span>新密码</span>
            <input v-model="passwordForm.newPassword" type="password" autocomplete="new-password" />
          </label>

          <label class="form-field">
            <span>确认新密码</span>
            <input v-model="passwordForm.confirmPassword" type="password" autocomplete="new-password" />
          </label>

          <p v-if="passwordMessage" class="form-message error-message">{{ passwordMessage }}</p>

          <div class="dialog-actions">
            <button class="secondary-button" type="button" @click="closePasswordDialog">取消</button>
            <button class="save-button" type="submit">保存密码</button>
          </div>
        </form>
      </section>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// API 预留：后续可在这里拉取用户资料并替换 mock 数据。
const profile = reactive({
  avatar: userStore.displayAvatar || '林',
  username: userStore.displayName || '林知微',
  email: 'lin.zhiwei@example.com',
  phone: '138 0000 2026',
  registeredAt: '2025-03-18',
})

const draftProfile = reactive({ ...profile })
const isEditingProfile = ref(false)
const isPasswordDialogOpen = ref(false)
const profileMessage = ref('')
const passwordMessage = ref('')

const security = reactive({
  password: '********',
  status: userStore.isLoggedIn ? '已登录' : userStore.isGuest ? '访客模式' : '未登录',
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

function startEditProfile() {
  isEditingProfile.value = true
  profileMessage.value = ''
}

function saveProfile() {
  Object.assign(profile, draftProfile)
  isEditingProfile.value = false
  profileMessage.value = '资料已保存'
  // API 预留：后续提交 profile 至用户资料接口。
}

function openPasswordDialog() {
  isPasswordDialogOpen.value = true
  passwordMessage.value = ''
}

function closePasswordDialog() {
  isPasswordDialogOpen.value = false
  resetPasswordForm()
}

function savePassword() {
  passwordMessage.value = ''

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    passwordMessage.value = '两次新密码不一致，请重新输入'
    return
  }

  security.password = '********'
  closePasswordDialog()
  // API 预留：后续提交 passwordForm 至修改密码接口。
}

function resetPasswordForm() {
  Object.assign(passwordForm, {
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
}

function confirmLogout() {
  if (!window.confirm('确认退出当前账号吗？')) {
    return
  }

  userStore.logout()
}
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

.profile-card {
  min-width: 0;
  border: 1px solid rgba(139, 92, 246, 0.24);
  border-radius: var(--profile-card-radius);
  background:
    linear-gradient(145deg, rgba(7, 22, 47, 0.86), rgba(5, 11, 36, 0.72)),
    rgba(7, 22, 47, 0.72);
  box-shadow: 0 20px 58px rgba(5, 11, 36, 0.34);
  backdrop-filter: blur(20px);
}

.profile-card {
  padding: 28px;
}

.card-heading span,
.form-field span {
  color: #c4b5fd;
  font-size: 13px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

h1,
h2,
p {
  margin: 0;
}

h1,
h2 {
  margin-top: 8px;
  color: #fff;
  overflow-wrap: anywhere;
}

h1 {
  font-size: 30px;
}

h2 {
  font-size: 26px;
}

p {
  margin-top: 10px;
  color: #94a3b8;
  line-height: 1.7;
  overflow-wrap: anywhere;
}

.profile-form {
  display: grid;
  gap: 18px;
  margin-top: 24px;
  min-width: 0;
}

.security-form {
  max-width: 760px;
}

.avatar-row {
  display: flex;
  gap: 16px;
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

.form-field {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.input-action {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  min-width: 0;
}

input {
  width: 100%;
  min-height: 44px;
  box-sizing: border-box;
  min-width: 0;
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 18px;
  outline: none;
  background: rgba(7, 22, 47, 0.48);
  color: #e5edff;
  font-size: 15px;
  font-weight: 700;
  padding: 0 14px;
  overflow: hidden;
  text-overflow: ellipsis;
}

input:focus {
  border-color: rgba(139, 92, 246, 0.58);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.14);
}

input[readonly] {
  color: #94a3b8;
}

.form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
  min-width: 0;
}

.form-message {
  margin: 0;
  color: #ddd6fe;
  font-size: 13px;
  font-weight: 800;
  overflow-wrap: anywhere;
}

.error-message {
  color: #fecaca;
}

.secondary-button,
.save-button,
.danger-button {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  border-radius: 18px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 800;
  white-space: normal;
  text-align: center;
  overflow-wrap: anywhere;
  transition: 0.2s ease;
}

.secondary-button {
  padding: 0 14px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(99, 102, 241, 0.14);
  color: #ede9fe;
}

.save-button {
  padding: 0 22px;
  border: 1px solid rgba(168, 85, 247, 0.5);
  background: linear-gradient(135deg, var(--profile-primary), var(--profile-primary-2), var(--profile-primary-3));
  color: #fff;
  box-shadow: 0 14px 30px rgba(99, 102, 241, 0.28);
}

.danger-button {
  padding: 0 18px;
  border: 1px solid rgba(248, 113, 113, 0.42);
  background: rgba(127, 29, 29, 0.12);
  color: #fecaca;
}

.secondary-button:hover,
.save-button:hover,
.danger-button:hover {
  transform: translateY(-1px);
}

.modal-backdrop {
  position: fixed;
  z-index: 40;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(5, 11, 36, 0.7);
  backdrop-filter: blur(10px);
}

.password-modal {
  width: min(520px, 100%);
  box-sizing: border-box;
  padding: 28px;
  border: 1px solid rgba(139, 92, 246, 0.28);
  border-radius: var(--profile-card-radius);
  background:
    linear-gradient(145deg, rgba(7, 22, 47, 0.96), rgba(5, 11, 36, 0.92)),
    rgba(7, 22, 47, 0.94);
  box-shadow: 0 24px 72px rgba(5, 11, 36, 0.52);
  backdrop-filter: blur(20px);
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

@media (max-width: 720px) {
  .input-action {
    grid-template-columns: 1fr;
  }

  .avatar-row,
  .form-actions,
  .dialog-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
