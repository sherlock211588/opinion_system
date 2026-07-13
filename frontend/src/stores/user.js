import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAuthStore } from './auth'

const GUEST_KEY = 'opinion_guest_mode'

function normalizeLoginPayload(firstArg, secondArg) {
  if (typeof firstArg === 'string') {
    return {
      login_type: 'username',
      account: firstArg.trim(),
      password: String(secondArg || ''),
    }
  }

  const payload = firstArg || {}

  if (payload.login_type && payload.account !== undefined) {
    return {
      login_type: payload.login_type,
      account: String(payload.account || '').trim(),
      password: String(payload.password || ''),
    }
  }

  if (payload.phone) {
    return {
      login_type: 'phone',
      account: String(payload.phone).trim(),
      password: String(payload.password || ''),
    }
  }

  if (payload.email) {
    return {
      login_type: 'email',
      account: String(payload.email).trim(),
      password: String(payload.password || ''),
    }
  }

  return {
    login_type: 'username',
    account: String(payload.username || payload.account || '').trim(),
    password: String(payload.password || ''),
  }
}

export const useUserStore = defineStore('user', () => {
  const authStore = useAuthStore()

  const guestMode = ref(
    localStorage.getItem(GUEST_KEY) === 'true',
  )

  const user = computed(() => authStore.currentUser)
  const currentUser = computed(() => authStore.currentUser)

  const isLoggedIn = computed(() => authStore.isLoggedIn)
  const isLogin = computed(() => authStore.isLoggedIn)

  const isGuest = computed(
    () => guestMode.value && !authStore.isLoggedIn,
  )

  const hasIdentity = computed(
    () => authStore.isLoggedIn || isGuest.value,
  )

  const username = computed(() => {
    if (authStore.currentUser?.username) {
      return authStore.currentUser.username
    }

    if (isGuest.value) {
      return '游客用户'
    }

    return ''
  })

  const nickname = computed(() => {
    if (authStore.currentUser?.nickname) {
      return authStore.currentUser.nickname
    }

    if (isGuest.value) {
      return '游客用户'
    }

    return ''
  })

  const avatar = computed(() => {
    if (authStore.avatarUrl) {
      return authStore.avatarUrl
    }

    if (isGuest.value) {
      return '访'
    }

    return ''
  })

  const displayName = computed(() => {
    if (authStore.isLoggedIn) {
      return authStore.displayName
    }

    if (isGuest.value) {
      return '游客用户'
    }

    return '未登录'
  })

  const displayAvatar = computed(() => {
    if (authStore.avatarUrl) {
      return authStore.avatarUrl
    }

    if (isGuest.value) {
      return '访'
    }

    if (authStore.displayName) {
      return authStore.displayName
        .slice(0, 1)
        .toUpperCase()
    }

    return 'YJ'
  })

  const loading = computed(() => authStore.loading)
  const initialized = computed(() => authStore.initialized)

  async function login(firstArg, secondArg) {
    const payload = normalizeLoginPayload(
      firstArg,
      secondArg,
    )

    if (!payload.account) {
      throw new Error('请输入账号')
    }

    if (!payload.password.trim()) {
      throw new Error('请输入密码')
    }

    const result = await authStore.login(payload)

    guestMode.value = false
    localStorage.removeItem(GUEST_KEY)

    return result
  }

  async function register(payload) {
    const result = await authStore.register(payload)

    if (result?.autoLoggedIn) {
      guestMode.value = false
      localStorage.removeItem(GUEST_KEY)
    }

    return result
  }

  function enterGuest() {
    authStore.logout()

    guestMode.value = true
    localStorage.setItem(GUEST_KEY, 'true')

    return true
  }

  function logout() {
    guestMode.value = false
    localStorage.removeItem(GUEST_KEY)

    return authStore.logout()
  }

  function updateUser(payload) {
    if (isGuest.value) {
      throw new Error('游客不能修改资料，请先登录')
    }

    return authStore.updateProfile(payload)
  }

  function updateProfile(payload) {
    if (isGuest.value) {
      throw new Error('游客不能修改资料，请先登录')
    }

    return authStore.updateProfile(payload)
  }

  function restoreUser() {
    return authStore.restoreSession()
  }

  function initUser() {
    return authStore.restoreSession()
  }

  function fetchUser() {
    if (isGuest.value) {
      return null
    }

    return authStore.fetchCurrentUser()
  }

  return {
    user,
    currentUser,
    isLoggedIn,
    isLogin,
    isGuest,
    hasIdentity,
    username,
    nickname,
    avatar,
    displayName,
    displayAvatar,
    loading,
    initialized,
    login,
    register,
    logout,
    updateUser,
    updateProfile,
    restoreUser,
    initUser,
    fetchUser,
    enterGuest,
  }
})