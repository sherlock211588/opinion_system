import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  changePassword,
  getCurrentUser,
  loginUser,
  registerUser,
  updateUserProfile,
} from '@/api/auth'

const TOKEN_KEY = 'opinion_access_token'
const USER_KEY = 'opinion_current_user'

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

function unwrap(payload) {
  if (
    payload?.data &&
    typeof payload.data === 'object' &&
    !Array.isArray(payload.data)
  ) {
    return payload.data
  }

  return payload
}

function pickToken(payload) {
  const data = unwrap(payload)

  return (
    data?.access_token ??
    data?.token ??
    data?.accessToken ??
    data?.jwt ??
    ''
  )
}

function pickUser(payload) {
  const data = unwrap(payload)

  return (
    data?.user ??
    data?.current_user ??
    data?.me ??
    data?.profile ??
    null
  )
}

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail
  const message = error?.response?.data?.message

  if (typeof detail === 'string' && detail.trim()) return detail
  if (typeof message === 'string' && message.trim()) return message
  if (typeof error?.message === 'string' && error.message.trim()) return error.message

  return fallback
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem(TOKEN_KEY) || '')
  const currentUser = ref(readStoredUser())
  const loading = ref(false)
  const initialized = ref(false)
  const sessionVerified = ref(false)
  const error = ref('')

  const isLoggedIn = computed(
    () => Boolean(accessToken.value && currentUser.value),
  )

  const displayName = computed(
    () =>
      currentUser.value?.nickname ||
      currentUser.value?.username ||
      '用户',
  )

  const avatarUrl = computed(() => currentUser.value?.avatar || '')

  function saveToken(token) {
    accessToken.value = token || ''

    if (accessToken.value) {
      localStorage.setItem(TOKEN_KEY, accessToken.value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  function saveUser(user) {
    currentUser.value = user || null

    if (currentUser.value) {
      localStorage.setItem(USER_KEY, JSON.stringify(currentUser.value))
    } else {
      localStorage.removeItem(USER_KEY)
    }
  }

  function clearSession() {
    saveToken('')
    saveUser(null)
    sessionVerified.value = false
  }

  async function fetchCurrentUser() {
    const response = await getCurrentUser()
    const user = pickUser(response) ?? unwrap(response)

    if (!user || typeof user !== 'object' || Array.isArray(user)) {
      throw new Error('获取用户资料失败')
    }

    saveUser(user)
    return user
  }

  async function login(payload) {
    loading.value = true
    error.value = ''

    try {
      const response = await loginUser(payload)
      const token = pickToken(response)

      if (!token) {
        throw new Error('登录成功但后端未返回 Token')
      }

      saveToken(token)

      let user = pickUser(response)

      if (!user) {
        user = await fetchCurrentUser()
      } else {
        saveUser(user)
      }

      sessionVerified.value = true

      return {
        token,
        user,
        raw: response,
      }
    } catch (err) {
      clearSession()
      error.value = getErrorMessage(err, '登录失败，请稍后重试')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    error.value = ''

    try {
      const response = await registerUser(payload)
      const token = pickToken(response)
      let user = pickUser(response)

      if (token) {
        saveToken(token)

        if (!user) {
          user = await fetchCurrentUser()
        } else {
          saveUser(user)
        }

        sessionVerified.value = true
      }

      return {
        token,
        user,
        autoLoggedIn: Boolean(token && user),
        raw: response,
      }
    } catch (err) {
      error.value = getErrorMessage(err, '注册失败，请稍后重试')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(payload) {
    loading.value = true
    error.value = ''

    const previousUser = currentUser.value

    try {
      const response = await updateUserProfile(payload)
      const user = pickUser(response) ?? unwrap(response)

      if (!user || typeof user !== 'object' || Array.isArray(user)) {
        throw new Error('资料保存成功但后端未返回用户资料')
      }

      saveUser(user)
      return user
    } catch (err) {
      saveUser(previousUser)
      error.value = getErrorMessage(err, '资料保存失败，请稍后重试')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updatePassword(payload) {
    loading.value = true
    error.value = ''

    try {
      return await changePassword(payload)
    } catch (err) {
      error.value = getErrorMessage(err, '密码修改失败，请稍后重试')
      throw err
    } finally {
      loading.value = false
    }
  }

  async function restoreSession() {
    if (initialized.value) return

    loading.value = true
    error.value = ''

    const token = localStorage.getItem(TOKEN_KEY) || ''
    const cachedUser = readStoredUser()

    if (!token) {
      clearSession()
      initialized.value = true
      sessionVerified.value = true
      loading.value = false
      return
    }

    saveToken(token)

    if (cachedUser) {
      currentUser.value = cachedUser
    }

    try {
      await fetchCurrentUser()
      sessionVerified.value = true
    } catch (err) {
      if (err?.response?.status === 401) {
        clearSession()
      } else {
        sessionVerified.value = false
        error.value = getErrorMessage(err, '暂时无法验证登录状态')
      }
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  function logout() {
    error.value = ''
    clearSession()
  }

  if (typeof window !== 'undefined') {
    window.addEventListener('opinion-auth-expired', clearSession)
  }

  return {
    accessToken,
    currentUser,
    user: currentUser,
    me: currentUser,
    loading,
    initialized,
    sessionVerified,
    error,
    isLoggedIn,
    displayName,
    avatarUrl,
    login,
    register,
    fetchCurrentUser,
    restoreSession,
    updateProfile,
    updatePassword,
    logout,
  }
})
