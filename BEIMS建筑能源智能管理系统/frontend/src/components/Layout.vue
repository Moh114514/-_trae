<template>
  <div class="layout-wrapper">
    <template v-if="isDashboard">
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </template>
    
    <template v-else>
      <el-container class="layout-container">
        <el-aside width="220px" class="sidebar">
          <div class="logo">
            <h1>BEIMS</h1>
            <p>建筑能源智能管理系统</p>
          </div>
          
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            router
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <el-menu-item index="/dashboard">
              <el-icon><Odometer /></el-icon>
              <span>综合概览</span>
            </el-menu-item>
            
            <el-sub-menu index="data">
              <template #title>
                <el-icon><DataLine /></el-icon>
                <span>数据管理</span>
              </template>
              <el-menu-item index="/data-import">
                <el-icon><Upload /></el-icon>
                <span>数据导入</span>
              </el-menu-item>
              <el-menu-item index="/query">
                <el-icon><Search /></el-icon>
                <span>数据查询</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="statistics">
              <template #title>
                <el-icon><DataAnalysis /></el-icon>
                <span>统计分析</span>
              </template>
              <el-menu-item index="/statistics/trend">
                <el-icon><TrendCharts /></el-icon>
                <span>能耗趋势</span>
              </el-menu-item>
              <el-menu-item index="/statistics/peak-demand">
                <el-icon><Top /></el-icon>
                <span>峰值需求分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/intensity">
                <el-icon><Histogram /></el-icon>
                <span>能耗强度分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/comparison">
                <el-icon><Operation /></el-icon>
                <span>对比分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/weather-correlation">
                <el-icon><Sunny /></el-icon>
                <span>天气相关性分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/occupancy-impact">
                <el-icon><User /></el-icon>
                <span>人员影响分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/hourly-pattern">
                <el-icon><Timer /></el-icon>
                <span>小时模式分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/weekly-pattern">
                <el-icon><Calendar /></el-icon>
                <span>周模式分析</span>
              </el-menu-item>
              <el-menu-item index="/statistics/seasonal-pattern">
                <span style="margin-right: 8px;">🍃</span>
                <span>季节性分析</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="intelligence">
              <template #title>
                <el-icon><ChatDotRound /></el-icon>
                <span>智慧运维</span>
              </template>
              <el-menu-item index="/intelligence">
                <el-icon><ChatLineRound /></el-icon>
                <span>智能问答</span>
              </el-menu-item>
              <el-menu-item index="/knowledge">
                <el-icon><Collection /></el-icon>
                <span>知识库管理</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-menu-item index="/report">
              <el-icon><Document /></el-icon>
              <span>报表导出</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <el-container>
          <el-header class="header">
            <div class="header-left">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
                <el-breadcrumb-item>{{ currentRoute?.meta?.title }}</el-breadcrumb-item>
              </el-breadcrumb>
            </div>
            
            <div class="header-right">
              <el-button type="primary" size="small" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新数据
              </el-button>
              
              <el-dropdown trigger="click" class="user-dropdown">
                <el-button type="default" size="small" class="user-btn">
                  <el-icon><User /></el-icon>
                  <span>{{ user?.full_name || '用户' }}</span>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="viewProfile">
                      <el-icon><Avatar /></el-icon>
                      个人信息
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="logout">
                      <el-icon><SwitchButton /></el-icon>
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </el-header>
          
          <el-main class="main-content">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </el-main>
        </el-container>
      </el-container>
    </template>
    
    <!-- 个人信息对话框 -->
    <el-dialog
      v-model="profileDialog"
      title="个人信息"
      width="400px"
    >
      <div class="profile-content">
        <div class="profile-item">
          <span class="profile-label">用户名:</span>
          <span class="profile-value">{{ user?.username }}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">姓名:</span>
          <span class="profile-value">{{ user?.full_name }}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">邮箱:</span>
          <span class="profile-value">{{ user?.email }}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">角色:</span>
          <span class="profile-value">{{ user?.role }}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">账号状态:</span>
          <span class="profile-value">{{ user?.is_active ? '活跃' : '禁用' }}</span>
        </div>
        <div class="profile-item">
          <span class="profile-label">创建时间:</span>
          <span class="profile-value">{{ user?.created_at ? new Date(user.created_at).toLocaleString() : '' }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/store'
import { dataAPI } from '@/api'
import { authAPI, getUser, removeToken } from '@/api/auth'
import { ElMessage, ElDialog } from 'element-plus'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)
const user = ref(getUser())
const profileDialog = ref(false)

const isDashboard = computed(() => {
  return route.path === '/dashboard'
})

const refreshData = async () => {
  try {
    const [buildingsRes, metersRes, summaryRes] = await Promise.all([
      dataAPI.getBuildings(),
      dataAPI.getMeters(),
      dataAPI.getSummary()
    ])
    
    appStore.setBuildings(buildingsRes.data.buildings)
    appStore.setMeters(metersRes.data.meters)
    appStore.setDataSummary(summaryRes.data)
    
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
  }
}

const viewProfile = () => {
  profileDialog.value = true
}

const logout = () => {
  removeToken()
  ElMessage.success('退出登录成功')
  router.push('/login')
}

const loadUserInfo = async () => {
  try {
    const response = await authAPI.getCurrentUser()
    user.value = response.data
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.layout-wrapper {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow-y: auto;
}

.logo {
  height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
  border-bottom: 1px solid #3a4a5b;
}

.logo h1 {
  font-size: 24px;
  margin: 0;
  font-weight: bold;
}

.logo p {
  font-size: 12px;
  margin: 5px 0 0;
  opacity: 0.8;
}

.sidebar-menu {
  border-right: none;
}

.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-dropdown {
  margin-left: 10px;
}

.user-btn {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
  transition: all 0.3s;
}

.user-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
}

.profile-content {
  padding: 10px 0;
}

.profile-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.profile-label {
  font-weight: bold;
  color: #606266;
}

.profile-value {
  color: #303133;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
