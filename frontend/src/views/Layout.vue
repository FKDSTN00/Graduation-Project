<template>
  <el-container class="layout-container">
    <el-aside
      v-show="!isMobile || sidebarVisible"
      width="220px"
      class="aside-menu"
      :class="{ 'is-mobile': isMobile }"
    >
      <div class="logo">
        <span>协同平台</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="el-menu-vertical"
        :background-color="isDark ? '#1d1e1f' : '#ffffff'"
        :text-color="isDark ? '#bfcbd9' : '#303133'"
        active-text-color="#409EFF"
        @select="onSelect"
      >
        <template v-if="!isAdmin">
          <el-menu-item index="/home">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/documents">
            <el-icon><Document /></el-icon>
            <span>文档管理</span>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <span>任务管理</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><Collection /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/files">
            <el-icon><Files /></el-icon>
            <span>文件中心</span>
          </el-menu-item>
          <el-menu-item index="/schedule">
            <el-icon><Calendar /></el-icon>
            <span>日程与会议</span>
          </el-menu-item>
          <el-menu-item index="/approval">
            <el-icon><Stamp /></el-icon>
            <span>审批流</span>
          </el-menu-item>
          <el-menu-item index="/votes">
            <el-icon><Ticket /></el-icon>
            <span>投票与问卷</span>
          </el-menu-item>
          <el-menu-item index="/feedback">
            <el-icon><ChatDotRound /></el-icon>
            <span>留言与反馈</span>
          </el-menu-item>
        </template>
        <template v-if="isAdmin">
          <el-menu-item index="/admin/kanban">
            <el-icon><DataBoard /></el-icon>
            <span>工作流程看板</span>
          </el-menu-item>
          <el-menu-item index="/admin/monitor">
            <el-icon><Monitor /></el-icon>
            <span>文档监控</span>
          </el-menu-item>
          <el-menu-item index="/admin/knowledge">
            <el-icon><Collection /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/admin/files">
            <el-icon><Files /></el-icon>
            <span>文件中心</span>
          </el-menu-item>
          <el-menu-item index="/admin/schedule">
            <el-icon><Calendar /></el-icon>
            <span>日程与会议</span>
          </el-menu-item>
          <el-menu-item index="/admin/approval">
            <el-icon><Stamp /></el-icon>
            <span>审批流</span>
          </el-menu-item>
          <el-menu-item index="/admin/vote">
            <el-icon><Bell /></el-icon>
            <span>投票与问卷</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/feedback">
            <el-icon><ChatDotRound /></el-icon>
            <span>留言与反馈</span>
          </el-menu-item>
          <el-menu-item index="/admin/backup">
            <el-icon><RefreshLeft /></el-icon>
            <span>系统级备份与恢复</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="main-header">
        <div class="header-left">
          <el-button
            v-if="isMobile"
            text
            circle
            @click="sidebarVisible = !sidebarVisible"
            class="burger"
          >
            <el-icon><Menu /></el-icon>
          </el-button>
          <h3>企业知识协同平台</h3>
        </div>
        <div class="header-right">
          <el-popover
            placement="bottom"
            :width="300"
            trigger="click"
            popper-class="notification-popover"
          >
            <template #reference>
              <el-button circle style="margin-right: 16px">
                <el-icon><Bell /></el-icon>
              </el-button>
            </template>
            <div class="notification-panel">
              <div class="notification-header" style="padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid var(--el-border-color-light); font-weight: bold;">
                通知中心
              </div>
              <div class="notification-body" style="max-height: 300px; overflow-y: auto;">
                <el-empty description="暂无新通知" :image-size="80"></el-empty>
              </div>
            </div>
          </el-popover>
          <el-switch
            v-model="isDark"
            inline-prompt
            :active-icon="Moon"
            :inactive-icon="Sunny"
            @change="toggleDark"
            style="margin-right: 16px"
          />
          <el-dropdown>
            <span class="el-dropdown-link user-chip">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar" icon="UserFilled" />
              <span class="username" :class="{ 'hidden-mobile': isMobile }">{{ displayName }}</span>
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToPersonalCenter">个人中心</el-dropdown-item>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content-area">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store'
import { 
  Document, Calendar, Stamp, Bell, DataBoard, Cpu, 
  Moon, Sunny, UserFilled, ArrowDown, Setting, Menu,
  Monitor, Collection, Files, User, ChatDotRound, RefreshLeft,
  House, List, Ticket
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const isDark = ref(false)
const isLoggingOut = ref(false)
const isMobile = ref(false)
const sidebarVisible = ref(false)

const displayName = computed(() => {
  if (isLoggingOut.value) return '正在退出...'
  return userStore.userInfo?.username || '用户'
})

const isAdmin = computed(() => userStore.userInfo?.role === 'admin')

const onSelect = () => {
  if (isMobile.value) sidebarVisible.value = false
}

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) sidebarVisible.value = false
}

const toggleDark = (value) => {
  const html = document.documentElement
  if (value) {
    html.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    html.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

const goToPersonalCenter = () => {
  router.push('/personal-center')
}

const handleLogout = () => {
  // 设置退出状态
  isLoggingOut.value = true
  
  // 清除所有数据
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  sessionStorage.removeItem('privacy_token')
  sessionStorage.removeItem('privacy_password')
  sessionStorage.removeItem('privacy_last_access')
  
  // 使用 nextTick 确保状态更新后再跳转
  setTimeout(() => {
    window.location.href = '/login'
  }, 0)
}

onMounted(async () => {
  const theme = localStorage.getItem('theme')
  if (theme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  
  // 如果 store 中没有用户信息，从后端获取
  if (!userStore.userInfo && userStore.token) {
    try {
      const request = (await import('../api/request')).default
      const res = await request.get('/users/profile')
      userStore.setUserInfo(res)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取失败且是401错误，说明token过期，跳转登录
      if (error.response?.status === 401) {
        userStore.logout()
        router.push('/login')
      }
    }
  }
})

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.aside-menu {
  background-color: var(--el-bg-color);
  transition: width 0.3s;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--el-border-color-light);
  z-index: 10;
}
.aside-menu.is-mobile {
  position: absolute;
  top: 60px;
  left: 0;
  height: calc(100vh - 60px);
  box-shadow: var(--el-box-shadow);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font-size: 20px;
  font-weight: bold;
  overflow: hidden;
  border-bottom: 1px solid var(--el-border-color-light);
}

.el-menu-vertical {
  border-right: none;
  flex: 1;
}

.main-header {
  background-color: var(--el-bg-color);
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 9;
}
.burger {
  margin-right: 8px;
}
.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.username.hidden-mobile {
  display: inline;
}

@media (max-width: 768px) {
  .layout-container {
    overflow: hidden;
  }
  .aside-menu {
    width: 220px;
  }
  .el-menu-vertical {
    height: calc(100vh - 120px);
    overflow-y: auto;
  }
  .main-content-area {
    padding: 10px;
  }
  .header-right {
    gap: 8px;
  }
  h3 {
    font-size: 16px;
  }
  .username.hidden-mobile {
    display: none;
  }
}

.header-left h3 {
  margin: 0;
  font-weight: 500;
  font-size: 18px;
}

.header-right {
  display: flex;
  align-items: center;
}

.el-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: var(--el-text-color-primary);
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.main-content-area {
  background-color: var(--el-bg-color-page);
  padding: 20px;
  overflow-y: auto;
}

/* Dark mode overrides for specific custom parts if needed */
/* Transition for router view */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
