import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue'
import MainLayout from '../layouts/MainLayout.vue'
import HomeView from '../views/HomeView.vue'
import HotEvents from '../views/HotEvents.vue'
import EventDetail from '../views/EventDetail.vue'
import EventDetailView from '../views/EventDetailView.vue'
import NewsDetailView from '../views/NewsDetailView.vue'
import CommunityView from '../views/CommunityView.vue'
import ProfileLayout from '../components/profile/ProfileLayout.vue'
import ProfileOverviewView from '../views/profile/ProfileOverviewView.vue'
import UserProfileView from '../views/profile/UserProfileView.vue'
import { useUserStore } from '../stores/user'
import { useLoginPromptStore } from '../stores/loginPrompt'

const router = createRouter({
  history: createWebHistory(),

  routes: [
    {
      path: '/',
      redirect: '/login',
    },

    {
      path: '/login',
      name: 'Login',
      component: Login,
    },

    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: 'home',
          name: 'Home',
          component: HomeView,
          meta: {
            requiresIdentity: true,
          },
        },

        {
          path: 'events',
          name: 'Events',
          component: HotEvents,
          meta: {
            requiresIdentity: true,
          },
        },

        // 事件详情：仅正式登录用户可访问
        {
          path: 'events/:id',
          name: 'EventDetail',
          component: EventDetail,
          meta: {
            requiresAuth: true,
          },
        },

        // 完整事件报告：仅正式登录用户可访问
        {
          path: 'report/:id',
          name: 'Report',
          component: EventDetailView,
          meta: {
            requiresAuth: true,
          },
        },

        // 新闻详情：仅正式登录用户可访问
        {
          path: 'news/:articleId',
          name: 'NewsDetail',
          component: NewsDetailView,
          meta: {
            requiresAuth: true,
          },
        },

        // 社区：游客和正式用户都可以访问
        {
          path: 'community',
          name: 'Community',
          component: CommunityView,
          meta: {
            requiresIdentity: true,
          },
        },

        // 个人中心概览：游客和正式用户都可以访问
        {
          path: 'profile',
          name: 'Profile',
          component: ProfileLayout,
          meta: {
            requiresIdentity: true,
          },
          children: [
            {
              path: '',
              name: 'ProfileOverview',
              component: ProfileOverviewView,
              meta: {
                requiresIdentity: true,
              },
            },

            // 编辑资料：仅正式登录用户可访问
            {
              path: 'info',
              name: 'UserProfile',
              component: UserProfileView,
              meta: {
                requiresAuth: true,
              },
            },
          ],
        },
      ],
    },

    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

router.beforeEach((to) => {
  const userStore = useUserStore()
  const loginPrompt = useLoginPromptStore()

  // 只有正式登录用户访问登录页时才自动回首页。
  // 游客仍然允许打开登录页。
  if (to.name === 'Login' && userStore.isLoggedIn) {
    return '/home'
  }

  // 首页、事件列表、社区、个人中心概览：
  // 必须已经选择正式登录或游客模式。
  if (
    to.meta.requiresIdentity &&
    !userStore.hasIdentity
  ) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  // 事件详情、报告、新闻详情、资料编辑：
  // 只有正式登录用户可以访问。
  if (
    to.meta.requiresAuth &&
    !userStore.isLoggedIn
  ) {
    loginPrompt.openLogin({
      redirect: to.fullPath,
      message: userStore.isGuest
        ? '该功能仅对登录用户开放，请先登录'
        : '请先登录后继续访问',
    })

    return false
  }

  return true
})

export default router
