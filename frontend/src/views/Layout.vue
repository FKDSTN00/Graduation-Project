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
          <el-menu-item index="/admin/announcement">
            <el-icon><Bell /></el-icon>
            <span>公告管理</span>
          </el-menu-item>
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
            <el-icon><Ticket /></el-icon>
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
          <div class="notification-container" v-click-outside="onClickOutside">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" style="margin-right: 16px; margin-top: 5px;">
                <el-button circle @click="popoverVisible = !popoverVisible">
                  <el-icon><Bell /></el-icon>
                </el-button>
            </el-badge>
            <div class="notification-dropdown" v-show="popoverVisible">
                <div class="notification-panel">
                  <div class="notification-header" style="padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid var(--el-border-color-light); font-weight: bold; display: flex; justify-content: space-between;">
                    <span>通知中心</span>
                    <el-button link type="primary" size="small" @click="loadNotifications">刷新</el-button>
                  </div>
                  <div class="notification-body" style="max-height: 300px; overflow-y: auto;">
                    <el-empty v-if="notifications.length === 0" description="暂无新通知" :image-size="80"></el-empty>
                    <div v-else class="notification-list">
                      <div 
                        v-for="item in notifications" 
                        :key="item.id" 
                        class="notification-item" 
                        :class="{ unread: !item.is_read }"
                        @click="handleViewNotification(item)"
                      >
                        <div class="notif-icon">
                           <el-icon v-if="item.type==='meeting'" color="#67C23A"><el-icon><Calendar /></el-icon></el-icon>
                           <el-icon v-else color="#409EFF"><Bell /></el-icon>
                        </div>
                        <div class="notif-info">
                            <div class="notif-title">{{ item.title }}</div>
                            <div class="notif-content">{{ item.content }}</div>
                            <div class="notif-time">{{ formatTime(item.created_at) }}</div>
                        </div>
                        <div class="notif-status" v-if="!item.is_read">
                            <span class="dot"></span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="notification-footer">
                     <el-button size="small" type="primary" link @click="handleMarkAllRead">全部已读</el-button>
                     <el-button size="small" type="danger" link @click="handleClearAll">清空</el-button>
                  </div>
                </div>
            </div>
          </div>
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
              <el-avatar :size="32" :src="avatarSrc" icon="UserFilled" />
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

  <el-dialog v-model="detailDialogVisible" title="通知详情" width="400px" append-to-body>
    <div v-if="currentNotification">
        <h3 style="margin-top:0;">{{ currentNotification.title }}</h3>
        <p style="white-space: pre-wrap; color: var(--el-text-color-regular); line-height: 1.6;">{{ currentNotification.content }}</p>
        <div style="margin-top: 15px; color: var(--el-text-color-secondary); font-size: 12px; text-align: right;">
        {{ currentNotification.created_at ? dayjs.utc(currentNotification.created_at).local().format('YYYY-MM-DD HH:mm:ss') : '' }}
        </div>
    </div>
    <template #footer>
        <el-button type="primary" @click="detailDialogVisible = false">知道了</el-button>
    </template>
  </el-dialog>
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

import { ElMessage, ClickOutside as vClickOutside } from 'element-plus'
import { getNotifications, markRead, markAllRead, clearAllNotifications } from '../api/user'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

const router = useRouter()
const userStore = useUserStore()
const isDark = ref(false)
const isLoggingOut = ref(false)
const isMobile = ref(false)
const sidebarVisible = ref(false)
const detailDialogVisible = ref(false)
const currentNotification = ref({})
const popoverVisible = ref(false)

const onClickOutside = () => {
    if (detailDialogVisible.value) return
    popoverVisible.value = false
}

// 通知逻辑
const notifications = ref([])
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

const loadNotifications = async () => {
    try {
        const res = await getNotifications()
        if (Array.isArray(res)) {
            notifications.value = res
        }
    } catch(e) {
        console.error('获取通知失败', e)
    }
}

const handleRead = async (item) => {
    if (!item.is_read) {
        try {
            await markRead(item.id)
            item.is_read = true
        } catch(e) {}
    }
}

const handleViewNotification = (item) => {
    currentNotification.value = item
    detailDialogVisible.value = true
    // 标记已读
    handleRead(item)
}

const handleMarkAllRead = async () => {
    try {
        await markAllRead()
        notifications.value.forEach(n => n.is_read = true)
        ElMessage.success('全部已读')
    } catch(e) {
        ElMessage.error('操作失败')
    }
}

const handleClearAll = async () => {
    try {
        await clearAllNotifications()
        notifications.value = []
        ElMessage.success('通知已清空')
    } catch(e) {
        ElMessage.error('操作失败')
    }
}

const formatTime = (iso) => {
    // 后端存储的是UTC时间，需要转换为本地时间
    return dayjs.utc(iso).local().format('MM-DD HH:mm')
}

const avatarSrc = computed(() => {
  if (!userStore.userInfo?.avatar) return ''
  // 增加时间戳参数，强制刷新缓存
  // 使用 session storage 存储一个固定的时间戳，只有在刷新页面或重新登录时才会更新
  let ts = sessionStorage.getItem('avatar_ts')
  if (!ts) {
    ts = new Date().getTime().toString()
    sessionStorage.setItem('avatar_ts', ts)
  }
  
  const url = userStore.userInfo.avatar
  return url.includes('?') ? `${url}&t=${ts}` : `${url}?t=${ts}`
})

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
  isLoggingOut.value = true
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  sessionStorage.removeItem('privacy_token')
  sessionStorage.removeItem('privacy_password')
  sessionStorage.removeItem('privacy_last_access')
  
  if (pollTimer) clearInterval(pollTimer)

  setTimeout(() => {
    window.location.href = '/login'
  }, 0)
}

let pollTimer = null

onMounted(async () => {
  const theme = localStorage.getItem('theme')
  if (theme === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  
  if (!userStore.userInfo && userStore.token) {
    try {
      const request = (await import('../api/request')).default
      const res = await request.get('/users/profile')
      userStore.setUserInfo(res)
    } catch (error) {
      console.error('获取用户信息失败:', error)
      if (error.response?.status === 401) {
        userStore.logout()
        router.push('/login')
      }
    }
  }

  // 启动通知轮询 (缩短为10秒)
  loadNotifications()
  pollTimer = setInterval(loadNotifications, 10000)

  // 页面可见时立即刷新
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

const handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
        loadNotifications()
    }
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  if (pollTimer) clearInterval(pollTimer)
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


.notification-container {
  position: relative;
}

.notification-dropdown {
  position: absolute;
  top: 40px;
  right: -80px;
  width: 320px;
  background-color: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-light);
  box-shadow: var(--el-box-shadow-light);
  border-radius: 4px;
  z-index: 2000;
  padding: 0;
}

.notification-popover {
  padding: 0 !important;
}

.notification-panel {
  display: flex;
  flex-direction: column;
}

.notification-header {
  padding: 10px;
  border-bottom: 1px solid var(--el-border-color-ligher);
}

.notification-body {
  max-height: 300px; 
  overflow-y: auto;
}

.notification-footer {
  padding: 8px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.notification-item {
  padding: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  display: flex;
  gap: 10px;
  position: relative;
}

.notification-item:hover {
  background-color: var(--el-fill-color-light);
}

.notification-item.unread {
  background-color: var(--el-color-primary-light-9);
}

.notif-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.notif-info {
  flex: 1;
  overflow: hidden;
}

.notif-title {
  font-weight: bold;
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.notif-content {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.notif-time {
  font-size: 10px;
  color: var(--el-text-color-placeholder);
}

.notif-status {
  display: flex;
  align-items: center;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: var(--el-color-danger);
  border-radius: 50%;
}
</style>

