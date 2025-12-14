import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '数据概览', icon: 'DataAnalysis' }
        },
        {
          path: 'ranking',
          name: 'Ranking',
          component: () => import('@/views/ScenicRanking.vue'),
          meta: { title: '景区排行榜', icon: 'TrophyBase' }
        },
        {
          path: 'visitor-source',
          name: 'VisitorSource',
          component: () => import('@/views/VisitorSource.vue'),
          meta: { title: '客源地分析', icon: 'Location' }
        },
        {
          path: 'season-analysis',
          name: 'SeasonAnalysis',
          component: () => import('@/views/SeasonalAnalysis.vue'),
          meta: { title: '人流量分析', icon: 'Sunny' }
        },
        {
          path: 'data-crawler',
          name: 'DataCrawler',
          component: () => import('@/views/DataCrawler.vue'),
          meta: { title: '数据爬取管理', icon: 'Connection' }
        },
        {
          path: 'scenic-manage',
          name: 'ScenicManage',
          component: () => import('@/views/ScenicManage.vue'),
          meta: { title: '景点数据管理', icon: 'Files' }
        },
        {
          path: 'health',
          name: 'Health',
          component: () => import('@/views/Health.vue'),
          meta: { title: '系统健康监控', icon: 'Monitor' }
        },
        {
          path: 'cache-manage',
          name: 'CacheManage',
          component: () => import('@/views/CacheManage.vue'),
          meta: { title: '缓存管理', icon: 'Coin' }
        },
        {
          path: 'profile',
          name: 'UserProfile',
          component: () => import('@/views/UserProfile.vue'),
          meta: { title: '账号信息', icon: 'User', hidden: true }
        }
      ]
    }
  ]
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token

  if (to.path === '/login') {
    if (token) {
      next('/')
    } else {
      next()
    }
  } else {
    if (token) {
      next()
    } else {
      next('/login')
    }
  }
})

export default router
