<template>
  <div class="home-dashboard">
    <div class="welcome-section">
      <h2 class="welcome-text">欢迎回来, {{ userStore.userInfo?.username || '用户' }}</h2>
      <div class="quick-actions">
        <el-button type="primary" size="large" @click="createNewDoc">
          <el-icon><DocumentAdd /></el-icon> 新建文档
        </el-button>
        <el-button type="success" size="large" @click="createNewTask">
          <el-icon><List /></el-icon> 新建任务
        </el-button>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- Left Column: Announcements (Large) -->
      <div class="main-column">
        <el-card class="dashboard-card announcement-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Bell /></el-icon> 公告</span>
              <el-button text @click="showAllDialog = true">更多</el-button>
            </div>
          </template>
          <div class="announcement-list">
            <div v-for="item in displayedAnnouncements" :key="item.id" class="announcement-item">
              <div class="announcement-title">
                <el-tag size="small" :type="item.type === 'important' ? 'danger' : 'primary'">{{ item.tag }}</el-tag>
                <span class="title-text" @click="openDetail(item.id)">{{ item.title }}</span>
              </div>
              <span class="announcement-date">{{ item.date }}</span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- Right Column: Tasks & Meetings -->
      <div class="side-column">
        <!-- Recent Tasks -->
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><tickets /></el-icon> 待处理任务</span>
              <el-button text @click="$router.push('/tasks')">查看全部</el-button>
            </div>
          </template>
          <div class="task-list">
            <div v-for="task in recentTasks" :key="task.id" class="task-item">
              <div class="task-info">
                <el-checkbox v-model="task.completed" disabled>{{ task.title }}</el-checkbox>
                <el-tag size="small" :type="getPriorityType(task.priority)" effect="plain">
                  {{ task.priority }}
                </el-tag>
              </div>
              <span class="task-deadline">截止: {{ task.deadline }}</span>
            </div>
            <el-empty v-if="recentTasks.length === 0" description="暂无待办任务" :image-size="60" />
          </div>
        </el-card>

        <!-- Recent Meetings -->
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Calendar /></el-icon> 近期会议</span>
              <el-button text @click="$router.push('/schedule')">日历</el-button>
            </div>
          </template>
          <div class="meeting-list">
            <div v-for="meeting in recentMeetings" :key="meeting.id" class="meeting-item">
              <div class="meeting-time-badge">
                <span class="month">{{ meeting.month }}</span>
                <span class="day">{{ meeting.day }}</span>
              </div>
              <div class="meeting-details">
                <div class="meeting-title">{{ meeting.title }}</div>
                <div class="meeting-time">{{ meeting.time }} | {{ meeting.location }}</div>
              </div>
            </div>
            <el-empty v-if="recentMeetings.length === 0" description="暂无近期会议" :image-size="60" />
          </div>
        </el-card>
      </div>
    </div>
    
    <el-dialog v-model="showAllDialog" title="所有公告" width="600px">
      <div class="announcement-list">
        <div v-for="item in announcements" :key="item.id" class="announcement-item">
          <div class="announcement-title">
            <el-tag size="small" :type="item.type === 'important' ? 'danger' : 'primary'">{{ item.tag }}</el-tag>
            <span class="title-text" @click="openDetail(item.id)">{{ item.title }}</span>
          </div>
          <span class="announcement-date">{{ item.date }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore, useTaskStore } from '../store'
import { DocumentAdd, List, Bell, Tickets, Calendar } from '@element-plus/icons-vue'
import { getNotices } from '../api/notice'
import { getEvents } from '../api/schedule'
import dayjs from 'dayjs'

const router = useRouter()
const userStore = useUserStore()
const taskStore = useTaskStore()

// Tasks from Store
const { pendingTasks } = storeToRefs(taskStore)
const recentTasks = computed(() => {
    // Sort by deadline ascending (nearest first)
    const sorted = [...pendingTasks.value].sort((a, b) => {
       if (!a.deadline) return 1
       if (!b.deadline) return -1
       return new Date(a.deadline) - new Date(b.deadline)
    })
    return sorted.slice(0, 3)
})

const announcements = ref([])
const displayedAnnouncements = computed(() => announcements.value.slice(0, 8))
const showAllDialog = ref(false)

const recentMeetings = ref([])

const createNewDoc = () => {
  router.push('/documents/create')
}

const createNewTask = () => {
  // Navigate to tasks page
  router.push('/tasks') 
}

const getPriorityType = (p) => {
  const map = { High: 'danger', Medium: 'warning', Low: 'info' }
  return map[p] || 'info'
}

const openDetail = (id) => {
    const { href } = router.resolve({ name: 'announcement-detail', params: { id } })
    window.open(href, '_blank')
}

onMounted(async () => {
    taskStore.fetchTasks()
    
    // Fetch Notices
    try {
       const res = await getNotices()
       announcements.value = res.map(item => ({
           id: item.id,
           title: item.title,
           date: dayjs(item.created_at).format('YYYY-MM-DD'),
           type: item.level,
           tag: item.level === 'important' ? '重要' : '普通'
       }))
    } catch(e) { console.error(e) }

    // Fetch Meetings & Schedules
    try {
        const start = dayjs().format('YYYY-MM-DD')
        const end = dayjs().add(60, 'day').format('YYYY-MM-DD')
        const res = await getEvents({ start_date: start, end_date: end })
        // res is already sorted by start_time
        
        recentMeetings.value = res.slice(0, 2).map(m => {
            let location = '个人日程'
            if (m.type === 'meeting') {
                location = m.meeting_link || '会议室'
            }
            
            return {
                id: m.id,
                title: m.title,
                month: dayjs(m.start_time).format('MM月'),
                day: dayjs(m.start_time).format('DD'),
                time: `${dayjs(m.start_time).format('HH:mm')}-${dayjs(m.end_time).format('HH:mm')}`,
                location: location
            }
        })
    } catch(e) { console.error(e) }
})
</script>

<style scoped>
.home-dashboard {
  padding: 10px;
}

.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.welcome-text {
  font-size: 24px;
  color: var(--el-text-color-primary);
  margin: 0;
}

.quick-actions {
  display: flex;
  gap: 16px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 20px;
}

.dashboard-card {
  /* Let content dictate height for side column */
}

.announcement-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
}

/* Announcement List */
.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.announcement-item:last-child {
  border-bottom: none;
}

.announcement-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-size: 15px;
  color: var(--el-text-color-regular);
  cursor: pointer;
}

.title-text:hover {
  color: var(--el-color-primary);
}

.announcement-date {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

/* Task List */
.side-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-deadline {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* Meeting List */
.meeting-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meeting-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.meeting-item:hover {
  background-color: var(--el-fill-color-light);
}

.meeting-time-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-radius: 8px;
  font-weight: bold;
}

.meeting-time-badge .month {
  font-size: 12px;
  line-height: 1;
}

.meeting-time-badge .day {
  font-size: 18px;
  line-height: 1.2;
}

.meeting-details {
  flex: 1;
}

.meeting-title {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
}

.meeting-time {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
