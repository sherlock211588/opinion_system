import request from './request'

export function loginUser(data) {
  return request.post('/auth/login', data)
}

export function registerUser(data) {
  return request.post('/auth/register', data)
}

export function getCurrentUser() {
  return request.get('/auth/me')
}

export function updateUserProfile(data) {
  return request.put('/auth/profile', data)
}

export function changePassword(data) {
  return request.put('/auth/password', data)
}

/* 兼容旧导入名称 */
export const login = loginUser
export const register = registerUser
export const getMe = getCurrentUser
export const updateProfile = updateUserProfile
export const updatePassword = changePassword