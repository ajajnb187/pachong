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
          meta: { title: '季节性分析', icon: 'Sunny' }
        },
        {
          path: 'scenic-detail/:id',
          name: 'ScenicDetail',
          component: () => import('@/views/ScenicDetail.vue'),
          meta: { title: '景区详情', icon: 'Location', hidden: true }
        },
        {
          path: 'data-crawler',
          name: 'DataCrawler',
          component: () => import('@/views/DataCrawler.vue'),
          meta: { title: '数据爬取管理', icon: 'Connection' }
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
