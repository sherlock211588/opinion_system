import { request4 as request } from './request'

export function getHealth() {
  return request.get('/health')
}

export function getDashboard() {
  return request.get('/dashboard')
}
