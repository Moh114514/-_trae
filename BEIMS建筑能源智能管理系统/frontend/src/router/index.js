import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import { isAuthenticated } from '@/api/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '综合概览', icon: 'Odometer' }
      },
      {
        path: 'data-import',
        name: 'DataImport',
        component: () => import('@/views/DataImport.vue'),
        meta: { title: '数据导入', icon: 'Upload' }
      },
      {
        path: 'query',
        name: 'Query',
        component: () => import('@/views/QueryData.vue'),
        meta: { title: '数据查询', icon: 'Search' }
      },
      {
        path: 'statistics',
        redirect: '/statistics/trend',
        meta: { title: '统计分析', icon: 'DataAnalysis' },
        children: [
          {
            path: 'trend',
            name: 'Trend',
            component: () => import('@/views/statistics/Trend.vue'),
            meta: { title: '能耗趋势' }
          },
          {
            path: 'peak-demand',
            name: 'PeakDemand',
            component: () => import('@/views/statistics/PeakDemand.vue'),
            meta: { title: '峰值需求分析' }
          },
          {
            path: 'intensity',
            name: 'Intensity',
            component: () => import('@/views/statistics/Intensity.vue'),
            meta: { title: '能耗强度分析' }
          },
          {
            path: 'comparison',
            name: 'Comparison',
            component: () => import('@/views/statistics/Comparison.vue'),
            meta: { title: '对比分析' }
          },
          {
            path: 'weather-correlation',
            name: 'WeatherCorrelation',
            component: () => import('@/views/statistics/WeatherCorrelation.vue'),
            meta: { title: '天气相关性分析' }
          },
          {
            path: 'occupancy-impact',
            name: 'OccupancyImpact',
            component: () => import('@/views/statistics/OccupancyImpact.vue'),
            meta: { title: '人员影响分析' }
          },
          {
            path: 'hourly-pattern',
            name: 'HourlyPattern',
            component: () => import('@/views/statistics/HourlyPattern.vue'),
            meta: { title: '小时模式分析' }
          },
          {
            path: 'weekly-pattern',
            name: 'WeeklyPattern',
            component: () => import('@/views/statistics/WeeklyPattern.vue'),
            meta: { title: '周模式分析' }
          },
          {
            path: 'seasonal-pattern',
            name: 'SeasonalPattern',
            component: () => import('@/views/statistics/SeasonalPattern.vue'),
            meta: { title: '季节性分析' }
          }
        ]
      },
      {
        path: 'visualization',
        redirect: '/statistics'
      },
      {
        path: 'anomaly',
        redirect: '/statistics'
      },
      {
        path: 'intelligence',
        name: 'Intelligence',
        component: () => import('@/views/Intelligence.vue'),
        meta: { title: '智能问答', icon: 'ChatDotRound' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'),
        meta: { title: '知识库管理', icon: 'Collection' }
      },
      {
        path: 'report',
        name: 'Report',
        component: () => import('@/views/Report.vue'),
        meta: { title: '报表导出', icon: 'Document' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - BEIMS` : 'BEIMS建筑能源智能管理系统'
  
  // 检查是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth !== false)) {
    // 检查用户是否已登录
    if (!isAuthenticated()) {
      // 未登录，重定向到登录页面
      next({ path: '/login' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
